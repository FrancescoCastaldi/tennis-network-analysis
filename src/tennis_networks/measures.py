"""Node and network measures (course slides L05 and L06)."""

import networkx as nx
import numpy as np
import pandas as pd


def degree_centralization(g):
    """Freeman centralization of total degree, normalized to 1 for a star."""
    n = g.number_of_nodes()
    if n < 3:
        return float("nan")
    deg = np.array([d for _, d in g.degree()])
    denominator = (n - 1) * (n - 2) * (2 if g.is_directed() else 1)
    return float((deg.max() - deg).sum() / denominator)


def giant_component(g):
    """Largest strongly connected component for directed graphs, largest component otherwise."""
    comps = nx.strongly_connected_components(g) if g.is_directed() else nx.connected_components(g)
    return g.subgraph(max(comps, key=len)).copy()


def path_stats(g):
    """Average shortest path length and diameter of the giant component."""
    giant = giant_component(g)
    if giant.number_of_nodes() < 2:
        return float("nan"), float("nan")
    return nx.average_shortest_path_length(giant), nx.diameter(giant)


def global_measures(g):
    n, m = g.number_of_nodes(), g.number_of_edges()
    avg_path, diameter = path_stats(g)
    out = {
        "nodes": n,
        "edges": m,
        "directed": g.is_directed(),
        "density": nx.density(g),
        "mean_degree": 2 * m / n if not g.is_directed() else m / n,
        "degree_centralization": degree_centralization(g),
        "transitivity": nx.transitivity(g),
        "avg_clustering": nx.average_clustering(g),
        "degree_assortativity": nx.degree_assortativity_coefficient(g),
        "giant_fraction": giant_component(g).number_of_nodes() / n,
        "avg_path_giant": avg_path,
        "diameter_giant": diameter,
        "max_kcore": max(nx.core_number(g).values()),
    }
    if g.is_directed():
        out["reciprocity"] = nx.reciprocity(g)
        out["weak_components"] = nx.number_weakly_connected_components(g)
        out["strong_components"] = nx.number_strongly_connected_components(g)
    else:
        out["components"] = nx.number_connected_components(g)
    return out


def triad_census(g):
    """Triad census, defined for directed graphs only (slide L06)."""
    return nx.triads.triadic_census(g) if g.is_directed() else {}


def node_measures(g, seed, bc_threshold=5000, bc_k=500):
    """Centrality table, one row per node. Betweenness is sampled above the threshold (slide L03.1)."""
    n = g.number_of_nodes()
    k = bc_k if n > bc_threshold else None
    weighted = nx.is_weighted(g)
    df = pd.DataFrame(index=list(g.nodes()))
    if g.is_directed():
        df["in_degree"] = pd.Series(dict(g.in_degree()))
        df["out_degree"] = pd.Series(dict(g.out_degree()))
        if weighted:
            df["in_strength"] = pd.Series(dict(g.in_degree(weight="weight")))
            df["out_strength"] = pd.Series(dict(g.out_degree(weight="weight")))
    else:
        df["degree"] = pd.Series(dict(g.degree()))
        if weighted:
            df["strength"] = pd.Series(dict(g.degree(weight="weight")))
    df["betweenness"] = pd.Series(nx.betweenness_centrality(g, k=k, seed=seed))
    df["closeness"] = pd.Series(nx.closeness_centrality(g))
    df["pagerank"] = pd.Series(nx.pagerank(g))
    try:
        df["eigenvector"] = pd.Series(nx.eigenvector_centrality_numpy(g))
    except Exception:  # does not converge on most directed match networks
        df["eigenvector"] = np.nan
    df["clustering"] = pd.Series(nx.clustering(g))
    df["kcore"] = pd.Series(nx.core_number(g))
    return df.rename_axis("node")


def communities(g, seed):
    """Louvain communities with a fixed seed. Returns (list of node sets, modularity)."""
    und = g.to_undirected() if g.is_directed() else g
    parts = nx.community.louvain_communities(und, weight="weight", seed=seed)
    return parts, nx.community.modularity(und, parts, weight="weight")


def top_pagerank_share(g, k=10):
    """Share of the total PageRank held by the top k nodes (concentration of prestige)."""
    pr = np.sort(np.array(list(nx.pagerank(g, weight="weight").values())))[::-1]
    return float(pr[:k].sum() / pr.sum())


def gini(values):
    """Gini coefficient of non-negative values (0 = equality, 1 = everything to one node)."""
    x = np.sort(np.asarray(values, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def robustness_curve(g, fractions, seed, order=None):
    """Relative size of the largest component after removing a fraction of the nodes.

    attack: removal in decreasing PageRank order (or the given order);
    random: random removal with a fixed seed. Directed graphs use weak connectivity.
    """
    und = g.to_undirected() if g.is_directed() else g
    n = und.number_of_nodes()
    if order is None:
        pr = nx.pagerank(g, weight="weight")
        order = sorted(pr, key=pr.get, reverse=True)
    rnd = list(np.random.default_rng(seed).permutation(list(und.nodes())))
    base = max(len(c) for c in nx.connected_components(und))
    rows = []
    for f in fractions:
        k = int(round(f * n))
        row = {"fraction": f}
        for label, seq in (("attack", order), ("random", rnd)):
            h = und.copy()
            h.remove_nodes_from(seq[:k])
            giant = max((len(c) for c in nx.connected_components(h)), default=0)
            row[label] = giant / base
        rows.append(row)
    return pd.DataFrame(rows).set_index("fraction")


def rank_band(rank):
    """Ranking bands of the study: top 10, 11-100, others."""
    if pd.isna(rank):
        return "others"
    return "top10" if rank <= 10 else ("11-100" if rank <= 100 else "others")


def rank_band_assortativity(g, ranks):
    """Homophily by ranking band: attribute assortativity on the undirected network."""
    und = nx.Graph(g.to_undirected() if g.is_directed() else g)
    nx.set_node_attributes(und, {n: rank_band(ranks.get(n)) for n in und.nodes()}, "band")
    return float(nx.attribute_assortativity_coefficient(und, "band"))


def rank_correlation(scores, ranks):
    """Spearman correlation between a network score and the median ranking (negative = consistent)."""
    joined = pd.concat([pd.Series(scores, name="score"), ranks.rename("rank")], axis=1, join="inner").dropna()
    return float(joined["score"].corr(joined["rank"], method="spearman")), len(joined)
