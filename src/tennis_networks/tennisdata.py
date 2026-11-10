"""tennis-data.co.uk matches: cleaning and construction of the comparative sub-networks.

Run (after `python -m tennis_networks.download`):
    python -m tennis_networks.tennisdata

Every network has an edge from the loser to the winner, weighted by the number of wins,
as network 1 of Michieli (2018). Matches ended by walkover are left out.

Outputs:
    data/processed/td_matches.csv              played matches (walkovers excluded)
    data/processed/td_<network>.csv            edge list: source (loser), target (winner), weight
    data/processed/td_<network>_ranks.csv      median ATP/WTA ranking of each player in the network
    results/tables/td_networks_summary.csv     matches, players and edges per network
    results/tables/td_validity_michieli.csv    overlap with Michieli network 1 (2000 to August 2017)
"""

import re
import warnings

import networkx as nx
import pandas as pd

from tennis_networks.config import PROCESSED, RAW, TABLES

TENNISDATA = RAW / "tennisdata"

# Greenset is a hard-court brand; carpet (indoor, abandoned in 2009) is kept apart
# and does not enter the surface networks.
SURFACES = {"Hard": "Hard", "Greenset": "Hard", "Clay": "Clay", "Grass": "Grass", "Carpet": "Carpet"}

ERAS = {
    "2000_2006": (2000, 2006),
    "2007_2012": (2007, 2012),
    "2013_2018": (2013, 2018),
    "2019_2025": (2019, 2025),
}

NAME_ALIASES = {
    "Raducànu E.": "Raducanu E.",
}


def clean_name(name):
    """Collapse white space; the 'Surname I.' format is the same in both sources."""
    cleaned = re.sub(r"\s+", " ", str(name)).strip()
    return NAME_ALIASES.get(cleaned, cleaned)


def spreadsheet_files(folder):
    """Season spreadsheets in `folder`, in order. macOS AppleDouble files (`._*`) are skipped:
    they are metadata written by the operating system, not spreadsheets."""
    return [path for path in sorted(folder.glob("*.xls*")) if not path.name.startswith("._")]


def load_matches(tours=("atp", "wta")):
    """All matches with columns tour, year, date, surface, series, round, winner, loser, wrank, lrank, comment.

    `year` is the season (the year of the file): the first matches of a season can fall in late December.
    """
    warnings.filterwarnings("ignore", message="Unknown extension", module="openpyxl")
    frames = []
    for tour in tours:
        for path in spreadsheet_files(TENNISDATA / tour):
            df = pd.read_excel(path)
            frames.append(
                pd.DataFrame(
                    {
                        "tour": tour.upper(),
                        "year": int(path.stem),
                        "date": pd.to_datetime(df["Date"]),
                        "surface": df["Surface"].map(SURFACES),
                        "series": df["Series"] if "Series" in df else df["Tier"],
                        "round": df["Round"],
                        "winner": df["Winner"].map(clean_name),
                        "loser": df["Loser"].map(clean_name),
                        "wrank": pd.to_numeric(df["WRank"], errors="coerce"),
                        "lrank": pd.to_numeric(df["LRank"], errors="coerce"),
                        "comment": df["Comment"].astype(str).str.strip(),
                    }
                )
            )
    return pd.concat(frames, ignore_index=True)


def played(matches, keep_walkovers=False):
    """Matches actually played: walkovers and rows without names are dropped, retirements are kept."""
    ok = matches["winner"].ne("") & matches["loser"].ne("") & matches["winner"].ne(matches["loser"])
    if not keep_walkovers:
        ok &= ~matches["comment"].str.lower().str.startswith("walkover")
    return matches[ok]


def edge_list(matches):
    """Aggregated edge list: source = loser, target = winner, weight = wins."""
    return (
        matches.groupby(["loser", "winner"])
        .size()
        .rename("weight")
        .reset_index()
        .rename(columns={"loser": "source", "winner": "target"})
    )


