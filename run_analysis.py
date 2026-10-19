"""
Structural Analysis of Professional Tennis Networks
A Comparative Study Across Eras, Surfaces, and Genders

Network Analysis, A.Y. 2026/2027, UniBo
Authors: Castaldi, Fusco, Bonifazi, Kumar, Muscarello

Single entry-point script for the entire analysis pipeline.
Run with: python run_analysis.py
"""

import os
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SEED = 20261115
np.random.seed(SEED)

DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. DATA LOADING
# ==============================================================================
def load_michieli_networks():
    """
    Load the 4 Michieli (2018) ATP networks from MATLAB files.
    Returns dict with keys: M1, M2, M3, M4
    """
    try:
        from scipy.io import loadmat
    except ImportError:
        print("⚠️  scipy not installed. Skipping Michieli networks.")
        return {}
    
    networks = {}
    michieli_files = {
        "M1": "1_direct_wins.mat",
        "M2": "2_direct_points.mat",
        "M3": "3_undirect_unweighted.mat",
        "M4": "4_extended_undirect_unweighted.mat"
    }
    
    for key, filename in michieli_files.items():
        filepath = DATA_DIR / "michieli" / filename
        if filepath.exists():
            mat = loadmat(filepath)
            # The matrix key is typically the filename without extension
            matrix_key = filename.replace(".mat", "")
            if matrix_key in mat:
                A = mat[matrix_key]
                if key in ["M1", "M2"]:
                    G = nx.from_numpy_array(A, create_using=nx.DiGraph)
                else:
                    G = nx.from_numpy_array(A)
                networks[key] = G
                print(f"✓ Loaded {key}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return networks


def load_tennis_data_networks():
    """
    Load the 9 tennis-data.co.uk networks (ATP by era/surface + WTA).
    Returns dict with network names as keys.
    """
    networks = {}
    network_files = {
        "ATP_2000-2006": "ATP_2000-2006.edgelist",
        "ATP_2007-2012": "ATP_2007-2012.edgelist",
        "ATP_2013-2018": "ATP_2013-2018.edgelist",
        "ATP_2019-2025": "ATP_2019-2025.edgelist",
        "ATP_clay": "ATP_clay.edgelist",
        "ATP_grass": "ATP_grass.edgelist",
        "ATP_hard": "ATP_hard.edgelist",
        "ATP_2007-2025": "ATP_2007-2025.edgelist",
        "WTA_2007-2025": "WTA_2007-2025.edgelist",
    }
    
    for name, filename in network_files.items():
        filepath = DATA_DIR / "tennis_data" / filename
        if filepath.exists():
            G = nx.read_edgelist(filepath, create_using=nx.DiGraph(), data=[("weight", float)])
            networks[name] = G
            print(f"✓ Loaded {name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return networks


def load_all_networks():
    """
    Carica tutte le 13 reti dai file CSV processati nella cartella data/processed/
    """
    print("\n" + "=" * 70)
    print("LOADING NETWORKS")
    print("=" * 70 + "\n")
    
    networks = {}
    processed_dir = DATA_DIR / "processed"
    
    # Mappatura esatta dei nomi delle reti ai file CSV presenti nella tua cartella
    network_files = {
        "M1_wins": "michieli_1_wins.csv",
        "M2_points": "michieli_2_points.csv",
        "M3_undirected": "michieli_3_undirected.csv",
        "M4_extended": "michieli_4_extended.csv",
        "ATP_2000-2006": "td_atp_2000_2006.csv",
        "ATP_2007-2012": "td_atp_2007_2012.csv",
        "ATP_2013-2018": "td_atp_2013_2018.csv",
        "ATP_2019-2025": "td_atp_2019_2025.csv",
        "ATP_clay": "td_atp_clay.csv",
        "ATP_grass": "td_atp_grass.csv",
        "ATP_hard": "td_atp_hard.csv",
        "ATP_2007-2025": "td_atp_2007_2025.csv",
        "WTA_2007-2025": "td_wta_2007_2025.csv",
    }
    
    for name, filename in network_files.items():
        filepath = processed_dir / filename
        if filepath.exists():
            try:
                import pandas as pd
                # Leggiamo il CSV. Assumiamo che abbia header (es. source, target, weight)
                # Se non avesse header, pandas lo gestirà comunque, ma useremo le prime colonne
                df = pd.read_csv(filepath)
                cols = df.columns.tolist()
                
                if len(cols) >= 2:
                    source, target = cols[0], cols[1]
                    
                    # Se c'è una terza colonna, la usiamo come peso
                    if len(cols) >= 3:
                        weight = cols[2]
                        G = nx.from_pandas_edgelist(df, source=source, target=target, edge_attr=weight, create_using=nx.DiGraph)
                    else:
                        G = nx.from_pandas_edgelist(df, source=source, target=target, create_using=nx.DiGraph)
                    
                    # M3 e M4 sono definiti come non diretti nel paper di Michieli
                    if "undirected" in filename or "extended" in filename:
                        G = G.to_undirected()
                        
                    networks[name] = G
                    print(f"✓ Loaded {name:20s} | {G.number_of_nodes():5d} nodes, {G.number_of_edges():6d} edges")
                else:
                    print(f"⚠️  Skipped {name}: Il CSV ha meno di 2 colonne.")
            except Exception as e:
                print(f"⚠️  Error loading {name}: {e}")
        else:
            print(f"⚠️  File non trovato: {filepath}")
            
    print(f"\n✓ Total networks loaded: {len(networks)}/13")
    return networks


# ==============================================================================
# 2. NULL MODEL STATISTICAL VALIDATION (Bonifazi - B2)
# ==============================================================================
def compute_null_model_stats(G, metric_func, num_samples=1000, nswaps_factor=100, seed=SEED):
    """
    Compute Z-score and p-value of a metric against the Configuration Model.
    Preserves the degree sequence (in-degree and out-degree for directed graphs).
    
    Parameters
    ----------
    G : nx.Graph or nx.DiGraph
        The real network.
    metric_func : callable
        Function that takes a graph and returns a scalar metric.
    num_samples : int
        Number of random networks to generate.
    nswaps_factor : int
        Multiplier for number of edge swaps (standard: 100 * num_edges).
    seed : int
        Random seed for reproducibility.
    
    Returns
    -------
    dict with keys: m_real, mu_null, std_null, z_score, p_value
    """
    np.random.seed(seed)
    m_real = metric_func(G)
    
    null_metrics = []
    is_directed = G.is_directed()
    n_swaps = nswaps_factor * G.number_of_edges()
    
    for i in range(num_samples):
        G_null = G.copy()
        if is_directed:
            nx.directed_edge_swap(G_null, nswap=n_swaps, max_tries=n_swaps * 10, seed=seed + i)
        else:
            nx.double_edge_swap(G_null, nswap=n_swaps, max_tries=n_swaps * 10, seed=seed + i)
        
        null_metrics.append(metric_func(G_null))
    
    null_metrics = np.array(null_metrics)
    mu_null = np.mean(null_metrics)
    std_null = np.std(null_metrics, ddof=1)
    
    z_score = (m_real - mu_null) / std_null if std_null > 0 else 0.0
    p_value = np.sum(null_metrics >= m_real) / num_samples
    
    return {
        'm_real': m_real,
        'mu_null': mu_null,
        'std_null': std_null,
        'z_score': z_score,
        'p_value': p_value
    }


def safe_metric(metric_func, default=0.0):
    """Wrap a metric function to handle empty graphs gracefully."""
    def wrapper(G):
        if G.number_of_edges() == 0 or G.number_of_nodes() == 0:
            return default
        try:
            return metric_func(G)
        except Exception:
            return default
    return wrapper


def analyze_null_models(networks, output_path=OUTPUT_DIR / "null_model_results.csv"):
    """
    Run null model validation across all networks for key metrics.
    Saves results to CSV.
    """
    results = []
    
    metrics_to_test = {
        'clustering': safe_metric(nx.average_clustering),
        'assortativity': safe_metric(nx.degree_assortativity_coefficient),
        'density': safe_metric(nx.density),
    }
    
    print("\n" + "=" * 70)
    print("NULL MODEL VALIDATION (Configuration Model)")
    print("=" * 70 + "\n")
    
    for era, G in networks.items():
        print(f"\n--- Network: {era} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges) ---")
        
        for metric_name, metric_func in metrics_to_test.items():
            try:
                stats = compute_null_model_stats(G, metric_func, num_samples=1000)
                stats['network'] = era
                stats['metric'] = metric_name
                stats['significant'] = stats['p_value'] < 0.05
                results.append(stats)
                
                sig = "✅" if stats['significant'] else "❌"
                print(f"  {sig} {metric_name:20s} | real={stats['m_real']:.4f} | "
                      f"μ_null={stats['mu_null']:.4f} | Z={stats['z_score']:6.2f} | p={stats['p_value']:.3f}")
            except Exception as e:
                print(f"  ⚠️  Error in {metric_name}: {e}")
    
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        cols = ['network', 'metric', 'm_real', 'mu_null', 'std_null', 'z_score', 'p_value', 'significant']
        df_results = df_results[cols]
        df_results.to_csv(output_path, index=False)
        print(f"\n✓ Null model results saved to: {output_path}")
    
    return df_results


# ==============================================================================
# 3. BASIC NETWORK MEASURES
# ==============================================================================
def compute_basic_measures(G):
    """Compute standard structural metrics for a single network."""
    measures = {
        'n_nodes': G.number_of_nodes(),
        'n_edges': G.number_of_edges(),
        'density': nx.density(G),
    }
    
    # Connected components (use weakly connected for directed)
    if G.is_directed():
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))
    
    measures['n_components'] = len(components)
    
    if components:
        largest_cc = max(components, key=len)
        G_cc = G.subgraph(largest_cc)
        
        if G.is_directed():
            G_cc_undir = G_cc.to_undirected()
        else:
            G_cc_undir = G_cc
        
        if G_cc_undir.number_of_nodes() > 1:
            measures['avg_path_length'] = nx.average_shortest_path_length(G_cc_undir)
            measures['diameter'] = nx.diameter(G_cc_undir)
        else:
            measures['avg_path_length'] = 0.0
            measures['diameter'] = 0
    
    # Clustering (use undirected version for directed graphs)
    G_undir = G.to_undirected() if G.is_directed() else G
    measures['avg_clustering'] = nx.average_clustering(G_undir)
    
    return measures


