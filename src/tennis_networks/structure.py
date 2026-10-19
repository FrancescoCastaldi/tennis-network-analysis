"""Structural measures of the comparative networks (course slides L05 and L06).

Run:
    python -m tennis_networks.structure
    python -m tennis_networks.structure --sw-samples 5      # quicker small-world estimate

For each tennis-data.co.uk network:
* HITS on the wins network: an edge goes from loser to winner, so a good *authority* beats players
  who reach the late rounds, and a good *hub* loses mostly to strong players (a solid player who
  goes deep and meets the champions);
* structural equivalence: cosine similarity of the opponent vectors of the regular players, and a QAP
  test of whether equivalent players have similar rankings (scalar attribute turned dyadic, slide L04);
* core-periphery: Borgatti-Everett discrete model, with the core grown in decreasing order of degree
  (slide L06 notes that this simple division is close to the optimised one), compared with the k-core;
* small-world index sigma = (C / C_null) / (L / L_null) against the configuration model.

Outputs in results/tables: structure_summary.csv, hits_top10.csv, structural_equivalence_pairs.csv
"""

import argparse

import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from tennis_networks import nullmodels as nm
from tennis_networks.config import PROCESSED, TABLES, load_config
from tennis_networks.hypotheses import NETWORKS as TESTED
from tennis_networks.loaders import load_network
from tennis_networks.qap import qap_correlation

NETWORKS = TESTED[:7] + ["td_atp_2007_2025", "td_wta_2007_2025"]
MIN_OPPONENTS = 30  # regular tour players, for structural equivalence


def hits_scores(g):
    """Hub and authority scores of a weighted directed graph."""
    hubs, authorities = nx.hits(g, max_iter=1000, tol=1e-10, normalized=True)
    return pd.Series(hubs, name="hub"), pd.Series(authorities, name="authority")


