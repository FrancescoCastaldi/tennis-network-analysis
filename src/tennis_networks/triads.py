"""Triad census and hypothesis H5 (course slides L06 and L04).

Run:
    python -m tennis_networks.triads
    python -m tennis_networks.triads --null 20 --jobs 2      # quicker, fewer null graphs

In a triangle of matches between three players, either one player beats both others and the
results are consistent (transitive triad 030T: A beats B, B beats C, A beats C), or the results go
round in a circle (cyclic triad 030C: A beats B, B beats C, C beats A). With random outcomes a
triangle is cyclic with probability 2/8, so the ratio 030C / 030T is 1/3. A lower ratio means a more
consistent hierarchy.

* For every network the ratio is compared with directed configuration-model graphs (every player keeps
  the number of distinct opponents beaten and lost to; repeated wins over the same opponent are not
  kept): is the hierarchy more consistent than these degrees imply?
* H5: the ATP hierarchy was more rigid in the 2007-2012 seasons, at the peak of the Big Three, than
  in the other seasons. One ratio per season, then a permutation test of the season labels.

Outputs in results/tables: triads_networks.csv, triads_by_season.csv, triads_h5.csv
"""

import argparse

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks import nullmodels as nm
from tennis_networks import tennisdata as td
from tennis_networks.config import PROCESSED, TABLES, load_config
from tennis_networks.hypotheses import group_permutation_test
from tennis_networks.inference import add_holm_correction
from tennis_networks.loaders import load_network
from tennis_networks.structure import NETWORKS

RANDOM_RATIO = 1 / 3
PEAK = (2007, 2012)


def cyclic_transitive_counts(g):
    """Number of 030C and 030T triads of a directed graph, without the full triad census.

    Both classes are triangles in which every pair has exactly one directed edge (no reciprocal
    pair). Such a triangle is cyclic when every player beats exactly one of the other two, and
    transitive otherwise. Counting only these triangles gives the same numbers as
    `nx.triads.triadic_census` and is much faster, which matters on hundreds of null graphs.
    """
    asym = nx.Graph()
    asym.add_edges_from((u, v) for u, v in g.edges() if u != v and not g.has_edge(v, u))
    order = {v: i for i, v in enumerate(asym.nodes())}
    cyclic = transitive = 0
    for u in asym:
        later = {w for w in asym[u] if order[w] > order[u]}
        for v in later:
            for w in later & set(asym[v]):
                if order[w] <= order[v]:
                    continue
                # Out-degrees inside the triangle: cyclic iff all three are 1.
                out_u = g.has_edge(u, v) + g.has_edge(u, w)
                out_v = g.has_edge(v, u) + g.has_edge(v, w)
                if out_u == 1 and out_v == 1:
                    cyclic += 1
                else:
                    transitive += 1
    return cyclic, transitive


def cyclic_ratio(g):
    """030C / 030T of a directed graph (reciprocal pairs, where both players won, are not counted)."""
    cyclic, transitive = cyclic_transitive_counts(g)
    return cyclic / transitive if transitive else float("nan")


def _triad_census_worker(args):
    """Worker function for parallel triad census null sampling."""
    g, seed = args
    rng = np.random.default_rng(seed)
    h = nm.degree_preserving_null(g, rng)
    return nx.triads.triadic_census(h)


def triad_census_spectrum(g, samples=20, seed=None, n_jobs=1):
    """16-class Holland-Leinhardt triad census z-score spectrum against the configuration model.

    Computes observed counts, configuration null means, null stds, z-scores, and empirical
    two-sided p-values for all 16 triad types.
    Returns a DataFrame with columns: triad, observed, null_mean, null_sd, z, p_empirical.
    """
    if not g.is_directed():
        raise ValueError("triad_census_spectrum requires a directed graph (DiGraph)")

    observed = nx.triads.triadic_census(g)
    triad_names = list(observed.keys())

    # One child seed per null graph, as in nullmodels.null_statistics: same result for any n_jobs.
    worker_args = [(g, s) for s in np.random.SeedSequence(seed).spawn(samples)]
    if n_jobs is None or n_jobs == 1:
        null_rows = [_triad_census_worker(a) for a in worker_args]
    else:
        import os
        from concurrent.futures import ProcessPoolExecutor

        max_workers = os.cpu_count() if n_jobs == -1 else max(1, int(n_jobs))
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            null_rows = list(executor.map(_triad_census_worker, worker_args))

    null_df = pd.DataFrame(null_rows)
    records = []
    for t in triad_names:
        res = nm.compare_to_null(observed[t], null_df[t])
        records.append({"triad": t, **res})
    return pd.DataFrame(records)


