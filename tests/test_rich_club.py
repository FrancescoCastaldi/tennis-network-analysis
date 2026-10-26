"""Tests for the rich-club coefficient and elite closure against null models."""

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks.rich_club import (
    compute_rich_club,
    max_z_test,
    normalized_rich_club,
    rich_club_summary,
)


def test_clique_has_rich_club_one():
    """In a complete clique K_n, every subgraph is complete so phi(k) = 1.0."""
    g = nx.complete_graph(10)
    curve = compute_rich_club(g)
    # Degrees are 9; for k < 9 all nodes are present and edge density is 1.0
    for _, phi in curve.values():
        assert np.isclose(phi, 1.0)


def test_star_graph_has_no_rich_club():
    """In a star graph, only the center has degree > 1, so no pairs of nodes with d > 1 exist."""
    g = nx.star_graph(10)
    curve = compute_rich_club(g)
    # For k >= 1 only the center remains, so N_{>k} <= 1 and no rich club exists
    assert all(n <= 1 for k, (n, _) in curve.items() if k >= 1)


def test_normalized_rich_club_karate():
    """Karate club normalized rich club against degree-preserving null models."""
    g = nx.karate_club_graph()
    df = normalized_rich_club(g, null_samples=20, seed=20261115)
    assert not df.empty
    assert "k" in df.columns
    assert "n_nodes" in df.columns
    assert "phi_obs" in df.columns
    assert "phi_null_mean" in df.columns
    assert "rho_rich" in df.columns
    assert "z_score" in df.columns
    assert "p_value" in df.columns
    # Check probabilities are bounded in [0, 1]
    assert (df["p_value"] >= 0).all() and (df["p_value"] <= 1.0).all()


def test_rich_club_determinism():
    """Two runs with the same seed yield identical normalized rich-club coefficients."""
    g = nx.karate_club_graph()
    df1 = normalized_rich_club(g, null_samples=10, seed=20261115)
    df2 = normalized_rich_club(g, null_samples=10, seed=20261115)
    np.testing.assert_allclose(df1["rho_rich"], df2["rho_rich"])
    np.testing.assert_allclose(df1["z_score"], df2["z_score"])


def test_rich_club_summary_schema():
    """rich_club_summary produces a valid dataframe structure."""
    g = nx.karate_club_graph()
    networks = {"karate": g}
    summary = rich_club_summary(networks, null_samples=10, seed=20261115)
    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["network"] == "karate"
    assert "peak_k" in summary.columns
    assert "elite_nodes" in summary.columns
    assert "rho_rich_peak" in summary.columns
    assert "z_peak" in summary.columns
    for col in ("thresholds_tested", "z_max_null_95", "p_max", "p_pointwise", "null_samples"):
        assert col in summary.columns


def test_max_z_test_counts_null_maxima():
    """The p-value compares the observed maximum with the maximum of each null row."""
    z_obs = np.array([0.0, 5.0, 1.0])
    z_null = np.array([[1.0, 0.5, 2.0], [6.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.9]])
    candidates = np.array([True, True, True])
    peak, observed, _, p_max = max_z_test(z_obs, z_null, candidates)
    assert peak == 1 and observed == 5.0
    # Only the second null row reaches 5 (at another threshold): p = (1 + 1) / (4 + 1).
    assert np.isclose(p_max, 2 / 5)


def test_max_z_test_ignores_non_candidates():
    z_obs = np.array([9.0, 1.0])
    z_null = np.zeros((3, 2))
    peak, observed, _, _ = max_z_test(z_obs, z_null, np.array([False, True]))
    assert peak == 1 and observed == 1.0


def test_random_graph_has_no_significant_rich_club():
    """On an Erdos-Renyi graph the peak z is within the null maxima."""
    g = nx.gnm_random_graph(300, 1500, seed=3)
    row = rich_club_summary({"er": g}, null_samples=99, seed=20261115).iloc[0]
    assert row["z_peak"] < row["z_max_null_95"]
    assert row["p_max"] > 0.05


def test_planted_rich_club_is_detected():
    """Linking the 25 highest-degree nodes of a random graph creates a rich club the test must find."""
    g = nx.gnm_random_graph(300, 1500, seed=3)
    top = [n for n, _ in sorted(g.degree, key=lambda x: -x[1])[:25]]
    g.add_edges_from((a, b) for i, a in enumerate(top) for b in top[i + 1 :])
    row = rich_club_summary({"planted": g}, null_samples=99, seed=20261115).iloc[0]
    assert row["z_peak"] > row["z_max_null_95"]
    assert np.isclose(row["p_max"], 1 / 100)


def test_rich_club_summary_same_result_in_parallel():
    g = nx.karate_club_graph()
    serial = rich_club_summary({"karate": g}, null_samples=8, seed=1, n_jobs=1)
    parallel = rich_club_summary({"karate": g}, null_samples=8, seed=1, n_jobs=2)
    pd.testing.assert_frame_equal(serial, parallel)
