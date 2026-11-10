"""Reproducible pipeline: configuration -> measures -> null models -> results/.

Run:
    python -m tennis_networks.analysis
    python -m tennis_networks.analysis --samples 100 --only example_karate
    python -m tennis_networks.analysis --centralization-only
"""

import argparse
import csv

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks import measures as ms
from tennis_networks import nullmodels as nm
from tennis_networks.config import (
    FIGURES,
    NULL_MODELS,
    PROCESSED,
    TABLES,
    load_config,
    seed_everything,
    write_run_manifest,
)
from tennis_networks.loaders import load_network

NULL_STATS = {
    "avg_clustering": nx.average_clustering,
    "transitivity": nx.transitivity,
    "degree_assortativity": nx.degree_assortativity_coefficient,
}


def plot_degree_distribution(g, path):
    deg = np.array([d for _, d in g.degree()])
    values, counts = np.unique(deg[deg > 0], return_counts=True)
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    ax.loglog(values, counts / counts.sum(), "o", markersize=4)
    ax.set_xlabel("degree k")
    ax.set_ylabel("P(k)")
    ax.set_title(g.graph["id"])
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_robustness(curve, nid, path):
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    ax.plot(curve.index, curve["attack"], "o-", markersize=3, label="attack (PageRank)")
    ax.plot(curve.index, curve["random"], "s-", markersize=3, label="random")
    ax.set_xlabel("fraction of players removed")
    ax.set_ylabel("relative giant component")
    ax.set_title(nid)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def analyse(spec, cfg, samples, cli_samples=False):
    seed = cfg["seed"]
    g = load_network(spec)
    nid = spec["id"]
    print(f"[{nid}] {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")

    nodes = ms.node_measures(g, seed, cfg["betweenness_sample_threshold"], cfg["betweenness_sample_size"])
    parts, mod = ms.communities(g, seed)
    nodes["community"] = pd.Series({n: i for i, part in enumerate(parts) for n in part})
    nodes.to_csv(TABLES / f"{nid}_nodes.csv", encoding="utf-8")

    glob = ms.global_measures(g)
    glob.update({"communities": len(parts), "modularity": mod})
    for key, val in ms.triad_census(g).items():
        glob[f"triad_{key}"] = val

    glob["top10_pagerank_share"] = ms.top_pagerank_share(g, 10)
    strength = nodes["in_strength"] if "in_strength" in nodes else nodes.get("in_degree", nodes.get("degree"))
    glob["gini_in_strength"] = ms.gini(strength)
    if spec.get("ranks"):
        ranks = pd.read_csv(PROCESSED / spec["ranks"], index_col="player")["rank"]
        glob["spearman_pagerank_atp_rank"], glob["players_with_rank"] = ms.rank_correlation(nodes["pagerank"], ranks)
        glob["rank_band_assortativity"] = ms.rank_band_assortativity(g, ranks)

    samples = samples if cli_samples else spec.get("null_samples", samples)
    null = nm.null_statistics(g, NULL_STATS, samples, seed)
    null_rows = [
        {"statistic": name, "samples": samples, **nm.compare_to_null(glob[name], null[name])} for name in NULL_STATS
    ]
    if not g.is_directed():
        sw = nm.small_world_sigma(g, spec.get("small_world_samples", min(samples, 100)), seed)
        glob["small_world_sigma"] = sw["sigma"]
    pd.DataFrame(null_rows).to_csv(NULL_MODELS / f"{nid}_null.csv", index=False, encoding="utf-8")

    curve = ms.robustness_curve(g, np.round(np.arange(0, 0.51, 0.05), 2), seed)
    curve.to_csv(TABLES / f"{nid}_robustness.csv", encoding="utf-8")
    plot_robustness(curve, nid, FIGURES / f"{nid}_robustness.png")
    plot_degree_distribution(g, FIGURES / f"{nid}_degree.png")
    return {"network": nid, **glob}


def refresh_centralization(cfg, config_path=None):
    """Refresh the global centralization column without rerunning null models or other stages."""
    results_path = TABLES / "global_measures.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"Run the full analysis before refreshing centralization: {results_path}")

    with results_path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.reader(source))
    if not rows:
        raise ValueError("Global measures table is empty")

    header = rows[0]
    required = {"network", "degree_centralization"}
    if missing := required - set(header):
        raise ValueError(f"Global measures table is missing columns: {', '.join(sorted(missing))}")
    network_index = header.index("network")
    centralization_index = header.index("degree_centralization")

    specs = {spec["id"]: spec for spec in cfg["networks"]}
    unknown = sorted({row[network_index] for row in rows[1:]} - set(specs))
    if unknown:
        raise ValueError(f"Networks in global measures are missing from the configuration: {', '.join(unknown)}")

    for row in rows[1:]:
        value = ms.degree_centralization(load_network(specs[row[network_index]]))
        row[centralization_index] = "" if pd.isna(value) else repr(float(value))
    with results_path.open("w", encoding="utf-8", newline="") as destination:
        csv.writer(destination, lineterminator="\n").writerows(rows)
    input_paths = [PROCESSED / spec["file"] for spec in cfg["networks"] if spec.get("file")]
    write_run_manifest(
        "analysis",
        config_path=config_path,
        input_paths=input_paths,
        extra={"mode": "centralization-only", "seed": cfg["seed"]},
    )
    print(f"Updated degree_centralization in {results_path}")
    return results_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=None)
    parser.add_argument("--samples", type=int, default=None, help="null graphs per statistic (default from config)")
    parser.add_argument("--only", default=None, help="id of a single network")
    parser.add_argument(
        "--centralization-only",
        action="store_true",
        help="refresh degree centralization in an existing global table without rerunning null models",
    )
    args = parser.parse_args()

    if args.centralization_only and (args.only or args.samples is not None):
        parser.error("--centralization-only cannot be combined with --only or --samples")

    cfg = load_config(args.config)
    seed_everything(cfg["seed"])
    if args.centralization_only:
        refresh_centralization(cfg, config_path=args.config)
        return

    samples = args.samples or cfg["null_model_samples"]
    for folder in (TABLES, FIGURES, NULL_MODELS):
        folder.mkdir(parents=True, exist_ok=True)

    specs = [s for s in cfg["networks"] if not args.only or s["id"] == args.only]
    input_paths = [PROCESSED / spec["file"] for spec in specs if spec.get("file")]
    input_paths.extend(PROCESSED / spec["ranks"] for spec in specs if spec.get("ranks"))
    write_run_manifest(
        "analysis",
        config_path=args.config,
        input_paths=input_paths,
        extra={"samples": samples, "only": args.only, "seed": cfg["seed"]},
    )
    rows = [analyse(s, cfg, samples, args.samples is not None) for s in specs]
    pd.DataFrame(rows).to_csv(TABLES / "global_measures.csv", index=False, encoding="utf-8")
    print(f"Results in {TABLES.parent}")


if __name__ == "__main__":
    main()
