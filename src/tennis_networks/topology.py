"""Degree distribution, compactness and ranking-band homophily (role B2, course slides L03 and L05).

Run:
    python -m tennis_networks.topology
    python -m tennis_networks.topology --perm 199      # quicker homophily test

For every tennis-data.co.uk network (the four Michieli networks are fitted too where meaningful):
* power law: maximum-likelihood fit of the number of distinct opponents with the method of Clauset,
  Shalizi and Newman (2009), then likelihood-ratio comparison with the lognormal, exponential and
  truncated power law alternatives (package powerlaw);
* compactness: average distance and diameter of the largest component of the undirected network,
  global efficiency, and the ratio between the average distance and ln(N) / ln(<k>), the value
  expected in a random network of the same size and mean degree (a descriptive reference, not a test:
  the test against the configuration model is the small-world index in structure.py);
* homophily: how often players of the same ranking band (top 10, 11-100, others) meet, against a
  permutation of the band labels over the players (999 draws, two-sided p with the +1 correction).
  Two nulls are reported: labels shuffled over all players, and labels shuffled only among players
  with a similar number of opponents (degree deciles), which removes the effect of activity (players
  who play more meet everybody more often).

Outputs in results/tables: powerlaw_fits.csv, compactness.csv, homophily_bands.csv, homophily_mixing.csv
"""

import argparse
import contextlib
import io
import logging
import warnings

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks.config import PROCESSED, TABLES, load_config, seed_everything
from tennis_networks.loaders import load_network
from tennis_networks.measures import giant_component, rank_band

BANDS = ["top10", "11-100", "others"]
MIN_TAIL = 50  # a tail shorter than this cannot discriminate between candidate distributions


def undirected_projection(g):
    """Undirected, unweighted projection: two players are linked if they ever met."""
    return nx.Graph(g.to_undirected() if g.is_directed() else g)


# ---------------------------------------------------------------------------------------------
# Degree distribution
# ---------------------------------------------------------------------------------------------


def _compare(fit, other):
    """Normalised log-likelihood ratio R and its p-value (R > 0: the power law fits better)."""
    ratio, p = fit.distribution_compare("power_law", other, normalized_ratio=True)
    return float(ratio), float(p)


