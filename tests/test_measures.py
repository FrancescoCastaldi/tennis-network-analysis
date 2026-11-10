import networkx as nx
import pandas as pd
import pytest

from tennis_networks import measures as ms


def test_karate_known_values(karate):
    out = ms.global_measures(karate)
    assert out["nodes"] == 34
    assert out["edges"] == 78
    assert out["transitivity"] == pytest.approx(0.2557, abs=1e-3)
    assert out["avg_clustering"] == pytest.approx(0.5706, abs=1e-3)
    assert out["degree_assortativity"] == pytest.approx(-0.4756, abs=1e-3)
    assert out["diameter_giant"] == 5


def test_star_centralization_is_one():
    assert ms.degree_centralization(nx.star_graph(9)) == pytest.approx(1.0)


def test_reciprocal_directed_star_centralization_is_one():
    g = nx.DiGraph()
    g.add_edges_from((0, node) for node in range(1, 10))
    g.add_edges_from((node, 0) for node in range(1, 10))
    assert ms.degree_centralization(g) == pytest.approx(1.0)


def test_one_way_directed_star_centralization_is_half():
    g = nx.DiGraph((0, node) for node in range(1, 10))
    assert ms.degree_centralization(g) == pytest.approx(0.5)


def test_top_share_of_a_star():
    g = nx.DiGraph([(i, 0) for i in range(1, 20)])
    assert ms.top_pagerank_share(g, 1) > 5 / 20  # well above the uniform share 1/20
    assert ms.top_pagerank_share(g, 20) == pytest.approx(1.0)


def test_gini_bounds():
    assert ms.gini([1, 1, 1, 1]) == pytest.approx(0.0)
    assert ms.gini([0, 0, 0, 10]) == pytest.approx(0.75)


def test_robustness_curve_starts_at_one_and_attack_is_faster():
    g = nx.barabasi_albert_graph(300, 2, seed=1)
    curve = ms.robustness_curve(g, [0, 0.05, 0.2], seed=1)
    assert curve.loc[0, "attack"] == pytest.approx(1.0)
    assert curve.loc[0.2, "attack"] < curve.loc[0.2, "random"]


def test_rank_band_assortativity_is_one_for_segregated_bands():
    g = nx.Graph([("a", "b"), ("c", "d")])
    ranks = pd.Series({"a": 1, "b": 3, "c": 200, "d": 300})
    assert ms.rank_band_assortativity(g, ranks) == pytest.approx(1.0)


def test_rank_correlation_is_minus_one_when_score_follows_ranking():
    scores = {"a": 0.5, "b": 0.3, "c": 0.2}
    ranks = pd.Series({"a": 1, "b": 2, "c": 3})
    rho, n = ms.rank_correlation(scores, ranks)
    assert rho == pytest.approx(-1.0)
    assert n == 3
