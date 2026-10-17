import networkx as nx
import numpy as np
import pytest

from tennis_networks import structure as st


def _core_periphery_graph():
    """A clique of 6 core nodes, each linked to 3 private periphery nodes."""
    g = nx.complete_graph(6)
    for c in range(6):
        for j in range(3):
            g.add_edge(c, f"p{c}{j}")
    return g


def test_core_periphery_recovers_the_clique():
    core, stats = st.core_periphery(_core_periphery_graph())
    assert core == set(range(6))
    assert stats["density_core"] == pytest.approx(1.0)
    assert stats["density_periphery"] == pytest.approx(0.0)
    assert stats["core_fit"] == pytest.approx(1.0)


def test_structural_equivalence_of_twins():
    g = nx.Graph()
    for twin in ("a", "b"):
        for opp in ("x", "y", "z"):
            g.add_edge(twin, opp, meetings=1)
    g.add_edge("c", "x", meetings=1)
    sim = st.structural_equivalence(g, ["a", "b", "c"])
    assert sim[0, 1] == pytest.approx(1.0)
    assert sim[0, 2] == pytest.approx(1 / np.sqrt(3))
    assert sim[0, 0] == 0


def test_meetings_graph_adds_both_directions():
    g = nx.DiGraph()
    g.add_edge("a", "b", weight=2)
    g.add_edge("b", "a", weight=1)
    assert st.meetings_graph(g)["a"]["b"]["meetings"] == 3


def test_hits_authority_is_the_winner():
    g = nx.DiGraph()
    for loser in ("l1", "l2", "l3"):
        g.add_edge(loser, "champion", weight=1)
    g.add_edge("l1", "l2", weight=1)
    hubs, auth = st.hits_scores(g)
    assert auth.idxmax() == "champion"
    assert hubs["l1"] == hubs.max()
