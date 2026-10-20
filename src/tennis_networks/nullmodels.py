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


def erdos_renyi_null(g, rng):
    """Erdos-Renyi G(n, m) null graph matching node set, edge count, and directedness of g.

    Nodes have identical labels and self-loops are omitted.
    """
    nodes = list(g.nodes())
    n = len(nodes)
    m = g.number_of_edges()
    directed = g.is_directed()
    max_m = n * (n - 1) if directed else n * (n - 1) // 2
    m = min(m, max(0, max_m))
    h_int = nx.gnm_random_graph(n, m, seed=rng, directed=directed)
    return nx.relabel_nodes(h_int, dict(enumerate(nodes)))


def _sample_null_worker(args):
    """Worker function for parallel Monte Carlo null model sampling."""
    g, stat_funcs, model, seed = args
    rng = np.random.default_rng(seed)
    if model == "erdos_renyi":
        h = erdos_renyi_null(g, rng)
    elif callable(model):
        h = model(g, rng)
    else:
        h = degree_preserving_null(g, rng)
    return {name: fn(h) for name, fn in stat_funcs}


def null_distribution(g, statistic, samples, seed, model="configuration", n_jobs=1):
    """Values of `statistic(graph)` over `samples` null graphs, with a fixed seed."""
    df = null_statistics(g, {"stat": statistic}, samples, seed, model=model, n_jobs=n_jobs)
    return df["stat"].to_numpy()


def null_statistics(g, statistics, samples, seed, model="configuration", n_jobs=1):
    """All statistics on the same null graphs: one row per sample, one column per statistic.

    Each null graph is generated once, which is the expensive part on large networks.
    Supports model='configuration' (default) or model='erdos_renyi', and parallelization
    via n_jobs (default 1, -1 for all available CPU cores).

    Every null graph draws from its own child of `SeedSequence(seed)`, so the result is the
    same whatever the number of workers. In parallel, statistics and a callable model must be
    picklable (module-level functions, not lambdas).
    """
    seeds = np.random.SeedSequence(seed).spawn(samples)
    stat_items = list(statistics.items())
    worker_args = [(g, stat_items, model, s) for s in seeds]

    if n_jobs is None or n_jobs == 1:
        rows = [_sample_null_worker(a) for a in worker_args]
    else:
        import os
        from concurrent.futures import ProcessPoolExecutor

        max_workers = os.cpu_count() if n_jobs == -1 else max(1, int(n_jobs))
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            rows = list(executor.map(_sample_null_worker, worker_args))

    return pd.DataFrame(rows, columns=list(statistics))


def compare_dual_null_models(g, statistics, samples, seed, n_jobs=1):
    """Dual null model comparison: Configuration Model vs Erdos-Renyi G(n, m).

    Evaluates observed statistics on g and compares them against both null distributions.
    Returns a DataFrame comparing observed values, null means, standard deviations,
    z-scores, and empirical p-values for both models.
    """
    expected_cols = [
        "statistic",
        "observed",
        "cm_null_mean",
        "cm_null_sd",
        "cm_z",
        "cm_p_empirical",
        "er_null_mean",
        "er_null_sd",
        "er_z",
        "er_p_empirical",
    ]
    if not statistics:
        return pd.DataFrame(columns=expected_cols)

    observed = {name: fn(g) for name, fn in statistics.items()}
    cm_df = null_statistics(g, statistics, samples, seed, model="configuration", n_jobs=n_jobs)
    er_seed = int(np.random.default_rng(seed).integers(0, 2**31 - 1))
    er_df = null_statistics(g, statistics, samples, er_seed, model="erdos_renyi", n_jobs=n_jobs)

    records = []
    for name in statistics:
        obs = observed[name]
        cm_res = compare_to_null(obs, cm_df[name])
        er_res = compare_to_null(obs, er_df[name])
        records.append(
            {
                "statistic": name,
                "observed": obs,
                "cm_null_mean": cm_res["null_mean"],
                "cm_null_sd": cm_res["null_sd"],
                "cm_z": cm_res["z"],
                "cm_p_empirical": cm_res["p_empirical"],
                "er_null_mean": er_res["null_mean"],
                "er_null_sd": er_res["null_sd"],
                "er_z": er_res["z"],
                "er_p_empirical": er_res["p_empirical"],
            }
        )
    return pd.DataFrame(records)


def compare_to_null(observed, null_values):
    """z-score and two-sided empirical p-value (with the +1 correction)."""
    null_values = np.asarray(null_values, dtype=float)
    if len(null_values) == 0:
        return {
            "observed": observed,
            "null_mean": float("nan"),
            "null_sd": float("nan"),
            "z": float("nan"),
            "p_empirical": float("nan"),
        }
    mu = float(null_values.mean())
    sd = float(null_values.std(ddof=1)) if len(null_values) > 1 else float("nan")
    z = (observed - mu) / sd if (not np.isnan(sd) and sd > 0) else float("nan")
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
