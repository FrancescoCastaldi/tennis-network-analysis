import math

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from tennis_networks import topology as tp


def test_compactness_of_the_karate_club(karate):
    out = tp.compactness(karate)
    assert out["nodes_giant"] == 34
    assert out["diameter"] == 5
    assert out["avg_distance"] == pytest.approx(2.4082, abs=1e-3)
    assert out["giant_fraction"] == 1.0
    # L over ln(N) / ln(<k>): the random reference of a 34-node graph with mean degree 4.59
    assert out["distance_ratio"] == pytest.approx(out["avg_distance"] / (math.log(34) / math.log(78 * 2 / 34)))


def test_compactness_uses_the_largest_component():
    g = nx.disjoint_union(nx.complete_graph(6), nx.path_graph(3))
    out = tp.compactness(g)
    assert out["nodes_total"] == 9
    assert out["nodes_giant"] == 6
    assert out["avg_distance"] == pytest.approx(1.0)


def test_degree_fit_prefers_an_alternative_for_a_bounded_distribution():
    # Every player meets roughly the same number of opponents: a power law cannot be plausible.
    g = nx.gnp_random_graph(600, 0.05, seed=7)
    out = tp.degree_fit(g)
    assert out["n_players"] > 500
    assert out["verdict"] != "plausible"
    assert np.isfinite(out["alpha"]) and out["xmin"] >= 1


def test_degree_fit_handles_a_heavy_tail():
    g = nx.barabasi_albert_graph(2000, 2, seed=3)
    out = tp.degree_fit(g)
    assert 2.0 < out["alpha"] < 4.5
    assert out["R_vs_exponential"] > 0  # the power law beats the exponential on a scale-free graph


def _toy_network():
    """Ten 'top' players who only meet each other, and thirty 'others' who only meet each other."""
    g = nx.Graph()
    g.add_edges_from((f"t{i}", f"t{j}") for i in range(10) for j in range(i + 1, 10))
    g.add_edges_from((f"o{i}", f"o{(i + 1) % 30}") for i in range(30))
    ranks = pd.Series({**{f"t{i}": i + 1 for i in range(10)}, **{f"o{i}": 200 + i for i in range(30)}})
    return g, ranks


def test_band_homophily_detects_a_segregated_network():
    g, ranks = _toy_network()
    summary, rows = tp.band_homophily(g, ranks, n_perm=99, seed=1)
    assert summary["same_band_share"] == 1.0
    assert summary["n_top10"] == 10 and summary["n_others"] == 30 and summary["n_11_100"] == 0
    assert summary["same_band_z_all"] > 3
    cell = next(r for r in rows if r["band_a"] == "top10" and r["band_b"] == "top10")
    assert cell["observed"] == 45 and cell["ratio_all"] > 1
    assert all(0 < r["p_all"] <= 1 for r in rows)  # +1 correction: never exactly 0


def test_band_homophily_is_reproducible_and_covers_every_pair():
    g, ranks = _toy_network()
    first = tp.band_homophily(g, ranks, n_perm=49, seed=5)
    second = tp.band_homophily(g, ranks, n_perm=49, seed=5)
    assert first[0] == second[0]
    pd.testing.assert_frame_equal(pd.DataFrame(first[1]), pd.DataFrame(second[1]))
    assert len(first[1]) == 6  # three bands: 3 same-band and 3 mixed pairs
    assert sum(r["observed"] for r in first[1]) == g.number_of_edges()


def test_power_law_verdict_needs_a_long_tail():
    row = {"n_tail": 10, "R_vs_lognormal": 1.0, "p_vs_lognormal": 0.5}
    row |= {
        "R_vs_exponential": 1.0,
        "p_vs_exponential": 0.5,
        "R_vs_truncated_power_law": 1.0,
        "p_vs_truncated_power_law": 0.5,
    }
    assert tp.power_law_verdict(row).startswith("inconclusive")