def to_graph(matches):
    g = nx.DiGraph()
    for s, t, w in edge_list(matches).itertuples(index=False):
        g.add_edge(s, t, weight=int(w))
    return g


def subsets(matches):
    """The networks of the study: ATP eras, ATP surfaces (2000-2025), ATP and WTA 2007-2025."""
    atp = matches[matches["tour"] == "ATP"]
    wta = matches[matches["tour"] == "WTA"]
    out = {}
    for label, (a, b) in ERAS.items():
        out[f"td_atp_{label}"] = atp[atp["year"].between(a, b)]
    for surface in ("Clay", "Grass", "Hard"):
        out[f"td_atp_{surface.lower()}"] = atp[atp["surface"] == surface]
    out["td_atp_2007_2025"] = atp[atp["year"].between(2007, 2025)]
    out["td_wta_2007_2025"] = wta[wta["year"].between(2007, 2025)]
    return out


def player_rank(matches):
    """Median ranking of each player over the matches of the subset (WRank and LRank columns)."""
    ranks = pd.concat(
        [
            matches[["winner", "wrank"]].set_axis(["player", "rank"], axis=1),
            matches[["loser", "lrank"]].set_axis(["player", "rank"], axis=1),
        ]
    )
    return ranks.dropna().groupby("player")["rank"].median()


def validity_against_michieli(matches):
    """Share of ATP (loser, winner) pairs and players of 2000 to August 2017 also present in Michieli network 1."""
    mich = pd.read_csv(PROCESSED / "michieli_1_wins.csv")
    mich_pairs = set(zip(mich["source"].str.lower(), mich["target"].str.lower(), strict=True))
    mich_players = set(mich["source"].str.lower()) | set(mich["target"].str.lower())
    atp = matches[(matches["tour"] == "ATP") & (matches["date"] <= "2017-08-31")]
    pairs = set(zip(atp["loser"].str.lower(), atp["winner"].str.lower(), strict=True))
    players = set(atp["loser"].str.lower()) | set(atp["winner"].str.lower())
    missing = sorted(players - mich_players)
    table = pd.DataFrame(
        [
            {
                "check": "ATP loser-winner pairs, 2000 to Aug 2017",
                "total": len(pairs),
                "found_in_michieli": len(pairs & mich_pairs),
                "share": len(pairs & mich_pairs) / len(pairs),
            },
            {
                "check": "ATP players, 2000 to Aug 2017",
                "total": len(players),
                "found_in_michieli": len(players & mich_players),
                "share": len(players & mich_players) / len(players),
            },
        ]
    )
    return table, missing


def main():
    matches = played(load_matches())
    PROCESSED.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    matches.to_csv(PROCESSED / "td_matches.csv", index=False, encoding="utf-8")

    per_year = matches.groupby(["tour", "year"]).size()
    if per_year.min() <= 1000:
        raise ValueError(f"season with too few matches:\n{per_year[per_year <= 1000]}")

    rows = []
    for name, sub in subsets(matches).items():
        edges = edge_list(sub)
        edges.to_csv(PROCESSED / f"{name}.csv", index=False, encoding="utf-8")
        player_rank(sub).rename("rank").rename_axis("player").to_csv(PROCESSED / f"{name}_ranks.csv", encoding="utf-8")
        players = set(edges["source"]) | set(edges["target"])
        rows.append(
            {
                "network": name,
                "matches": len(sub),
                "players": len(players),
                "edges": len(edges),
                "first": sub["date"].min().date(),
                "last": sub["date"].max().date(),
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(TABLES / "td_networks_summary.csv", index=False, encoding="utf-8")
    print(summary.to_string(index=False))

    validity, missing = validity_against_michieli(matches)
    validity.to_csv(TABLES / "td_validity_michieli.csv", index=False, encoding="utf-8")
    print(validity.to_string(index=False))
    print(f"tennis-data players missing in Michieli: {len(missing)}, e.g. {missing[:10]}")


if __name__ == "__main__":
    main()
