"""Unit tests and regression tests for run_analysis.py pipeline entry-point."""

import json
import sys
from pathlib import Path

import networkx as nx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import run_analysis  # noqa: E402


def test_parse_args_defaults():
    args = run_analysis.parse_args([])
    assert not args.quick
    assert args.network is None
    assert args.num_samples is None
    assert not args.skip_null


def test_parse_args_custom():
    args = run_analysis.parse_args(
        ["--quick", "--network", "M1_wins", "--num-samples", "10", "--skip-null", "--output-dir", "custom_out"]
    )
    assert args.quick
    assert args.network == "M1_wins"
    assert args.num_samples == 10
    assert args.skip_null
    assert args.output_dir == "custom_out"


def test_compute_null_model_stats_synthetic():
    G = nx.gnm_random_graph(40, 120, seed=1, directed=True)
    rows = run_analysis.compute_null_model_stats(G, num_samples=9, nswaps_factor=5, seed=1)
    assert [r["metric"] for r in rows] == ["avg_clustering", "transitivity", "degree_assortativity"]
    for r in rows:
        # Two-sided p-value with the +1 correction: never 0, at least 1 / (samples + 1).
        assert 1 / 10 <= r["p_value"] <= 1
        assert r["samples"] == 9


def test_null_model_uses_undirected_projection():
    G = nx.DiGraph([(0, 1), (1, 0), (1, 2), (2, 3), (3, 0)])
    und = run_analysis.undirected_projection(G)
    assert not und.is_directed()
    assert und.number_of_edges() == 4  # the reciprocal pair 0-1 becomes one edge


def test_null_graphs_are_randomised_on_large_networks():
    # The old cap of 15,000 swaps left most edges of large networks in place.
    G = nx.gnm_random_graph(2000, 20000, seed=2)
    rng = run_analysis.np.random.default_rng(3)
    h = run_analysis.nm.degree_preserving_null(G, rng, swaps_per_edge=10)
    kept = sum(1 for u, v in h.edges() if G.has_edge(u, v))
    assert kept / G.number_of_edges() < 0.05
    assert sorted(d for _, d in h.degree()) == sorted(d for _, d in G.degree())


def test_run_analysis_smoke_pipeline(tmp_path):
    out_dir = tmp_path / "test_out"
    exit_code = run_analysis.main(
        ["--quick", "--skip-null", "--network", "ATP_2007-2012", "--output-dir", str(out_dir)]
    )
    assert exit_code == 0
    assert (out_dir / "basic_measures.csv").exists()
    assert (out_dir / "centralities_top10.csv").exists()
    assert (out_dir / "kcore_decomposition.csv").exists()
    assert (out_dir / "small_world.csv").exists()
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "analysis"
    assert manifest["config"]["sha256"]
    assert manifest["inputs"]


def test_betweenness_ignores_win_counts():
    # c beat a 50 times directly. Read as a distance, that strong tie would be "longer" than the
    # detour a -> b -> c, and b would wrongly become a broker.
    G = nx.DiGraph()
    G.add_edge("a", "c", weight=50)
    G.add_edge("a", "b", weight=1)
    G.add_edge("b", "c", weight=1)
    assert nx.betweenness_centrality(G, weight="weight")["b"] > 0  # the old behaviour
    cent, _ = run_analysis.compute_centralities(G)
    assert cent["betweenness"]["b"] == 0


def test_core_periphery_matches_report_model():
    G = nx.karate_club_graph()
    cp = run_analysis.compute_core_periphery(G)
    core, stats = run_analysis.core_periphery(G)
    assert set(cp["core"]) == core
    assert cp["core_fit"] == stats["core_fit"]


def test_sampled_distances_exclude_self_pairs(monkeypatch):
    G = nx.path_graph(30)
    exact = run_analysis.compute_basic_measures(G)
    monkeypatch.setattr(run_analysis, "EXACT_PATHS_MAX_NODES", 10)
    monkeypatch.setattr(run_analysis, "PATH_SAMPLE_SIZE", 30)
    sampled = run_analysis.compute_basic_measures(G)
    assert sampled["paths_sampled"]
    # With every node as a source the estimate equals the exact value only if d(s, s) = 0 is left out.
    assert sampled["avg_path_length"] == exact["avg_path_length"]


def test_small_world_skipped_on_large_networks(monkeypatch):
    monkeypatch.setattr(run_analysis, "SMALL_WORLD_MAX_NODES", 20)
    sw = run_analysis.compute_small_world(nx.karate_club_graph())
    assert sw["samples"] == 0
    assert run_analysis.np.isnan(sw["sigma"])


def test_network_list_leaves_out_points_network():
    # Michieli network 2 has symmetric weights and no winner: the group decided not to use it.
    assert "M2_points" not in run_analysis.NETWORK_FILES
    assert len(run_analysis.NETWORK_FILES) == 12


def test_unknown_network_returns_error_code(tmp_path):
    assert run_analysis.main(["--quick", "--skip-null", "--network", "nope", "--output-dir", str(tmp_path)]) == 1
