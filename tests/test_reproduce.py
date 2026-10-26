import networkx as nx
import pytest

from tennis_networks.reproduce import clustering_variants


def toy_wins():
    # A triangle (a, b, c) plus a pendant node d, edges directed loser -> winner.
    g = nx.DiGraph()
    g.add_weighted_edges_from([("a", "b", 2), ("b", "c", 1), ("c", "a", 1), ("c", "d", 3)])
    return g


def test_clustering_variants_on_a_triangle_with_a_pendant_node():
    wins = toy_wins()
    values = clustering_variants(wins.to_undirected(), wins)
    assert len(values) == 8
    assert values["global transitivity"] == pytest.approx(0.6)
    assert values["mean over all nodes (isolated count as 0)"] == pytest.approx((1 + 1 + 1 / 3 + 0) / 4)
    assert values["mean over nodes with at least one triangle"] == pytest.approx(7 / 9)
    assert values["mean over nodes with degree of at least 2"] == pytest.approx(7 / 9)
    assert all(v >= 0 for v in values.values())
