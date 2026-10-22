"""Agreement of tennis-data.co.uk with network 1 of Michieli (2018) over their common window.

Run (after `python -m tennis_networks.michieli` and `python -m tennis_networks.tennisdata`):
    python -m tennis_networks.source_check

The two sources overlap on ATP main-draw matches from January 2000 to August 2017. Network 1 starts in
1968, so the wins of a player are compared only for players who debut in tennis-data after DEBUT_AFTER:
their whole career lies inside the window.

Outputs:
    results/tables/td_michieli_pairs.csv     agreement on the loser-winner pairs of tennis-data
    results/tables/td_michieli_players.csv   wins of each such player in the two sources
"""

import pandas as pd

from tennis_networks.config import PROCESSED, TABLES

WINDOW_END = "2017-08-31"
DEBUT_AFTER = "2003-01-01"


def common_window(matches):
    """ATP matches of tennis-data inside the period covered by network 1."""
    return matches[(matches["tour"] == "ATP") & (matches["date"] <= WINDOW_END)]


def pair_agreement(atp, michieli):
    """Loser-winner pairs of tennis-data by how their number of wins compares with network 1."""
    ours = atp.assign(source=atp["loser"].str.lower(), target=atp["winner"].str.lower())
    ours = ours.groupby(["source", "target"]).size().rename("tennis_data").reset_index()
    ref = michieli.assign(source=michieli["source"].str.lower(), target=michieli["target"].str.lower())
    ref = ref.groupby(["source", "target"], as_index=False)["weight"].sum()  # names that differ only in case
    pairs = ours.merge(ref, on=["source", "target"], how="left")
    pairs["michieli"] = pairs["weight"].fillna(0)
    outcome = pd.Series("identical", index=pairs.index)
    outcome[pairs["michieli"] > pairs["tennis_data"]] = "Michieli higher"
    outcome[(pairs["michieli"] < pairs["tennis_data"]) & (pairs["michieli"] > 0)] = "tennis-data higher"
    outcome[pairs["michieli"] == 0] = "absent in Michieli"
    counts = outcome.value_counts().reindex(
        ["identical", "Michieli higher", "tennis-data higher", "absent in Michieli"], fill_value=0
    )
    return pd.DataFrame({"outcome": counts.index, "pairs": counts.to_numpy(), "share": counts.to_numpy() / len(pairs)})


def player_wins(atp, michieli):
    """Wins of the players who debut after DEBUT_AFTER, in tennis-data and in network 1."""
    names = pd.concat(
        [
            atp[["winner", "date"]].set_axis(["player", "date"], axis=1),
            atp[["loser", "date"]].set_axis(["player", "date"], axis=1),
        ]
    )
    names["player"] = names["player"].str.lower()
    debut = names.groupby("player")["date"].min()
    wins_td = atp.groupby(atp["winner"].str.lower()).size().rename("wins_tennis_data")
    wins_m = michieli.groupby(michieli["target"].str.lower())["weight"].sum().rename("wins_michieli")
    both = pd.concat([wins_td, wins_m], axis=1).join(debut.rename("debut"), how="inner").dropna()
    both = both[both["debut"] >= DEBUT_AFTER].drop(columns="debut")
    return both.rename_axis("player").reset_index()


def main():
    matches = pd.read_csv(PROCESSED / "td_matches.csv", parse_dates=["date"])
    michieli = pd.read_csv(PROCESSED / "michieli_1_wins.csv")
    atp = common_window(matches)
    TABLES.mkdir(parents=True, exist_ok=True)
    pairs = pair_agreement(atp, michieli)
    players = player_wins(atp, michieli)
    pairs.to_csv(TABLES / "td_michieli_pairs.csv", index=False, encoding="utf-8")
    players.to_csv(TABLES / "td_michieli_players.csv", index=False, encoding="utf-8")
    print(pairs.round(4).to_string(index=False))
    both = players[["wins_tennis_data", "wins_michieli"]]
    print(
        f"{len(players)} players, Pearson r {both.corr().iloc[0, 1]:.3f}, "
        f"Spearman {both.corr('spearman').iloc[0, 1]:.3f}, "
        f"identical {(both.iloc[:, 0] == both.iloc[:, 1]).mean():.3f}, "
        f"wins {both.iloc[:, 0].sum():.0f} against {both.iloc[:, 1].sum():.0f}"
    )


if __name__ == "__main__":
    main()
