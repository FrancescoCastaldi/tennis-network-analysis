"""Tests of hypotheses H1-H4 on the tennis-data.co.uk networks (course slide L04).

Run (after `python -m tennis_networks.tennisdata`):
    python -m tennis_networks.hypotheses

Three kinds of test, all with the seed of config/networks.json:
* permutation of matches between two groups (H3, surfaces): group labels are shuffled keeping the
  group sizes, both networks are rebuilt and the difference is recomputed;
* season series (H1 eras, H4 ATP vs WTA): one statistic per season, then permutation of the season
  labels (H1) or random sign flips of the paired season differences (H4);
* configuration model (H2): observed assortativity against graphs with the same degree sequence.
  Average clustering and transitivity are computed on the same null graphs.

Outputs: results/tables/hypothesis_tests.csv, yearly_statistics.csv and null_undirected.csv
"""

import argparse

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks import measures as ms
from tennis_networks import nullmodels as nm
from tennis_networks import tennisdata as td
from tennis_networks.config import PROCESSED, TABLES, load_config
from tennis_networks.loaders import load_undirected

NETWORKS = [f"td_atp_{e}" for e in td.ERAS] + ["td_atp_clay", "td_atp_grass", "td_atp_hard", "td_wta_2007_2025"]


def _undirected(m):
    return td.to_graph(m).to_undirected()


# Statistics computed on a set of matches.
MATCH_STATS = {
    "players": lambda m: td.to_graph(m).number_of_nodes(),
    "top10_pagerank_share": lambda m: ms.top_pagerank_share(td.to_graph(m), 10),
    "degree_centralization": lambda m: ms.degree_centralization(_undirected(m)),
    "degree_assortativity": lambda m: nx.degree_assortativity_coefficient(_undirected(m)),
    "avg_clustering": lambda m: nx.average_clustering(_undirected(m)),
}

UNDIRECTED_NULL_STATS = {
    "degree_assortativity": nx.degree_assortativity_coefficient,
    "avg_clustering": nx.average_clustering,
    "transitivity": nx.transitivity,
}


def permutation_test(a, b, statistic, n_perm, seed):
    """Difference statistic(a) - statistic(b) against permutations of the matches between the two groups."""
    observed = statistic(a) - statistic(b)
    pooled = pd.concat([a, b], ignore_index=True)
    rng = np.random.default_rng(seed)
    perm = []
    for _ in range(n_perm):
        idx = rng.permutation(len(pooled))
        perm.append(statistic(pooled.iloc[idx[: len(a)]]) - statistic(pooled.iloc[idx[len(a) :]]))
    perm = np.array(perm)
    # With groups of different size the expected difference under H0 is not zero:
    # the test compares distances from the mean of the permutations (two-sided).
    centre = perm.mean()
    extreme = np.sum(np.abs(perm - centre) >= abs(observed - centre) - 1e-12)
    return {"diff": observed, "perm_mean_diff": centre, "p_value": (extreme + 1) / (n_perm + 1)}