def core_periphery(und):
    """Borgatti-Everett discrete core-periphery with the core grown by decreasing degree.

    For each core size k the fit is the correlation (phi coefficient) between the adjacency and the
    ideal pattern (core-core pairs linked, periphery-periphery pairs not linked), with the
    core-periphery pairs left out as in the model's "missing off-diagonal" variant. Returns the best
    core as a set and a dictionary with the fit and the densities of the three blocks.
    """
    order = sorted(und.nodes(), key=lambda v: (-und.degree(v), str(v)))
    n, m = len(order), und.number_of_edges()
    position = {v: i for i, v in enumerate(order)}
    best = (-np.inf, 0, 0, 0)
    e_cc, deg_core = 0, 0
    for k, v in enumerate(order, start=1):
        e_cc += sum(1 for u in und.neighbors(v) if position[u] < k - 1)
        deg_core += und.degree(v)
        e_cp = deg_core - 2 * e_cc
        e_pp = m - e_cc - e_cp
        n_cc, n_pp = k * (k - 1) // 2, (n - k) * (n - k - 1) // 2
        n11, n10, n01, n00 = e_cc, n_cc - e_cc, e_pp, n_pp - e_pp
        den = np.sqrt(float(n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
        phi = (n11 * n00 - n10 * n01) / den if den > 0 else -np.inf
        if phi > best[0]:
            best = (phi, k, e_cc, e_cp)
    phi, k, e_cc, e_cp = best
    e_pp = m - e_cc - e_cp
    n_cc, n_cp, n_pp = k * (k - 1) / 2, k * (n - k), (n - k) * (n - k - 1) / 2
    stats = {
        "core_size": k,
        "core_share": k / n,
        "core_fit": float(phi),
        "density_core": e_cc / n_cc if n_cc else np.nan,
        "density_core_periphery": e_cp / n_cp if n_cp else np.nan,
        "density_periphery": e_pp / n_pp if n_pp else np.nan,
    }
    return set(order[:k]), stats


def continuous_core_periphery(und, weight=None, max_iter=500):
    """Borgatti-Everett continuous core-periphery model (1999).

    Computes continuous coreness c_i in [0, 1] maximizing Pearson correlation
    rho(A, c c^T) over off-diagonal entries (i < j).
    Returns (coreness_dict, correlation).
    """
    if und.is_directed():
        raise ValueError("continuous_core_periphery requires an undirected graph")

    nodes = list(und.nodes())
    n = len(nodes)
    if n < 2:
        return ({v: 0.0 for v in nodes}, 0.0)

    a = nx.to_numpy_array(und, nodelist=nodes, weight=weight)

    iu = np.triu_indices(n, 1)
    x = a[iu]
    sx = np.std(x)
    if sx < 1e-12:
        return ({v: 1.0 if a.sum() > 0 else 0.0 for v in nodes}, 0.0)

    x_tilde = x - np.mean(x)
    sx_norm = np.sqrt(np.sum(x_tilde**2))

    x_mat = np.zeros((n, n), dtype=float)
    x_mat[iu] = x_tilde
    x_mat = x_mat + x_mat.T

    m = n * (n - 1) // 2

    def objective(c):
        s1 = np.sum(c)
        s2 = np.sum(c**2)
        s4 = np.sum(c**4)
        y_sum = (s1**2 - s2) / 2.0
        y_bar = y_sum / m
        var_y = (s2**2 - s4) / 2.0 - (y_sum**2) / m
        if var_y <= 1e-13:
            return 0.0, np.zeros_like(c)
        d_val = np.sqrt(var_y)
        num_val = 0.5 * (c @ (x_mat @ c))
        rho = num_val / (sx_norm * d_val)

        grad_v = 2.0 * s2 * c - 2.0 * (c**3) - 2.0 * y_bar * (s1 - c)
        grad_d = grad_v / (2.0 * d_val)
        grad_rho = (x_mat @ c * d_val - num_val * grad_d) / (sx_norm * var_y)
        return -rho, -grad_rho

    # Initialize with leading eigenvector of adjacency matrix
    evals, evecs = np.linalg.eigh(a)
    c0 = np.abs(evecs[:, -1])
    if np.std(c0) < 1e-6:
        c0 = c0 + np.linspace(0.01, 0.05, n)
    max_c0 = np.max(c0)
    c0 = c0 / max_c0 if max_c0 > 0 else np.ones(n) / np.sqrt(n)

    res = minimize(
        objective,
        c0,
        jac=True,
        bounds=[(0.0, None)] * n,
        method="L-BFGS-B",
        options={"maxiter": max_iter, "ftol": 1e-9},
    )

    c_opt = np.maximum(res.x, 0.0)
    max_c = np.max(c_opt)
    c_opt = c_opt / max_c if max_c > 1e-9 else np.zeros(n)

    fit = max(0.0, float(-res.fun)) if res.fun <= 0 else 0.0
    return dict(zip(nodes, c_opt, strict=True)), fit


def structural_equivalence(und, players):
    """Cosine similarity between the opponent vectors (number of meetings) of the given players."""
    nodes = list(und.nodes())
    a = nx.to_scipy_sparse_array(und, nodelist=nodes, weight="meetings", format="csr")
    rows = a[[nodes.index(p) for p in players]].toarray()
    norms = np.linalg.norm(rows, axis=1)
    sim = rows @ rows.T / np.outer(norms, norms)
    np.fill_diagonal(sim, 0)
    return sim


def meetings_graph(g):
    """Undirected projection weighted by the number of matches between two players."""
    und = nx.Graph()
    for u, v, w in g.edges(data="weight"):
        prev = und.get_edge_data(u, v, {"meetings": 0})["meetings"]
        und.add_edge(u, v, meetings=prev + w)
    return und


def analyse(spec, seed, sw_samples, n_perm):
    g = load_network(spec)
    und = meetings_graph(g)
    ranks = pd.read_csv(PROCESSED / spec["ranks"], index_col="player")["rank"]
    pr = pd.Series(nx.pagerank(g, weight="weight"), name="pagerank")
    hubs, auth = hits_scores(g)
    scores = pd.concat([hubs, auth, pr, ranks.rename("rank")], axis=1, join="inner").dropna()
    row = {
        "network": spec["id"],
        "authority_pagerank_spearman": scores["authority"].corr(scores["pagerank"], method="spearman"),
        "authority_rank_spearman": scores["authority"].corr(scores["rank"], method="spearman"),
        "hub_rank_spearman": scores["hub"].corr(scores["rank"], method="spearman"),
    }
    top = []
    for kind, s in (("authority", auth), ("hub", hubs)):
        for pos, (player, value) in enumerate(s.sort_values(ascending=False).head(10).items(), start=1):
            top.append(
                {
                    "network": spec["id"],
                    "score": kind,
                    "position": pos,
                    "player": player,
                    "value": value,
                    "median_rank": ranks.get(player),
                }
            )

    core, cp = core_periphery(und)
    _cont_core, cont_fit = continuous_core_periphery(und)
    kcore = nx.core_number(und)
    kmax = max(kcore.values())
    inner = {v for v, k in kcore.items() if k == kmax}
    core_ranks = ranks.reindex(sorted(core)).dropna()
    row.update(cp)
    row.update(
        {
            "continuous_core_fit": cont_fit,
            "max_kcore": kmax,
            "max_kcore_size": len(inner),
            "core_kcore_jaccard": len(core & inner) / len(core | inner),
            "core_median_rank": float(core_ranks.median()),
            "core_share_top100": float((core_ranks <= 100).mean()),
        }
    )

    regulars = [v for v in und.nodes() if und.degree(v) >= MIN_OPPONENTS and v in ranks.index]
    sim = structural_equivalence(und, regulars)
    log_rank = np.log(ranks.reindex(regulars).to_numpy())
    rank_gap = np.abs(log_rank[:, None] - log_rank[None, :])
    qap = qap_correlation(sim, rank_gap, n_perm=n_perm, seed=seed)
    row.update(
        {
            "equivalence_players": len(regulars),
            "equivalence_mean_similarity": float(sim[np.triu_indices(len(regulars), 1)].mean()),
            "equivalence_rankgap_r": qap["r"],
            "equivalence_rankgap_p": qap["p_value"],
        }
    )
    iu = np.triu_indices(len(regulars), 1)
    best = np.argsort(sim[iu])[::-1][:10]
    pairs = [
        {
            "network": spec["id"],
            "player_a": regulars[iu[0][b]],
            "player_b": regulars[iu[1][b]],
            "cosine": float(sim[iu][b]),
            "rank_a": ranks[regulars[iu[0][b]]],
            "rank_b": ranks[regulars[iu[1][b]]],
        }
        for b in best
    ]

    if sw_samples:
        sw = nm.small_world_sigma(nx.Graph(und), sw_samples, seed)
        row.update({"sw_samples": sw_samples, "sw_C": sw["C"], "sw_L": sw["L"], "sw_C_null": sw["C_null"]})
        row.update({"sw_L_null": sw["L_null"], "sw_sigma": sw["sigma"]})
    print(f"[{spec['id']}] core {cp['core_size']} players, sigma {row.get('sw_sigma', float('nan')):.2f}")
    return row, top, pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sw-samples", type=int, default=None, help="null graphs for sigma (default from config)")
    parser.add_argument("--perm", type=int, default=999, help="QAP permutations")
    args = parser.parse_args()
    cfg = load_config()
    specs = {s["id"]: s for s in cfg["networks"]}
    rows, tops, pairs = [], [], []
    for name in NETWORKS:
        spec = specs[name]
        samples = args.sw_samples if args.sw_samples is not None else spec.get("small_world_samples", 20)
        row, top, pair = analyse(spec, cfg["seed"], samples, args.perm)
        rows.append(row)
        tops += top
        pairs += pair
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(TABLES / "structure_summary.csv", index=False, encoding="utf-8")
    pd.DataFrame(tops).to_csv(TABLES / "hits_top10.csv", index=False, encoding="utf-8")
    pd.DataFrame(pairs).to_csv(TABLES / "structural_equivalence_pairs.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
