import networkx as nx
import numpy as np

from tennis_networks import nullmodels as nm


def test_null_preserves_degree_sequence(karate):
    h = nm.degree_preserving_null(karate, np.random.default_rng(1))
    assert sorted(d for _, d in h.degree()) == sorted(d for _, d in karate.degree())
    assert set(h.edges()) != set(karate.edges())


def test_directed_null_preserves_in_and_out_degree():
    g = nx.gnp_random_graph(40, 0.1, seed=3, directed=True)
    h = nm.degree_preserving_null(g, np.random.default_rng(2))
    assert dict(g.in_degree()) == dict(h.in_degree())
    assert dict(g.out_degree()) == dict(h.out_degree())


def test_null_has_no_self_loops_or_parallel_edges(karate):
    h = nm.degree_preserving_null(karate, np.random.default_rng(5))
    assert nx.number_of_selfloops(h) == 0
    assert h.number_of_edges() == karate.number_of_edges()


def test_null_is_reproducible(karate):
    a = nm.null_distribution(karate, nx.average_clustering, 5, seed=7)
    b = nm.null_distribution(karate, nx.average_clustering, 5, seed=7)
    assert np.allclose(a, b)


def test_null_statistics_share_samples(karate):
    stats = {"c": nx.average_clustering, "t": nx.transitivity}
    a = nm.null_statistics(karate, stats, 4, seed=3)
    b = nm.null_statistics(karate, stats, 4, seed=3)
    assert list(a.columns) == ["c", "t"]
    assert len(a) == 4
    assert np.allclose(a.values, b.values)


def test_compare_to_null_pvalue_bounds():
    res = nm.compare_to_null(10.0, np.random.default_rng(0).normal(0, 1, 99))
    assert 0 < res["p_empirical"] <= 1
    assert res["z"] > 5
