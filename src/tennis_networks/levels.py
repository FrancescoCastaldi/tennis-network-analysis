"""Hypotheses at the monadic, dyadic and mixed levels (course slide L04).

Run:
    python -m tennis_networks.levels

* H6, monadic: in each ATP era, PageRank explains the median ranking beyond the number of wins.
  Regression of log(ranking) on log(PageRank) and log(wins), with permutation of the dependent vector.
* H7, dyadic: head-to-head dominance carries over between surfaces. QAP correlation between the
  head-to-head balance matrices (wins of i over j minus wins of j over i) on clay and on hard courts,
  and on grass and hard courts, for the regular players of 2000-2025.
* H8, mixed: players with the same surface profile (clay specialist, hard-court specialist,
  all-rounder) meet each other more often than expected. The nominal attribute becomes a same-profile
  matrix, the scalar specialisation becomes an absolute-difference matrix; both are correlated with
  the matrix of matches played, with QAP.

Output: results/tables/levels_tests.csv
"""

import argparse

import numpy as np
import pandas as pd

from tennis_networks.config import PROCESSED, TABLES, load_config
from tennis_networks.qap import permutation_regression, qap_correlation
from tennis_networks.tennisdata import ERAS

MIN_MATCHES = {"Clay": 30, "Hard": 30, "Grass": 15}
SPECIALIST_GAP = 0.10  # difference in win rate between clay and hard that makes a specialist


def _row(hypothesis, level, comparison, statistic, value, p_value, n, extra=""):
    return {
        "hypothesis": hypothesis,
        "level": level,
        "comparison": comparison,
        "statistic": statistic,
        "value": value,
        "p_value": p_value,
        "n": n,
        "note": extra,
    }


def monadic(n_perm, seed):
    rows = []
    for era in ERAS:
        name = f"td_atp_{era}"
        nodes = pd.read_csv(TABLES / f"{name}_nodes.csv", index_col="node")
        ranks = pd.read_csv(PROCESSED / f"{name}_ranks.csv", index_col="player")["rank"]
        df = nodes.join(ranks, how="inner")
        df = df[(df["in_strength"] > 0) & df["rank"].notna()]
        x = np.column_stack([np.log(df["pagerank"]), np.log(df["in_strength"])])
        for r in permutation_regression(np.log(df["rank"]), x, ["log PageRank", "log wins"], n_perm, seed):
            rows.append(
                _row(
                    "H6",
                    "monadic",
                    f"{name}: log(ranking) on log(PageRank) and log(wins)",
                    f"beta {r['predictor']}",
                    r["beta"],
                    r["p_value"],
                    len(df),
                    f"R2 = {r['r2']:.3f}",
                )
            )
    return rows


def _players_with(atp, surfaces):
    counts = pd.concat([atp["winner"], atp["loser"]]).to_frame("player")
    counts["surface"] = pd.concat([atp["surface"], atp["surface"]])
    per = counts.groupby(["player", "surface"]).size().unstack(fill_value=0)
    keep = np.ones(len(per), dtype=bool)
    for s in surfaces:
        keep &= per.get(s, 0) >= MIN_MATCHES[s]
    return sorted(per.index[keep])


def _matrix(matches, players, kind):
    """kind = 'balance': wins of i over j minus wins of j over i; 'meetings': matches between i and j."""
    index = {p: i for i, p in enumerate(players)}
    m = np.zeros((len(players), len(players)))
    sub = matches[matches["winner"].isin(index) & matches["loser"].isin(index)]
    for w, loser in zip(sub["winner"], sub["loser"], strict=True):
        i, j = index[w], index[loser]
        if kind == "balance":
            m[i, j] += 1
            m[j, i] -= 1
        else:
            m[i, j] += 1
            m[j, i] += 1
    return m


def dyadic(atp, n_perm, seed):
    rows = []
    for a, b in (("Clay", "Hard"), ("Grass", "Hard")):
        players = _players_with(atp, (a, b))
        ma = _matrix(atp[atp["surface"] == a], players, "balance")
        mb = _matrix(atp[atp["surface"] == b], players, "balance")
        res = qap_correlation(ma, mb, n_perm, seed)
        rows.append(
            _row(
                "H7",
                "dyadic",
                f"head-to-head balance on {a} vs on {b}, ATP 2000-2025",
                "QAP Pearson r",
                res["r"],
                res["p_value"],
                len(players),
                f"mean permuted r = {res['perm_mean']:.3f}",
            )
        )
    return rows


def surface_profile(atp, players):
    """Win rate on clay minus win rate on hard, and the resulting nominal profile."""
    out = {}
    for s in ("Clay", "Hard"):
        m = atp[atp["surface"] == s]
        wins = m["winner"].value_counts()
        losses = m["loser"].value_counts()
        out[s] = (wins.reindex(players, fill_value=0) / (wins.add(losses, fill_value=0)).reindex(players)).fillna(0)
    gap = out["Clay"] - out["Hard"]
    profile = np.where(gap > SPECIALIST_GAP, "clay", np.where(gap < -SPECIALIST_GAP, "hard", "all-round"))
    return gap, pd.Series(profile, index=players)


def mixed(atp, n_perm, seed):
    players = _players_with(atp, ("Clay", "Hard"))
    gap, profile = surface_profile(atp, players)
    meetings = _matrix(atp, players, "meetings")
    labels = profile.to_numpy()
    same = (labels[:, None] == labels[None, :]).astype(float)
    distance = np.abs(gap.to_numpy()[:, None] - gap.to_numpy()[None, :])
    counts = profile.value_counts().to_dict()
    note = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    rows = []
    for stat, x in (("same surface profile", same), ("difference in clay-hard specialisation", distance)):
        res = qap_correlation(x, meetings, n_perm, seed)
        rows.append(
            _row(
                "H8",
                "mixed",
                f"{stat} vs matches played, ATP 2000-2025",
                "QAP Pearson r",
                res["r"],
                res["p_value"],
                len(players),
                note,
            )
        )
    return rows, profile, gap


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--perm", type=int, default=999, help="permutations per test")
    args = parser.parse_args()
    seed = load_config()["seed"]
    matches = pd.read_csv(PROCESSED / "td_matches.csv", parse_dates=["date"])
    atp = matches[(matches["tour"] == "ATP") & matches["surface"].isin(["Clay", "Hard", "Grass"])]

    rows = monadic(args.perm, seed) + dyadic(atp, args.perm, seed)
    mixed_rows, profile, gap = mixed(atp, args.perm, seed)
    rows += mixed_rows
    TABLES.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "levels_tests.csv", index=False, encoding="utf-8")
    pd.DataFrame({"clay_minus_hard_win_rate": gap, "profile": profile}).rename_axis("player").to_csv(
        TABLES / "surface_profiles.csv", encoding="utf-8"
    )
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
