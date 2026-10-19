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


def test_continuous_core_periphery_recovers_clique():
    coreness, fit = st.continuous_core_periphery(_core_periphery_graph())
    # All 6 core clique nodes should attain maximum coreness of 1.0
    for c in range(6):
        assert coreness[c] == pytest.approx(1.0, abs=1e-2)
    # Periphery nodes should have distinctly lower coreness
    for c in range(6):
        for j in range(3):
            assert coreness[f"p{c}{j}"] < 0.35
    assert fit > 0.65


def test_continuous_core_periphery_edge_cases():
    # Empty graph
    empty_c, empty_fit = st.continuous_core_periphery(nx.Graph())
    assert empty_c == {}
    assert empty_fit == 0.0

    # Single node graph
    g1 = nx.Graph()
    g1.add_node("lone")
    c1, fit1 = st.continuous_core_periphery(g1)
    assert c1 == {"lone": 0.0}
    assert fit1 == 0.0

    # Edgeless graph with multiple nodes
    g_no_edges = nx.Graph()
    g_no_edges.add_nodes_from(["a", "b", "c"])
    c_ne, fit_ne = st.continuous_core_periphery(g_no_edges)
    assert all(val == 0.0 for val in c_ne.values())
    assert fit_ne == 0.0

    # Path graph: central nodes have higher coreness than leaves
    p5 = nx.path_graph(5)
    c_p5, fit_p5 = st.continuous_core_periphery(p5)
    assert c_p5[2] >= c_p5[1] >= c_p5[0]
    assert 0.0 <= fit_p5 <= 1.0


def test_continuous_core_periphery_star_graph():
    # Borgatti & Everett (1999): star S_n has hub c=1.0, leaves c=1/sqrt(n-1), fit=1.0
    s5 = nx.star_graph(4)  # center=0, 4 leaves
    c_s5, fit_s5 = st.continuous_core_periphery(s5)
    assert c_s5[0] == pytest.approx(1.0, abs=1e-4)
    expected_leaf = 1.0 / np.sqrt(4)
    for leaf in range(1, 5):
        assert c_s5[leaf] == pytest.approx(expected_leaf, abs=1e-3)
    assert fit_s5 == pytest.approx(1.0, abs=1e-4)


def test_continuous_core_periphery_directed_raises():
    di = nx.DiGraph([(0, 1), (1, 2)])
    with pytest.raises(ValueError, match="requires an undirected graph"):
        st.continuous_core_periphery(di)


def test_continuous_core_periphery_weighted():
    g = nx.Graph()
    g.add_edge("a", "b", weight=10.0)
    g.add_edge("b", "c", weight=1.0)
    c_w, fit_w = st.continuous_core_periphery(g, weight="weight")
    assert c_w["b"] > 0
    assert 0.0 <= fit_w <= 1.0