def season_ratios(matches, tour, years):
    m = matches[matches["tour"] == tour]
    return pd.Series({y: cyclic_ratio(td.to_graph(m[m["year"] == y])) for y in years}, name=f"{tour}_cyclic_ratio")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--null", type=int, default=None, help="null graphs per network (default: test_null_samples)")
    parser.add_argument("--perm", type=int, default=999, help="permutations for H5")
    parser.add_argument("--jobs", type=int, default=1, help="worker processes for the null graphs (-1 = all cores)")
    args = parser.parse_args()
    cfg = load_config()
    seed = cfg["seed"]
    args.null = args.null or cfg["test_null_samples"]
    specs = {s["id"]: s for s in cfg["networks"]}
    TABLES.mkdir(parents=True, exist_ok=True)

    rows = []
    for name in NETWORKS:
        g = load_network(specs[name])
        observed = cyclic_ratio(g)
        null = nm.null_statistics(g, {"ratio": cyclic_ratio}, args.null, seed, n_jobs=args.jobs)["ratio"]
        res = nm.compare_to_null(observed, null)
        rows.append({"network": name, "cyclic_ratio": observed, "random_outcomes": RANDOM_RATIO, **res})
        print(f"[{name}] 030C/030T = {observed:.3f}, configuration model {res['null_mean']:.3f}, z = {res['z']:.1f}")
    pd.DataFrame(rows).assign(samples=args.null).to_csv(TABLES / "triads_networks.csv", index=False, encoding="utf-8")

    spectrum_2007_2012 = triad_census_spectrum(
        load_network(specs["td_atp_2007_2012"]), samples=args.null, seed=seed, n_jobs=args.jobs
    )
    spectrum_2007_2012.to_csv(TABLES / "triads_spectrum_2007_2012.csv", index=False, encoding="utf-8")

    matches = pd.read_csv(PROCESSED / "td_matches.csv", parse_dates=["date"])
    seasons = pd.concat(
        [season_ratios(matches, "ATP", range(2000, 2026)), season_ratios(matches, "WTA", range(2007, 2026))], axis=1
    )
    seasons.index.name = "season"
    seasons.to_csv(TABLES / "triads_by_season.csv", encoding="utf-8")

    atp = seasons["ATP_cyclic_ratio"]
    peak = atp.loc[PEAK[0] : PEAK[1]]
    rest = atp.drop(peak.index)
    res = group_permutation_test(peak, rest, args.perm, seed)
    h5 = {
        "hypothesis": "H5",
        "statistic": "cyclic_ratio",
        "comparison": "ATP seasons 2007-2012 vs 2000-2006 and 2013-2025",
        "value_a": peak.mean(),
        "value_b": rest.mean(),
        **res,
    }
    wta = seasons["WTA_cyclic_ratio"].dropna()
    paired = (wta - atp.loc[wta.index]).to_numpy()
    flips = np.random.default_rng(seed).choice([-1.0, 1.0], size=(10 * args.perm, len(paired)))
    extreme = np.sum(np.abs((flips * paired).mean(axis=1)) >= abs(paired.mean()) - 1e-12)
    tours = {
        "hypothesis": "H5 (tours)",
        "statistic": "cyclic_ratio",
        "comparison": "WTA vs ATP, paired season differences 2007-2025",
        "value_a": wta.mean(),
        "value_b": atp.loc[wta.index].mean(),
        "diff": paired.mean(),
        "p_value": (extreme + 1) / (10 * args.perm + 1),
    }
    out = add_holm_correction(pd.DataFrame([h5, tours]))
    out.to_csv(TABLES / "triads_h5.csv", index=False, encoding="utf-8")
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