def degree_fit(g):
    """Fit the degree distribution (distinct opponents) with a power law and its alternatives."""
    import powerlaw

    degrees = np.array([d for _, d in undirected_projection(g).degree() if d > 0])
    logging.getLogger("powerlaw").setLevel(logging.ERROR)
    with (
        np.errstate(all="ignore"),
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        warnings.simplefilter("ignore")
        fit = powerlaw.Fit(degrees, discrete=True, verbose=False)
        out = {
            "n_players": len(degrees),
            "k_min_observed": int(degrees.min()),
            "k_max_observed": int(degrees.max()),
            "alpha": float(fit.power_law.alpha),
            "xmin": float(fit.power_law.xmin),
            "ks_distance": float(fit.power_law.D),
            "n_tail": int((degrees >= fit.power_law.xmin).sum()),
        }
        for name in ("lognormal", "exponential", "truncated_power_law"):
            try:
                out[f"R_vs_{name}"], out[f"p_vs_{name}"] = _compare(fit, name)
            except Exception:  # a failed comparison is reported as missing, never as 0
                out[f"R_vs_{name}"], out[f"p_vs_{name}"] = np.nan, np.nan
    out["tail_share"] = out["n_tail"] / out["n_players"]
    out["verdict"] = power_law_verdict(out)
    return out


def power_law_verdict(row):
    """Plain-language reading of one fit, following Clauset et al. (2009).

    "plausible" needs a tail of at least MIN_TAIL players and no alternative that is significantly
    better; otherwise the power law is "not supported" (an alternative wins) or "inconclusive".
    """
    alt = [(row[f"R_vs_{a}"], row[f"p_vs_{a}"]) for a in ("lognormal", "exponential", "truncated_power_law")]
    if row["n_tail"] < MIN_TAIL:
        return "inconclusive (short tail)"
    if any(p < 0.1 and r < 0 for r, p in alt if not np.isnan(r)):
        return "not supported (alternative fits better)"
    return "plausible"


# ---------------------------------------------------------------------------------------------
# Compactness
# ---------------------------------------------------------------------------------------------


def compactness(g):
    """Distance-based compactness of the undirected projection (largest connected component)."""
    und = undirected_projection(g)
    giant = giant_component(und)
    n, m = giant.number_of_nodes(), giant.number_of_edges()
    mean_degree = 2 * m / n
    length = nx.average_shortest_path_length(giant)
    reference = np.log(n) / np.log(mean_degree) if mean_degree > 1 else np.nan
    return {
        "nodes_total": und.number_of_nodes(),
        "nodes_giant": n,
        "giant_fraction": n / und.number_of_nodes(),
        "mean_degree_giant": mean_degree,
        "avg_distance": length,
        "diameter": nx.diameter(giant),
        "global_efficiency": nx.global_efficiency(giant),
        "random_reference_distance": reference,
        "distance_ratio": length / reference,
        "distance_over_ln_n": length / np.log(n),
    }


# ---------------------------------------------------------------------------------------------
# Homophily by ranking band
# ---------------------------------------------------------------------------------------------


def _mixing(band_idx, u, v):
    """Symmetric 3 x 3 matrix of edge counts between ranking bands (each edge counted once)."""
    k = len(BANDS)
    counts = np.zeros((k, k))
    np.add.at(counts, (band_idx[u], band_idx[v]), 1)
    return counts + counts.T - np.diag(np.diag(counts))


def _same_band_share(mix):
    return float(np.trace(mix) / mix.sum())


def _permuted_mixing(band_idx, u, v, strata, n_perm, rng):
    """Mixing matrices of n_perm label permutations, shuffling labels only inside each stratum."""
    groups = [np.flatnonzero(strata == s) for s in np.unique(strata)]
    out = np.empty((n_perm, len(BANDS), len(BANDS)))
    for i in range(n_perm):
        shuffled = band_idx.copy()
        for idx in groups:
            shuffled[idx] = band_idx[rng.permutation(idx)]
        out[i] = _mixing(shuffled, u, v)
    return out


def _compare_mixing(observed, null):
    """Expected counts, ratio, z and two-sided p (+1 correction) of each cell, plus the same-band share."""
    n_perm = len(null)
    mean, std = null.mean(axis=0), null.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (observed - mean) / std
        ratio = np.where(mean > 0, observed / mean, np.nan)
    p = ((np.abs(null - mean) >= np.abs(observed - mean)).sum(axis=0) + 1) / (n_perm + 1)
    share = np.array([_same_band_share(x) for x in null])
    obs_share = _same_band_share(observed)
    share_p = (np.sum(np.abs(share - share.mean()) >= abs(obs_share - share.mean())) + 1) / (n_perm + 1)
    return mean, ratio, z, p, float(share.mean()), float((obs_share - share.mean()) / share.std(ddof=1)), float(share_p)


def band_homophily(g, ranks, n_perm, seed):
    """Observed against expected edges within and between ranking bands, with label permutations.

    Players without a ranking are counted in the band "others", as in measures.rank_band. Every
    permutation keeps the network and the number of players per band fixed. Null "all": the labels are
    shuffled over all players. Null "deg": they are shuffled only among players of the same degree
    decile, so that the expectation also accounts for how many opponents each player has.
    """
    und = undirected_projection(g)
    nodes = list(und.nodes())
    index = {v: i for i, v in enumerate(nodes)}
    band_idx = np.array([BANDS.index(rank_band(ranks.get(v))) for v in nodes])
    edges = np.array([(index[a], index[b]) for a, b in und.edges()])
    u, v = edges[:, 0], edges[:, 1]
    degree = np.array([und.degree(x) for x in nodes])
    deciles = pd.qcut(degree, 10, labels=False, duplicates="drop")

    observed = _mixing(band_idx, u, v)
    rng = np.random.default_rng(seed)
    nulls = {
        "all": _permuted_mixing(band_idx, u, v, np.zeros(len(nodes), dtype=int), n_perm, rng),
        "deg": _permuted_mixing(band_idx, u, v, np.asarray(deciles), n_perm, rng),
    }
    cmp = {k: _compare_mixing(observed, x) for k, x in nulls.items()}

    summary = {
        "n_players": len(nodes),
        "n_top10": int((band_idx == 0).sum()),
        "n_11_100": int((band_idx == 1).sum()),
        "n_others": int((band_idx == 2).sum()),
        "ranked_share": float(np.mean([x in ranks.index for x in nodes])),
        "same_band_share": _same_band_share(observed),
        "attribute_assortativity": float(
            nx.attribute_assortativity_coefficient(_labelled(und, nodes, band_idx), "band")
        ),
        "permutations": n_perm,
    }
    for key, (_, _, _, _, share_null, share_z, share_p) in cmp.items():
        summary[f"same_band_share_null_{key}"] = share_null
        summary[f"same_band_z_{key}"] = share_z
        summary[f"same_band_p_{key}"] = share_p

    rows = []
    for i, a in enumerate(BANDS):
        for j, b in enumerate(BANDS):
            if j < i:
                continue
            row = {"band_a": a, "band_b": b, "observed": int(observed[i, j])}
            for key, (mean, ratio, z, p, *_) in cmp.items():
                row.update(
                    {
                        f"expected_{key}": float(mean[i, j]),
                        f"ratio_{key}": float(ratio[i, j]),
                        f"z_{key}": float(z[i, j]),
                        f"p_{key}": float(p[i, j]),
                    }
                )
            rows.append(row)
    return summary, rows


def _labelled(und, nodes, band_idx):
    h = und.copy()
    nx.set_node_attributes(h, {v: BANDS[b] for v, b in zip(nodes, band_idx, strict=True)}, "band")
    return h


# ---------------------------------------------------------------------------------------------


def analyse(spec, seed, n_perm):
    """All measures of this module for one network of the configuration."""
    g = load_network(spec)
    nid = spec["id"]
    fit = {"network": nid, **degree_fit(g)}
    comp = {"network": nid, **compactness(g)}
    summary, mixing = None, []
    if spec.get("ranks"):
        ranks = pd.read_csv(PROCESSED / spec["ranks"], index_col="player")["rank"]
        summary, mixing = band_homophily(g, ranks, n_perm, seed)
        summary = {"network": nid, **summary}
        mixing = [{"network": nid, **row} for row in mixing]
    print(f"[{nid}] alpha={fit['alpha']:.2f}, xmin={fit['xmin']:.0f}, L={comp['avg_distance']:.2f}")
    return fit, comp, summary, mixing


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=None)
    parser.add_argument("--perm", type=int, default=999, help="label permutations of the homophily test")
    args = parser.parse_args()

    cfg = load_config(args.config)
    seed_everything(cfg["seed"])
    # Left out on purpose: the karate club fixture, and the Michieli wins network, whose undirected
    # projection is the same graph as the Michieli matches network (one row is enough).
    specs = [s for s in cfg["networks"] if not s.get("builtin") and s["id"] != "atp_wins_direct"]
    fits, comps, sums, mixes = [], [], [], []
    for spec in specs:
        fit, comp, summary, mixing = analyse(spec, cfg["seed"], args.perm)
        fits.append(fit)
        comps.append(comp)
        if summary:
            sums.append(summary)
            mixes.extend(mixing)
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(fits).to_csv(TABLES / "powerlaw_fits.csv", index=False, encoding="utf-8")
    pd.DataFrame(comps).to_csv(TABLES / "compactness.csv", index=False, encoding="utf-8")
    pd.DataFrame(sums).to_csv(TABLES / "homophily_bands.csv", index=False, encoding="utf-8")
    pd.DataFrame(mixes).to_csv(TABLES / "homophily_mixing.csv", index=False, encoding="utf-8")
    print(f"Results in {TABLES}")


if __name__ == "__main__":
    main()
