import math

import networkx as nx
import numpy as np
import pandas as pd

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


def test_erdos_renyi_null_preserves_nodes_and_edges(karate):
    h = nm.erdos_renyi_null(karate, np.random.default_rng(42))
    assert set(h.nodes()) == set(karate.nodes())
    assert h.number_of_edges() == karate.number_of_edges()
    assert nx.number_of_selfloops(h) == 0
    assert not h.is_directed()


def test_directed_erdos_renyi_null():
    g = nx.DiGraph([(0, 1), (1, 2), (2, 0), (0, 3)])
    h = nm.erdos_renyi_null(g, np.random.default_rng(42))
    assert set(h.nodes()) == set(g.nodes())
    assert h.number_of_edges() == g.number_of_edges()
    assert h.is_directed()
    assert nx.number_of_selfloops(h) == 0


def test_null_statistics_parallel_n_jobs(karate):
    stats = {"c": nx.average_clustering, "t": nx.transitivity}
    df_seq = nm.null_statistics(karate, stats, 4, seed=42, n_jobs=1)
    df_par = nm.null_statistics(karate, stats, 4, seed=42, n_jobs=2)
    assert list(df_par.columns) == ["c", "t"]
    assert len(df_par) == 4
    assert len(df_seq) == 4
    assert not df_par.isna().any().any()
    # Each null graph has its own child seed: the number of workers does not change the result.
    pd.testing.assert_frame_equal(df_seq, df_par)


def test_compare_dual_null_models(karate):
    stats = {"clustering": nx.average_clustering, "transitivity": nx.transitivity}
    res = nm.compare_dual_null_models(karate, stats, samples=5, seed=123, n_jobs=1)
    expected_cols = [
        "statistic",
        "observed",
        "cm_null_mean",
        "cm_null_sd",
        "cm_z",
        "cm_p_empirical",
        "er_null_mean",
        "er_null_sd",
        "er_z",
        "er_p_empirical",
    ]
    assert list(res.columns) == expected_cols
    assert len(res) == 2
    assert set(res["statistic"]) == {"clustering", "transitivity"}
    assert not res.isna().any().any()


def test_compare_dual_null_models_empty(karate):
    res = nm.compare_dual_null_models(karate, {}, samples=5, seed=123)
    assert len(res) == 0
    assert "cm_z" in res.columns
    assert "er_z" in res.columns


def test_compare_to_null_empty():
    res = nm.compare_to_null(5.0, [])
    assert math.isnan(res["null_mean"])
    assert math.isnan(res["null_sd"])
    assert math.isnan(res["z"])
    assert math.isnan(res["p_empirical"])
