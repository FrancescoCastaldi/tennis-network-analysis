"""Unit tests and regression tests for run_analysis.py pipeline entry-point."""

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
    G = nx.cycle_graph(6, create_using=nx.DiGraph)
    stats = run_analysis.compute_null_model_stats(G, nx.density, num_samples=3, nswaps_factor=2, max_swaps=10)
    assert "m_real" in stats
    assert "mu_null" in stats
    assert "z_score" in stats
    assert "p_value" in stats
    assert stats["m_real"] > 0


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
