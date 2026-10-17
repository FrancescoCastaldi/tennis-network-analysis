"""Null models and significance against them (course slide L04)."""

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks.measures import giant_component


def _swap_edges(edges, directed, nswap, rng):
    """Degree-preserving double-edge swaps; self-loops and parallel edges are rejected.

    Directed: (a->b, c->d) becomes (a->d, c->b), so in- and out-degrees are unchanged.
    Undirected: (a-b, c-d) becomes (a-d, c-b) or (a-c, b-d).
    """
    edges = [tuple(e) for e in edges]
    key = (lambda u, v: (u, v)) if directed else (lambda u, v: (u, v) if u <= v else (v, u))
    present = {key(u, v) for u, v in edges}
    m = len(edges)
    picks = rng.integers(0, m, size=(nswap, 2))
    flips = rng.random(nswap) < 0.5
    for (i, j), flip in zip(picks, flips, strict=True):
        if i == j:
            continue
        a, b = edges[i]
        c, d = edges[j]
        if not directed and flip:
            c, d = d, c
        if a == d or c == b or len({a, b, c, d}) < 4 and not directed:
            continue
        e1, e2 = key(a, d), key(c, b)
        if e1 in present or e2 in present or e1 == e2:
            continue
        present.discard(key(a, b))
        present.discard(key(c, d))
        present.add(e1)
        present.add(e2)
        edges[i], edges[j] = (a, d), (c, b)
    return edges


def degree_preserving_null(g, rng, swaps_per_edge=10):
    """One realisation of the configuration model obtained by edge swaps.

    Keeps the degree sequence (in and out for directed graphs). Weights are not
    kept: the null model is about topology.
    """
    nodes = list(g.nodes())
    index = {n: i for i, n in enumerate(nodes)}
    edges = [(index[u], index[v]) for u, v in g.edges()]
    h = nx.DiGraph() if g.is_directed() else nx.Graph()
    h.add_nodes_from(nodes)
    if len(edges) >= 4:
        edges = _swap_edges(edges, g.is_directed(), swaps_per_edge * len(edges), rng)
    h.add_edges_from((nodes[u], nodes[v]) for u, v in edges)
    return h


def null_distribution(g, statistic, samples, seed):
    """Values of `statistic(graph)` over `samples` null graphs, with a fixed seed."""
    rng = np.random.default_rng(seed)
    return np.array([statistic(degree_preserving_null(g, rng)) for _ in range(samples)])


def null_statistics(g, statistics, samples, seed):
    """All statistics on the same null graphs: one row per sample, one column per statistic.

    Each null graph is generated once, which is the expensive part on large networks.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(samples):
        h = degree_preserving_null(g, rng)
        rows.append({name: fn(h) for name, fn in statistics.items()})
    return pd.DataFrame(rows, columns=list(statistics))


def compare_to_null(observed, null_values):
    """z-score and two-sided empirical p-value (with the +1 correction)."""
    null_values = np.asarray(null_values, dtype=float)
    mu, sd = null_values.mean(), null_values.std(ddof=1)
    z = (observed - mu) / sd if sd > 0 else float("nan")
    extreme = np.sum(np.abs(null_values - mu) >= abs(observed - mu))
    p = (extreme + 1) / (len(null_values) + 1)
    return {"observed": observed, "null_mean": mu, "null_sd": sd, "z": z, "p_empirical": p}


def small_world_sigma(g, samples, seed):
    """sigma = (C / C_null) / (L / L_null) on the giant component (Humphries and Gurney)."""
    giant = giant_component(g)
    c_obs = nx.average_clustering(giant)
    l_obs = nx.average_shortest_path_length(giant)
    rng = np.random.default_rng(seed)
    cs, ls = [], []
    for _ in range(samples):
        h = giant_component(degree_preserving_null(giant, rng))
        cs.append(nx.average_clustering(h))
        ls.append(nx.average_shortest_path_length(h))
    c_null, l_null = np.mean(cs), np.mean(ls)
    return {"C": c_obs, "L": l_obs, "C_null": c_null, "L_null": l_null, "sigma": (c_obs / c_null) / (l_obs / l_null)}
