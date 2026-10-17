"""Build NetworkX graphs from the entries of config/networks.json."""

import networkx as nx
import pandas as pd

from tennis_networks.config import PROCESSED


def load_network(spec):
    """Return the graph described by one configuration entry.

    Self-loops are removed and parallel edges collapsed, because the edge-swap
    null models need simple graphs.
    """
    directed = bool(spec.get("directed", False))
    if spec.get("builtin") == "karate_club":
        g = nx.karate_club_graph()
    else:
        path = PROCESSED / spec["file"]
        if path.suffix == ".graphml":
            g = nx.read_graphml(path)
        else:
            df = pd.read_csv(path, dtype={"source": str, "target": str})
            cols = ["source", "target"] + (["weight"] if "weight" in df.columns else [])
            g = nx.from_pandas_edgelist(
                df[cols],
                edge_attr="weight" if "weight" in cols else None,
                create_using=nx.DiGraph if directed else nx.Graph,
            )
    g = nx.DiGraph(g) if directed else nx.Graph(g)
    g.remove_edges_from(list(nx.selfloop_edges(g)))
    g.graph["id"] = spec["id"]
    return g


def load_undirected(name):
    """Undirected, unweighted projection of a processed edge list (two players linked if they ever met)."""
    edges = pd.read_csv(PROCESSED / f"{name}.csv")
    return nx.Graph(nx.from_pandas_edgelist(edges, "source", "target"))