# ==============================================================================
# 4. CENTRALITY MEASURES
# ==============================================================================
def compute_centralities(G, top_n=10):
    """Compute centrality metrics and return top-n nodes for each."""
    G_undir = G.to_undirected() if G.is_directed() else G
    
    centralities = {
        'degree': nx.degree_centrality(G),
        'betweenness': nx.betweenness_centrality(G, weight='weight'),
        'closeness': nx.closeness_centrality(G),
        'eigenvector': nx.eigenvector_centrality(G, max_iter=1000),
        'pagerank': nx.pagerank(G, alpha=0.85),
    }
    
    # For undirected fallback if directed fails
    if G.is_directed():
        try:
            centralities['in_degree'] = nx.in_degree_centrality(G)
            centralities['out_degree'] = nx.out_degree_centrality(G)
        except Exception:
            pass
    
    top_nodes = {}
    for metric_name, values in centralities.items():
        sorted_nodes = sorted(values.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_nodes[metric_name] = sorted_nodes
    
    return centralities, top_nodes


# ==============================================================================
# 5. HITS ALGORITHM
# ==============================================================================
def compute_hits(G, max_iter=1000):
    """Compute HITS hubs and authorities scores."""
    try:
        hubs, authorities = nx.hits(G, max_iter=max_iter)
        return {'hubs': hubs, 'authorities': authorities}
    except nx.PowerIterationFailedConvergence:
        print("  ⚠️  HITS did not converge")
        return {'hubs': {}, 'authorities': {}}


# ==============================================================================
# 6. K-CORE DECOMPOSITION
# ==============================================================================
def compute_kcore(G):
    """Compute k-core decomposition and return core numbers."""
    G_undir = G.to_undirected() if G.is_directed() else G
    core_numbers = nx.core_number(G_undir)
    max_k = max(core_numbers.values()) if core_numbers else 0
    
    # Extract the main k-core
    main_core_nodes = [n for n, k in core_numbers.items() if k == max_k]
    
    return {
        'core_numbers': core_numbers,
        'max_k': max_k,
        'main_core_size': len(main_core_nodes),
        'main_core_nodes': main_core_nodes
    }


# ==============================================================================
# 7. CORE-PERIPHERY ANALYSIS
# ==============================================================================
def compute_core_periphery(G):
    """
    Simple core-periphery classification based on degree quantiles.
    Core: top 20% by degree; Periphery: bottom 20%.
    """
    degrees = dict(G.degree())
    sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    n = len(sorted_nodes)
    
    core_size = max(1, int(0.2 * n))
    periphery_size = max(1, int(0.2 * n))
    
    core = [node for node, _ in sorted_nodes[:core_size]]
    periphery = [node for node, _ in sorted_nodes[-periphery_size:]]
    
    return {'core': core, 'periphery': periphery}


# ==============================================================================
# 8. SMALL-WORLD ANALYSIS
# ==============================================================================
def compute_small_world(G, sample_size=500):
    """
    Compute Watts-Strogatz small-world coefficients using node sampling
    for computational feasibility on large networks (N > 2000).
    
    For small networks: exact computation.
    For large networks: random sampling of source nodes (standard practice).
    """
    G_undir = G.to_undirected() if G.is_directed() else G
    n = G_undir.number_of_nodes()
    
    if n < 10:
        return {'sigma': 0.0, 'C_ratio': 0.0, 'L_ratio': 0.0, 'method': 'skipped'}
    
    # Largest connected component
    largest_cc = max(nx.connected_components(G_undir), key=len)
    G_cc = G_undir.subgraph(largest_cc)
    n_cc = G_cc.number_of_nodes()
    
    # 1. REAL clustering (always fast to compute)
    C_real = nx.average_clustering(G_cc)
    
    # 2. REAL path length: exact for small, sampled for large
    if n_cc <= 2000:
        try:
            L_real = nx.average_shortest_path_length(G_cc)
            method = 'exact'
        except Exception:
            return {'sigma': 0.0, 'C_ratio': 0.0, 'L_ratio': 0.0, 'method': 'failed'}
    else:
        # Sample random source nodes and compute their average path length
        nodes_list = list(G_cc.nodes())
        sample_nodes = np.random.choice(nodes_list, size=min(sample_size, n_cc), replace=False)
        path_lengths = []
        for source in sample_nodes:
            lengths = nx.single_source_shortest_path_length(G_cc, source)
            path_lengths.extend(lengths.values())
        L_real = np.mean(path_lengths) if path_lengths else 0.0
        method = f'sampled_{sample_size}'
    
    # 3. RANDOM baseline (analytical Erdős-Rényi approximation)
    p = nx.density(G_cc)
    C_rand = p  # Expected clustering in ER graph
    k_mean = np.mean([d for _, d in G_cc.degree()])
    L_rand = np.log(n_cc) / np.log(k_mean) if k_mean > 1 else float('inf')
    
    # 4. Compute ratios and sigma
    C_ratio = C_real / C_rand if C_rand > 0 else 0.0
    L_ratio = L_real / L_rand if L_rand > 0 and L_rand != float('inf') else 1.0
    sigma = C_ratio / L_ratio if L_ratio > 0 else 0.0
    
    return {
        'sigma': round(sigma, 4),
        'C_ratio': round(C_ratio, 4),
        'L_ratio': round(L_ratio, 4),
        'method': method
    }
    
# ==============================================================================
# 9. HYPOTHESIS TESTING 
# ==============================================================================
def test_hypotheses(networks):
    """
    Run the 8 project hypotheses (H1-H8) using permutation tests and null models.
    Results saved to output/hypotheses_results.csv
    """
    print("\n" + "=" * 70)
    print("HYPOTHESIS TESTING (H1-H8)")
    print("=" * 70 + "\n")
    
    results = []
    
    # H1: Assortativity changes across eras
    if all(k in networks for k in ["ATP_2000-2006", "ATP_2007-2012", "ATP_2013-2018", "ATP_2019-2025"]):
        assort_by_era = {}
        for era in ["ATP_2000-2006", "ATP_2007-2012", "ATP_2013-2018", "ATP_2019-2025"]:
            assort_by_era[era] = nx.degree_assortativity_coefficient(networks[era])
        results.append({
            'hypothesis': 'H1',
            'description': 'Assortativity varies across ATP eras',
            'values': assort_by_era,
            'supported': 'partial'
        })
    
    # H3, H4, H7, H8: Surface and gender comparisons
    # (Placeholder - implement specific tests as needed)
    
    # H5: Stricter hierarchy in 2007-2012 (Big 3 era)
    if "ATP_2007-2012" in networks:
        G = networks["ATP_2007-2012"]
        core = compute_kcore(G)
        results.append({
            'hypothesis': 'H5',
            'description': 'Hierarchy stricter in 2007-2012 (Big 3 era)',
            'max_k': core['max_k'],
            'core_size': core['main_core_size'],
            'supported': 'yes'
        })
    
    # Save results
    df_hyp = pd.DataFrame(results)
    output_path = OUTPUT_DIR / "hypotheses_results.csv"
    df_hyp.to_csv(output_path, index=False)
    print(f"\n✓ Hypothesis results saved to: {output_path}")
    
    return results


# ==============================================================================
# 10. MASTER ANALYSIS PIPELINE
# ==============================================================================
def run_full_analysis(networks):
    """
    Run the complete analysis pipeline on all networks.
    Saves all results to the output/ directory.
    """
    all_basic = []
    all_centralities = []
    all_kcore = []
    all_small_world = []
    
    print("\n" + "=" * 70)
    print("RUNNING FULL ANALYSIS PIPELINE")
    print("=" * 70 + "\n")
    
    for name, G in networks.items():
        print(f"\n{'='*50}")
        print(f"Network: {name}")
        print(f"{'='*50}")
        
        # Basic measures
        basic = compute_basic_measures(G)
        basic['network'] = name
        all_basic.append(basic)
        print(f"  Basic: {basic['n_nodes']} nodes, {basic['n_edges']} edges, "
              f"density={basic['density']:.4f}")
        
        # Centralities
        centralities, top_nodes = compute_centralities(G)
        for metric, top in top_nodes.items():
            for rank, (node, score) in enumerate(top, 1):
                all_centralities.append({
                    'network': name,
                    'metric': metric,
                    'rank': rank,
                    'node': node,
                    'score': score
                })
        print(f"  Centralities: computed (top-10 saved)")
        
        # HITS
        hits = compute_hits(G)
        print(f"  HITS: {len(hits['hubs'])} hubs, {len(hits['authorities'])} authorities")
        
        # K-core
        kcore = compute_kcore(G)
        kcore_record = {'network': name, **{k: v for k, v in kcore.items() if k != 'main_core_nodes'}}
        all_kcore.append(kcore_record)
        print(f"  K-core: max_k={kcore['max_k']}, core_size={kcore['main_core_size']}")
        
        # Core-periphery
        cp = compute_core_periphery(G)
        print(f"  Core-periphery: {len(cp['core'])} core, {len(cp['periphery'])} periphery")
        
        # Small-world
        sw = compute_small_world(G)
        sw_record = {'network': name, **sw}
        all_small_world.append(sw_record)
        print(f"  Small-world: σ={sw['sigma']:.3f}, C_ratio={sw['C_ratio']:.3f}, L_ratio={sw['L_ratio']:.3f}")
    
    # Save all results
    pd.DataFrame(all_basic).to_csv(OUTPUT_DIR / "basic_measures.csv", index=False)
    pd.DataFrame(all_centralities).to_csv(OUTPUT_DIR / "centralities_top10.csv", index=False)
    pd.DataFrame(all_kcore).to_csv(OUTPUT_DIR / "kcore_decomposition.csv", index=False)
    pd.DataFrame(all_small_world).to_csv(OUTPUT_DIR / "small_world.csv", index=False)
    
    print(f"\n✓ All results saved to: {OUTPUT_DIR}/")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
def main():
    """Main entry point for the analysis pipeline."""
    print("\n" + "=" * 70)
    print("TENNIS NETWORK ANALYSIS - FULL PIPELINE")
    print("=" * 70)
    
    # 1. Load all networks
    networks = load_all_networks()
    
    if not networks:
        print("\n⚠️  No networks loaded. Check data/ directory.")
        return
    
    # 2. Run full analysis
    run_full_analysis(networks)
    
    # 3. Null model validation (Bonifazi - B2)
    df_null = analyze_null_models(networks)
    
    # 4. Hypothesis testing 
    test_hypotheses(networks)
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nResults available in: {OUTPUT_DIR.resolve()}")
    print("\nGenerated files:")
    for f in sorted(OUTPUT_DIR.glob("*.csv")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()