"""
Structural Analysis of Professional Tennis Networks
A Comparative Study Across Eras, Surfaces, and Genders

Network Analysis, A.Y. 2026/2027, UniBo
Authors: Castaldi, Fusco, Bonifazi, Kumar, Muscarello

Quick overview of every network in one run: basic measures, centralities, HITS, k-cores,
core-periphery, small-world and configuration-model tests. Results go to output/ (not tracked).
It reuses the functions of the tennis_networks package, so its numbers agree with the report.

The report tables, figures and the hypothesis tests H1-H8 come from `make all`, not from this script.

Run with:
    python run_analysis.py                      # all networks, 50 null graphs each
    python run_analysis.py --quick --network ATP_grass
"""

import argparse
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from tennis_networks import nullmodels as nm  # noqa: E402
from tennis_networks.config import load_config, write_run_manifest  # noqa: E402
from tennis_networks.structure import core_periphery  # noqa: E402

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SEED = load_config()["seed"]  # every random draw below takes this seed explicitly

DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "output"

# The 12 networks of the study, built by `make networks` (edge lists with source, target[, weight]).
# Michieli network 2 (ATP points) is left out: its weights are symmetric and carry no winner.
NETWORK_FILES = {
    "M1_wins": ("michieli_1_wins.csv", True),
    "M3_undirected": ("michieli_3_undirected.csv", False),
    "M4_extended": ("michieli_4_extended.csv", False),
    "ATP_2000-2006": ("td_atp_2000_2006.csv", True),
    "ATP_2007-2012": ("td_atp_2007_2012.csv", True),
    "ATP_2013-2018": ("td_atp_2013_2018.csv", True),
    "ATP_2019-2025": ("td_atp_2019_2025.csv", True),
    "ATP_clay": ("td_atp_clay.csv", True),
    "ATP_grass": ("td_atp_grass.csv", True),
    "ATP_hard": ("td_atp_hard.csv", True),
    "ATP_2007-2025": ("td_atp_2007_2025.csv", True),
    "WTA_2007-2025": ("td_wta_2007_2025.csv", True),
}


# ==============================================================================
# 1. DATA LOADING
# ==============================================================================
def load_all_networks(processed_dir=None, selected_networks=None):
    """Load all networks, or the selected ones, from the processed edge lists.

    Directed networks have an edge from the loser to the winner, weighted by the number of wins.
    A missing file is reported and skipped; a malformed one raises an error.
    """
    print("\n" + "=" * 70)
    print("LOADING NETWORKS")
    print("=" * 70 + "\n")

    target_dir = Path(processed_dir) if processed_dir else DATA_DIR / "processed"
    files = NETWORK_FILES
    if selected_networks:
        if isinstance(selected_networks, str):
            selected_networks = [selected_networks]
        files = {k: v for k, v in NETWORK_FILES.items() if k in selected_networks}

    networks = {}
    for name, (filename, directed) in files.items():
        filepath = target_dir / filename
        if not filepath.exists():
            print(f"WARNING: {filepath} not found, run `make networks` first")
            continue
        df = pd.read_csv(filepath, dtype={"source": str, "target": str})
        G = nx.from_pandas_edgelist(
            df,
            source="source",
            target="target",
            edge_attr="weight" if "weight" in df.columns else None,
            create_using=nx.DiGraph if directed else nx.Graph,
        )
        networks[name] = G
        print(f"Loaded {name:20s} | {G.number_of_nodes():5d} nodes, {G.number_of_edges():6d} edges")

    print(f"\nNetworks loaded: {len(networks)}/{len(files)}")
    return networks


# ==============================================================================
# 2. NULL MODEL STATISTICAL VALIDATION
# ==============================================================================
# The statistics are computed on the undirected, unweighted projection (two players linked if they
# ever met), the same graph used for Table "null" and hypothesis H2 in the report.
# Density is not tested: degree-preserving swaps keep the number of edges, so it never changes.
NULL_METRICS = {
    "avg_clustering": nx.average_clustering,
    "transitivity": nx.transitivity,
    "degree_assortativity": nx.degree_assortativity_coefficient,
}


def undirected_projection(G):
    """Simple undirected, unweighted graph: two players are linked if they met at least once."""
    und = nx.Graph()
    und.add_nodes_from(G.nodes())
    und.add_edges_from(G.edges())
    und.remove_edges_from(list(nx.selfloop_edges(und)))
    return und


