"""Reproduce the main figures of Michieli (2018) on the converted networks.

Run (after `python -m tennis_networks.michieli`):
    python -m tennis_networks.reproduce

Output: results/tables/michieli_reproduction.csv (value in the paper, value obtained, note).
Average distances and diameters are estimated by BFS from 1,000 sources drawn with the configured seed.
"""

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks.config import PROCESSED, TABLES, load_config

# Paper, Sections II.B and II.F-G, Table III (column "PR with Teleport.").
PAPER_PAGERANK_TOP10 = [
    "Connors J.",
    "Lendl I.",
    "Federer R.",
    "Mcenroe J.",
    "Nadal R.",
    "Djokovic N.",
    "Vilas G.",
    "Nastase I.",
    "Agassi A.",
    "Borg B.",
]


def read(name, directed):
    df = pd.read_csv(PROCESSED / name)
    attr = "weight" if "weight" in df.columns else None
    return nx.from_pandas_edgelist(
        df, "source", "target", edge_attr=attr, create_using=nx.DiGraph if directed else nx.Graph
    )


def sampled_distances(g, seed, k=1000):
    """Average distance over reachable pairs and longest distance observed from k random sources."""
    rng = np.random.default_rng(seed)
    nodes = list(g.nodes())
    sources = rng.choice(len(nodes), size=min(k, len(nodes)), replace=False)
    total, count, longest = 0, 0, 0
    for i in sources:
        lengths = nx.single_source_shortest_path_length(g, nodes[i])
        d = np.fromiter(lengths.values(), dtype=int)
        d = d[d > 0]
        total, count, longest = total + d.sum(), count + len(d), max(longest, d.max(initial=0))
    return total / count, longest


def main():
    seed = load_config()["seed"]
    rows = []

    def add(net, measure, paper, ours, note=""):
        rows.append({"network": net, "measure": measure, "paper": paper, "ours": ours, "note": note})

    sampled = "estimated from 1,000 sources"
    g1 = read("michieli_1_wins.csv", True)
    scc = max(nx.strongly_connected_components(g1), key=len)
    add("M1 directed", "largest strongly connected component", 2428, len(scc))
    d, diam = sampled_distances(g1, seed)
    add("M1 directed", "average distance", 3.48, round(d, 2), sampled)
    add("M1 directed", "diameter", 10, diam, "longest distance observed from 1,000 sources")
    pr = nx.pagerank(g1, alpha=0.85, weight="weight")
    top = sorted(pr, key=pr.get, reverse=True)[:10]
    add(
        "M1 directed",
        "top-10 PageRank players shared with the paper",
        10,
        len(set(top) & set(PAPER_PAGERANK_TOP10)),
        "ours: " + ", ".join(top),
    )

    g3 = read("michieli_3_undirected.csv", False)
    add("M3 undirected", "connected components", 1, nx.number_connected_components(g3))
    d, _ = sampled_distances(g3, seed)
    add("M3 undirected", "average distance", 3.34, round(d, 2), sampled)
    add("M3 undirected", "diameter", 8, nx.approximation.diameter(g3, seed=seed), "double-sweep approximation")
    add(
        "M3 undirected",
        "average clustering",
        0.07,
        round(nx.average_clustering(g3), 3),
        f"transitivity {nx.transitivity(g3):.3f}; no standard definition gives the value of the paper",
    )
    add("M3 undirected", "degree assortativity", -0.0076, round(nx.degree_assortativity_coefficient(g3), 4))

    g4 = read("michieli_4_extended.csv", False)
    d, _ = sampled_distances(g4, seed)
    add("M4 extended", "average distance", 3.64, round(d, 2), sampled)
    add("M4 extended", "diameter", 9, nx.approximation.diameter(g4, seed=seed), "double-sweep approximation")
    add("M4 extended", "degree assortativity", 0.272, round(nx.degree_assortativity_coefficient(g4), 4))

    out = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES / "michieli_reproduction.csv", index=False, encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
