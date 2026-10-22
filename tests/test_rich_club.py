"""Tests for the rich-club coefficient and elite closure against null models."""

import networkx as nx
import numpy as np

from tennis_networks.rich_club import (
    compute_rich_club,
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