def compute_null_model_stats(G, metrics=None, num_samples=50, nswaps_factor=10, seed=SEED):
    """Observed metrics against the configuration model, one row per metric.

    Null graphs come from `tennis_networks.nullmodels.degree_preserving_null` with
    `nswaps_factor` swap attempts per edge (no upper cap, so large networks are fully
    randomised). Every null graph is generated once and all metrics are computed on it.
    p-values are two-sided with the +1 correction, so they are never 0.
    """
    metrics = metrics or NULL_METRICS
    und = undirected_projection(G)

    def null_model(g, rng):
        return nm.degree_preserving_null(g, rng, swaps_per_edge=nswaps_factor)

    null = nm.null_statistics(und, metrics, num_samples, seed, model=null_model)
    rows = []
    for name, fn in metrics.items():
        res = nm.compare_to_null(fn(und), null[name])
        rows.append(
            {
                "metric": name,
                "m_real": res["observed"],
                "mu_null": res["null_mean"],
                "std_null": res["null_sd"],
                "z_score": res["z"],
                "p_value": res["p_empirical"],
                "samples": num_samples,
            }
        )
    return rows


def analyze_null_models(networks, output_path=None, num_samples=50, nswaps_factor=10, seed=SEED):
    """Run null model validation across all networks and save the results to CSV."""
    dest_path = Path(output_path) if output_path else OUTPUT_DIR / "null_model_results.csv"
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("NULL MODEL VALIDATION (Configuration Model)")
    print("=" * 70 + "\n")

    results = []
    for name, G in networks.items():
        print(f"\n--- Network: {name} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges) ---")
        for row in compute_null_model_stats(G, num_samples=num_samples, nswaps_factor=nswaps_factor, seed=seed):
            row["network"] = name
            row["significant"] = row["p_value"] < 0.05
            results.append(row)
            print(
                f"  {row['metric']:22s} | real={row['m_real']:.4f} | null={row['mu_null']:.4f} | "
                f"z={row['z_score']:7.2f} | p={row['p_value']:.3f}"
            )

    cols = ["network", "metric", "m_real", "mu_null", "std_null", "z_score", "p_value", "samples", "significant"]
    df_results = pd.DataFrame(results, columns=cols)
    if not df_results.empty:
        df_results.to_csv(dest_path, index=False)
        print(f"\nNull model results saved to: {dest_path}")

    return df_results


# ==============================================================================
# 3. BASIC NETWORK MEASURES
# ==============================================================================
EXACT_PATHS_MAX_NODES = 1500  # above this, average distance is estimated from sampled sources
PATH_SAMPLE_SIZE = 300
SMALL_WORLD_MAX_NODES = 2000  # sigma needs exact distances on every null graph


def _warn(name, err):
    print(f"  WARNING: {name} not computed ({type(err).__name__}: {err})")


