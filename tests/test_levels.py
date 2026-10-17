import numpy as np
import pandas as pd

from tennis_networks import levels


def _matches():
    rows = [("A", "B", "Clay"), ("A", "B", "Clay"), ("B", "A", "Hard"), ("C", "A", "Hard")]
    return pd.DataFrame(rows, columns=["winner", "loser", "surface"])


def test_balance_matrix_is_antisymmetric():
    m = levels._matrix(_matches(), ["A", "B", "C"], "balance")
    assert np.allclose(m, -m.T)
    assert m[0, 1] == 1  # A: 2 wins and 1 loss against B


def test_meetings_matrix_counts_matches():
    m = levels._matrix(_matches(), ["A", "B", "C"], "meetings")
    assert m[0, 1] == 3
    assert m[0, 2] == 1
    assert np.allclose(m, m.T)


def test_surface_profile_labels_specialists():
    m = _matches()
    gap, profile = levels.surface_profile(m, ["A", "B", "C"])
    assert gap["A"] == 1.0  # all wins on clay, none on hard
    assert profile["A"] == "clay"
    assert profile["C"] == "hard"
