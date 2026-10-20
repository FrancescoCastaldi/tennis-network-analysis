import math

import networkx as nx
import pandas as pd
import pytest

from tennis_networks.triads import cyclic_ratio


def test_transitive_triangle_has_no_cycles():
    g = nx.DiGraph([("c", "b"), ("b", "a"), ("c", "a")])  # loser -> winner: a beats both
    assert cyclic_ratio(g) == 0


def test_cycles_and_transitive_triangles_are_counted():
    g = nx.DiGraph([("c", "b"), ("b", "a"), ("c", "a")])
    g.add_edges_from([("x", "y"), ("y", "z"), ("z", "x")])
    g.add_edges_from([("p", "q"), ("q", "r"), ("p", "r")])
    assert cyclic_ratio(g) == pytest.approx(0.5)


def test_ratio_is_undefined_without_transitive_triads():
    assert math.isnan(cyclic_ratio(nx.DiGraph([("x", "y"), ("y", "z"), ("z", "x")])))


def test_triad_census_spectrum_all_16_types():
    from tennis_networks.triads import triad_census_spectrum

    g = nx.DiGraph(
        [
            ("c", "b"),
            ("b", "a"),
            ("c", "a"),
            ("x", "y"),
            ("y", "z"),
            ("z", "x"),
            ("a", "x"),
            ("b", "y"),
        ]
    )
    df = triad_census_spectrum(g, samples=5, seed=123, n_jobs=1)
    expected_cols = ["triad", "observed", "null_mean", "null_sd", "z", "p_empirical"]
    assert list(df.columns) == expected_cols
    assert len(df) == 16
    expected_triads = {
        "003",
        "012",
        "102",
        "021D",
        "021U",
        "021C",
        "111D",
        "111U",
        "030T",
        "030C",
        "201",
        "120D",
        "120U",
        "120C",
        "210",
        "300",
    }
    assert set(df["triad"]) == expected_triads
    assert (df["p_empirical"] > 0).all() and (df["p_empirical"] <= 1.0).all()


def test_triad_census_spectrum_parallel_n_jobs():
    from tennis_networks.triads import triad_census_spectrum

    g = nx.DiGraph([("a", "b"), ("b", "c"), ("a", "c"), ("d", "a"), ("d", "b")])
    df_par = triad_census_spectrum(g, samples=4, seed=42, n_jobs=2)
    df_seq = triad_census_spectrum(g, samples=4, seed=42, n_jobs=1)
    assert len(df_par) == 16
    assert not df_par["observed"].isna().any()
    pd.testing.assert_frame_equal(df_seq, df_par)


def test_triad_census_spectrum_undirected_raises():
    import pytest

    from tennis_networks.triads import triad_census_spectrum

    und = nx.Graph([(0, 1), (1, 2)])
    with pytest.raises(ValueError, match="requires a directed graph"):
        triad_census_spectrum(und)


def test_triad_census_spectrum_small_graph():
    from tennis_networks.triads import triad_census_spectrum

    g2 = nx.DiGraph([(0, 1)])
    df = triad_census_spectrum(g2, samples=3, seed=42)
    assert len(df) == 16
    assert (df["observed"] == 0).all()


def test_cyclic_transitive_counts_match_networkx_census():
    from tennis_networks.triads import cyclic_transitive_counts

    for seed in range(5):
        g = nx.gnm_random_graph(60, 500, seed=seed, directed=True)
        census = nx.triads.triadic_census(g)
        assert cyclic_transitive_counts(g) == (census["030C"], census["030T"])