def compute_basic_measures(G, seed=SEED):
    """Size, components, distances and clustering of one network.

    Distances are measured on the undirected giant component. Above EXACT_PATHS_MAX_NODES nodes they
    are estimated from PATH_SAMPLE_SIZE random sources (the distance of a source to itself is left
    out), and `diameter` is then a lower bound: `paths_sampled` says which case applies.
    Values that cannot be computed are NaN, never 0.
    """
    measures = {"n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges(), "density": nx.density(G)}
    components = list(nx.weakly_connected_components(G)) if G.is_directed() else list(nx.connected_components(G))
    measures["n_components"] = len(components)
    measures.update({"avg_path_length": np.nan, "diameter": np.nan, "paths_sampled": False})

    if components:
        giant = undirected_projection(G.subgraph(max(components, key=len)))
        n_cc = giant.number_of_nodes()
        try:
            if 1 < n_cc <= EXACT_PATHS_MAX_NODES:
                measures["avg_path_length"] = nx.average_shortest_path_length(giant)
                measures["diameter"] = nx.diameter(giant)
            elif n_cc > EXACT_PATHS_MAX_NODES:
                rng = np.random.default_rng(seed)
                sources = rng.choice(list(giant.nodes()), size=min(PATH_SAMPLE_SIZE, n_cc), replace=False)
                lengths = []
                for s in sources:
                    lengths.extend(d for t, d in nx.single_source_shortest_path_length(giant, s).items() if t != s)
                measures["avg_path_length"] = float(np.mean(lengths))
                measures["diameter"] = int(max(lengths))
                measures["paths_sampled"] = True
        except (nx.NetworkXError, ValueError) as err:
            _warn("distances", err)

    measures["avg_clustering"] = nx.average_clustering(undirected_projection(G))
    return measures


# ==============================================================================
# 4. CENTRALITY MEASURES
# ==============================================================================
def compute_centralities(G, top_n=10, k_sample=500, seed=SEED):
    """Centrality scores and the top-n players for each.

    Betweenness and closeness ignore the weights: a weight is a number of wins, and NetworkX would
    read it as a distance (more wins, longer path). Betweenness is sampled with k_sample sources above
    k_sample nodes. Closeness is exact and is skipped above EXACT_PATHS_MAX_NODES * 4 nodes, because
    a top 10 drawn from a random sample of players would be meaningless.
    """
    n_nodes = G.number_of_nodes()
    k = k_sample if n_nodes > k_sample else None
    centralities = {
        "degree": nx.degree_centrality(G),
        "betweenness": nx.betweenness_centrality(G, k=k, seed=seed, weight=None),
        "pagerank": nx.pagerank(G, alpha=0.85, weight="weight"),
    }
    if n_nodes <= EXACT_PATHS_MAX_NODES * 4:
        centralities["closeness"] = nx.closeness_centrality(G)
    else:
        print(f"  closeness skipped ({n_nodes} nodes)")
    try:
        centralities["eigenvector"] = nx.eigenvector_centrality(G, max_iter=1000, weight="weight")
    except nx.PowerIterationFailedConvergence as err:
        # Common on directed match networks (no strongly connected structure): no undirected fallback,
        # which would silently change the meaning of the score.
        _warn("eigenvector centrality", err)
    if G.is_directed():
        centralities["in_degree"] = nx.in_degree_centrality(G)
        centralities["out_degree"] = nx.out_degree_centrality(G)

    top_nodes = {
        name: sorted(values.items(), key=lambda x: x[1], reverse=True)[:top_n] for name, values in centralities.items()
    }
    return centralities, top_nodes


# ==============================================================================
# 5. HITS ALGORITHM
# ==============================================================================
def compute_hits(G, max_iter=1000):
    """Compute HITS hubs and authorities scores."""
    try:
        hubs, authorities = nx.hits(G, max_iter=max_iter)
        return {"hubs": hubs, "authorities": authorities}
    except nx.PowerIterationFailedConvergence as err:
        _warn("HITS", err)
        return {"hubs": {}, "authorities": {}}


# ==============================================================================
# 6. K-CORE DECOMPOSITION
# ==============================================================================
def compute_kcore(G):
    """Compute k-core decomposition and return core numbers."""
    core_numbers = nx.core_number(undirected_projection(G))
    max_k = max(core_numbers.values()) if core_numbers else 0
    main_core_nodes = [n for n, k in core_numbers.items() if k == max_k]
    return {
        "core_numbers": core_numbers,
        "max_k": max_k,
        "main_core_size": len(main_core_nodes),
        "main_core_nodes": main_core_nodes,
    }


# ==============================================================================
# 7. CORE-PERIPHERY ANALYSIS
# ==============================================================================
def compute_core_periphery(G):
    """Borgatti-Everett discrete core-periphery, the same model as the report (structure.core_periphery)."""
    core, stats = core_periphery(undirected_projection(G))
    return {"core": sorted(core), **stats}


# ==============================================================================
# 8. SMALL-WORLD ANALYSIS
# ==============================================================================
def compute_small_world(G, samples=5, seed=SEED):
    """Small-world sigma against the configuration model, as in the report (nullmodels.small_world_sigma).

    Skipped (NaN) when the giant component has more than SMALL_WORLD_MAX_NODES nodes, because every null
    graph needs exact shortest paths.
    """
    und = undirected_projection(G)
    n_cc = len(max(nx.connected_components(und), key=len)) if und.number_of_nodes() else 0
    empty = {"sigma": np.nan, "C": np.nan, "L": np.nan, "C_null": np.nan, "L_null": np.nan}
    if n_cc < 10 or n_cc > SMALL_WORLD_MAX_NODES:
        return {**empty, "samples": 0, "method": f"skipped ({n_cc} nodes in the giant component)"}
    sw = nm.small_world_sigma(und, samples, seed)
    return {**{k: sw[k] for k in empty}, "samples": samples, "method": "configuration model"}


# ==============================================================================
# 9. MASTER ANALYSIS PIPELINE
# ==============================================================================
def run_full_analysis(networks, output_dir=None, sw_samples=5):
    """
    Run the complete analysis pipeline on all networks.
    Saves all results to the output directory.
    """
    dest_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    all_basic = []
    all_centralities = []
    all_kcore = []
    all_core_periphery = []
    all_small_world = []

    print("\n" + "=" * 70)
    print("RUNNING FULL ANALYSIS PIPELINE")
    print("=" * 70 + "\n")

    for name, G in networks.items():
        print(f"\n{'=' * 50}")
        print(f"Network: {name}")
        print(f"{'=' * 50}")

        # Basic measures
        basic = compute_basic_measures(G)
        basic["network"] = name
        all_basic.append(basic)
        print(f"  Basic: {basic['n_nodes']} nodes, {basic['n_edges']} edges, density={basic['density']:.4f}")

        # Centralities
        centralities, top_nodes = compute_centralities(G)
        for metric, top in top_nodes.items():
            for rank, (node, score) in enumerate(top, 1):
                all_centralities.append({"network": name, "metric": metric, "rank": rank, "node": node, "score": score})
        print("  Centralities: computed (top-10 saved)")

        # HITS
        hits = compute_hits(G)
        print(f"  HITS: {len(hits['hubs'])} hubs, {len(hits['authorities'])} authorities")

        # K-core
        kcore = compute_kcore(G)
        kcore_record = {"network": name, **{k: v for k, v in kcore.items() if k != "main_core_nodes"}}
        all_kcore.append(kcore_record)
        print(f"  K-core: max_k={kcore['max_k']}, core_size={kcore['main_core_size']}")

        # Core-periphery
        cp = compute_core_periphery(G)
        all_core_periphery.append({"network": name, **{k: v for k, v in cp.items() if k != "core"}})
        print(f"  Core-periphery: {cp['core_size']} core players, fit {cp['core_fit']:.3f}")

        # Small-world
        sw = compute_small_world(G, samples=sw_samples)
        all_small_world.append({"network": name, **sw})
        print(f"  Small-world: sigma={sw['sigma']:.3f} ({sw['method']})")

    # Save all results
    pd.DataFrame(all_basic).to_csv(dest_dir / "basic_measures.csv", index=False)
    pd.DataFrame(all_centralities).to_csv(dest_dir / "centralities_top10.csv", index=False)
    pd.DataFrame(all_kcore).to_csv(dest_dir / "kcore_decomposition.csv", index=False)
    pd.DataFrame(all_core_periphery).to_csv(dest_dir / "core_periphery.csv", index=False)
    pd.DataFrame(all_small_world).to_csv(dest_dir / "small_world.csv", index=False)

    print(f"\nAll results saved to: {dest_dir}/")


# ==============================================================================
# MAIN ENTRY POINT & CLI
# ==============================================================================
def parse_args(argv=None):
    """Parse command line arguments for the analysis pipeline."""
    parser = argparse.ArgumentParser(description="Structural Analysis of Professional Tennis Networks - Full Pipeline")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run in rapid smoke-test mode (fewer Monte Carlo samples)",
    )
    parser.add_argument(
        "--network",
        type=str,
        default=None,
        help="Run analysis on a specific network only (e.g. 'M1_wins' or 'ATP_2007-2012')",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of random network samples for null model validation (default: 50, quick: 5)",
    )
    parser.add_argument(
        "--nswaps-factor",
        type=int,
        default=None,
        help="Multiplier for edge swaps per edge in null model (default: 10, quick: 2)",
    )
    parser.add_argument(
        "--skip-null",
        action="store_true",
        help="Skip Monte Carlo null model validation and compute topology/centralities only",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for generated CSV tables",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point for the analysis pipeline."""
    args = parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    num_samples = args.num_samples if args.num_samples is not None else (5 if args.quick else 50)
    nswaps_factor = args.nswaps_factor if args.nswaps_factor is not None else (2 if args.quick else 10)

    print("\n" + "=" * 70)
    print("TENNIS NETWORK ANALYSIS - FULL PIPELINE")
    print("=" * 70)

    # 1. Load networks (selective if target specified)
    networks = load_all_networks(selected_networks=args.network)

    if not networks:
        if args.network:
            print(f"WARNING: network '{args.network}' not found. Choose one of: {', '.join(NETWORK_FILES)}")
        else:
            print("\nWARNING: no networks loaded. Check data/processed.")
        return 1

    if args.network:
        print(f"Target network selected: {args.network}")

    input_paths = [
        DATA_DIR / "processed" / filename
        for name, (filename, _directed) in NETWORK_FILES.items()
        if not args.network or name == args.network
    ]
    write_run_manifest(
        "analysis",
        input_paths=input_paths,
        output_path=output_dir / "run_manifest.json",
        extra={
            "quick": args.quick,
            "network": args.network,
            "num_samples": num_samples,
            "nswaps_factor": nswaps_factor,
            "skip_null": args.skip_null,
        },
    )

    # 2. Run full analysis
    run_full_analysis(networks, output_dir=output_dir, sw_samples=2 if args.quick else 5)

    # 3. Null model validation
    if not args.skip_null:
        analyze_null_models(
            networks,
            output_path=output_dir / "null_model_results.csv",
            num_samples=num_samples,
            nswaps_factor=nswaps_factor,
        )
    else:
        print("\nSkipping null model validation (--skip-null)")

    # Hypotheses H1-H8 are tested by their own modules, not here:
    print("\nHypotheses H1-H8: run `make hypotheses triads levels` (results in results/tables).")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nResults available in: {output_dir.resolve()}")
    print("\nGenerated files:")
    for f in sorted(output_dir.glob("*.csv")):
        print(f"  - {f.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