def group_permutation_test(x, y, n_perm, seed):
    """Difference between the means of two groups of season values, with permutation of the labels."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    observed = x.mean() - y.mean()
    pooled = np.concatenate([x, y])
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(n_perm):
        p = rng.permutation(pooled)
        extreme += abs(p[: len(x)].mean() - p[len(x) :].mean()) >= abs(observed) - 1e-12
    return {"diff": observed, "p_value": (extreme + 1) / (n_perm + 1)}


def paired_signflip_test(diffs, n_perm, seed):
    """Mean of paired differences against random sign flips."""
    d = np.asarray(diffs, float)
    observed = d.mean()
    rng = np.random.default_rng(seed)
    flips = rng.choice([-1.0, 1.0], size=(n_perm, len(d)))
    extreme = np.sum(np.abs((flips * d).mean(axis=1)) >= abs(observed) - 1e-12)
    return {"mean_diff": observed, "p_value": (extreme + 1) / (n_perm + 1)}


def yearly(matches, tour, years, stat):
    m = matches[matches["tour"] == tour]
    return pd.Series({y: MATCH_STATS[stat](m[m["year"] == y]) for y in years}, name=f"{tour}_{stat}")


def season_series(matches):
    """Season statistics of the ATP (2000-2025) and the WTA (2007-2025): players, PageRank share, centralization."""
    ys = {}
    for stat in ("top10_pagerank_share", "degree_centralization", "players"):
        ys[f"ATP_{stat}"] = yearly(matches, "ATP", range(2000, 2026), stat)
        ys[f"WTA_{stat}"] = yearly(matches, "WTA", range(2007, 2026), stat)
    series = pd.DataFrame(ys)
    series.index.name = "season"
    return series


def h1_rows(series, n_perm, seed):
    """H1: concentration of prestige in the Big Three seasons (2007-2018) against 2019-2025."""
    rows = []
    for stat in ("top10_pagerank_share", "degree_centralization"):
        s = series[f"ATP_{stat}"]
        res = group_permutation_test(s.loc[2007:2018], s.loc[2019:2025], n_perm, seed)
        rows.append(
            {
                "hypothesis": "H1",
                "statistic": stat,
                "comparison": "ATP 2007-2018 vs 2019-2025 (season means)",
                "value_a": s.loc[2007:2018].mean(),
                "value_b": s.loc[2019:2025].mean(),
                **res,
            }
        )
    return rows


def h3_rows(matches, n_perm, seed):
    """H3: grass against clay and hard, permuting matches (same players, same period)."""
    rows = []
    atp = matches[matches["tour"] == "ATP"]
    grass = atp[atp["surface"] == "Grass"]
    for other in ("Clay", "Hard"):
        rest = atp[atp["surface"] == other]
        for stat in ("degree_centralization", "top10_pagerank_share"):
            res = permutation_test(grass, rest, MATCH_STATS[stat], max(n_perm // 5, 99), seed)
            rows.append(
                {
                    "hypothesis": "H3",
                    "statistic": stat,
                    "comparison": f"ATP Grass vs {other}",
                    "value_a": MATCH_STATS[stat](grass),
                    "value_b": MATCH_STATS[stat](rest),
                    **res,
                }
            )
    return rows


def h4_rows(series, n_perm, seed):
    """H4: concentration of PageRank in the WTA against the ATP, season by season (2007-2025)."""
    rows = []
    for stat in ("top10_pagerank_share", "degree_centralization"):
        a, w = series[f"ATP_{stat}"].loc[2007:2025], series[f"WTA_{stat}"].loc[2007:2025]
        res = paired_signflip_test(w - a, 10 * n_perm, seed)
        rows.append(
            {
                "hypothesis": "H4",
                "statistic": stat,
                "comparison": "WTA vs ATP, paired season differences 2007-2025",
                "value_a": w.mean(),
                "value_b": a.mean(),
                "diff": res["mean_diff"],
                "p_value": res["p_value"],
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--perm", type=int, default=999, help="permutations per test")
    parser.add_argument("--null", type=int, default=None, help="null graphs for H2 (default: test_null_samples)")
    args = parser.parse_args()
    cfg = load_config()
    seed = cfg["seed"]
    args.null = args.null or cfg["test_null_samples"]
    matches = pd.read_csv(PROCESSED / "td_matches.csv", parse_dates=["date"])
    TABLES.mkdir(parents=True, exist_ok=True)

    series = season_series(matches)
    series.to_csv(TABLES / "yearly_statistics.csv", encoding="utf-8")
    rows = h1_rows(series, args.perm, seed)

    # H2: disassortativity against the configuration model, plus clustering on the same null graphs.
    null_rows = []
    for name in NETWORKS:
        g = load_undirected(name)
        nulls = nm.null_statistics(g, UNDIRECTED_NULL_STATS, args.null, seed)
        observed = {stat: fn(g) for stat, fn in UNDIRECTED_NULL_STATS.items()}
        for stat in UNDIRECTED_NULL_STATS:
            res = nm.compare_to_null(observed[stat], nulls[stat])
            null_rows.append({"network": name, "statistic": stat, "samples": args.null, **res})
        res = nm.compare_to_null(observed["degree_assortativity"], nulls["degree_assortativity"])
        rows.append(
            {
                "hypothesis": "H2",
                "statistic": "degree_assortativity",
                "comparison": f"{name} vs configuration model",
                "value_a": res["observed"],
                "value_b": res["null_mean"],
                "diff": res["observed"] - res["null_mean"],
                "z": res["z"],
                "p_value": res["p_empirical"],
            }
        )
    pd.DataFrame(null_rows).to_csv(TABLES / "null_undirected.csv", index=False, encoding="utf-8")

    rows += h3_rows(matches, args.perm, seed)
    rows += h4_rows(series, args.perm, seed)

    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "hypothesis_tests.csv", index=False, encoding="utf-8")
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
