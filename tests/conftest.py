import networkx as nx
import pandas as pd
import pytest


@pytest.fixture
def karate():
    return nx.karate_club_graph()


@pytest.fixture
def matches():
    """Six matches covering the cleaning rules: one walkover, one retirement, three surfaces."""
    rows = [
        # winner, loser, year, surface, wrank, lrank, comment
        ("Federer R.", "Nadal R.", 2008, "Grass", 1, 2, "Completed"),
        ("Nadal R.", "Federer R.", 2008, "Clay", 2, 1, "Completed"),
        ("Nadal R.", "Ferrer D.", 2008, "Clay", 2, 5, "Completed"),
        ("Federer R.", "Ferrer D.", 2009, "Hard", 1, 5, "Completed"),
        ("Ferrer D.", "Lopez F.", 2009, "Hard", 5, 30, "Retired"),
        ("Lopez F.", "Ferrer D.", 2009, "Hard", 30, 5, "Walkover"),
    ]
    df = pd.DataFrame(rows, columns=["winner", "loser", "year", "surface", "wrank", "lrank", "comment"])
    df["tour"] = "ATP"
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-06-01")
    return df
