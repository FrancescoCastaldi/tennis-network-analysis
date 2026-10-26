"""Rich-club coefficient and elite closure against null models (course slide L06).

Measures whether high-degree players form tightly interconnected subgraphs
beyond degree-sequence expectations (Colizza et al. 2006, Newman 2018 §7.8),
against degree-preserving configuration null models.

Run:
    python -m tennis_networks.rich_club [--jobs n]

The summary reports, for each network, the degree threshold k* with the largest z-score among the
candidate thresholds (clubs of at least 5 players and at most half of the network). Because k* is
chosen after looking at every threshold, its significance is assessed with a max-statistic test:
for each null graph the largest z over the same thresholds is computed, and the p-value is the
share of null graphs whose maximum reaches the observed one (one-sided, +1 correction). This
p-value accounts for the choice of k*; the pointwise p-value of k* alone does not.

Seed and number of null graphs come from config/networks.json (seed, test_null_samples).
Output: results/tables/rich_club_summary.csv
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks.config import TABLES, load_config
from tennis_networks.loaders import load_undirected
from tennis_networks.nullmodels import degree_preserving_null

# Comparative networks configured for hypothesis testing
NETWORKS = (
    "td_atp_2000_2006",
    "td_atp_2007_2012",
    "td_atp_2013_2018",
    "td_atp_2019_2025",
    "td_atp_clay",
    "td_atp_grass",
    "td_atp_hard",
    "td_atp_2007_2025",
    "td_wta_2007_2025",
)


def compute_rich_club(g: nx.Graph) -> dict[int, tuple[int, float]]:
    """Computes unnormalised rich-club coefficient phi(k) and node count N_{>k}."""
    g_undir = g.to_undirected() if g.is_directed() else g
    raw_rc = nx.rich_club_coefficient(g_undir, normalized=False)
    degrees = dict(g_undir.degree())
    deg_values = np.array(list(degrees.values()))

    result = {}
    for k, phi in raw_rc.items():
        n_nodes = int(np.sum(deg_values > k))
        result[k] = (n_nodes, float(phi))
    return result


def _sample_null_rich_club(args: tuple[nx.Graph, np.random.SeedSequence]) -> dict[int, float]:
    """Helper worker to sample one configuration model and compute its rich-club curve."""
    g, seed_seq = args
    rng = np.random.default_rng(seed_seq)
    h = degree_preserving_null(g, rng)
    rc = nx.rich_club_coefficient(h, normalized=False)
    return {k: float(v) for k, v in rc.items()}


def _rich_club_curves(g, null_samples, seed, n_jobs):
    """Observed curve and the matrix of null curves on the same thresholds.

    Returns (ks, n_nodes, phi_obs, null) where null has one row per null graph and one column per k.
    """
    g_undir = g.to_undirected() if g.is_directed() else g
    obs_rc = compute_rich_club(g_undir)
    ks = sorted(obs_rc)
    children = np.random.SeedSequence(seed).spawn(null_samples)
    tasks = [(g_undir, c) for c in children]
    if n_jobs > 1:
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            null_curves = list(executor.map(_sample_null_rich_club, tasks))
    else:
        null_curves = [_sample_null_rich_club(t) for t in tasks]
    null = np.array([[nc.get(k, 0.0) for k in ks] for nc in null_curves], dtype=float).reshape(null_samples, len(ks))
    n_nodes = np.array([obs_rc[k][0] for k in ks])
    phi_obs = np.array([obs_rc[k][1] for k in ks])
    return ks, n_nodes, phi_obs, null


def _z_scores(phi_obs, null):
    """z of the observed curve and of every null curve, against the null mean and sd (ddof=1) of each k.

    Thresholds where the null sd is 0 get NaN: the z-score is not defined there.
    """
    mean = null.mean(axis=0)
    sd = null.std(axis=0, ddof=1) if len(null) > 1 else np.zeros(null.shape[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        z_obs = np.where(sd > 0, (phi_obs - mean) / sd, np.nan)
        z_null = np.where(sd > 0, (null - mean) / sd, np.nan)
    return mean, sd, z_obs, z_null


def normalized_rich_club(
    g: nx.Graph,
    null_samples: int = 200,
    seed: int = 20261115,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Observed phi(k) against degree-preserving configuration null models, one row per threshold k.

    `p_value` is pointwise (two-sided, +1 correction): valid for a threshold fixed in advance, not for
    a threshold chosen because its z is the largest (see `max_z_test`).
    """
    columns = ["k", "n_nodes", "phi_obs", "phi_null_mean", "phi_null_std", "rho_rich", "z_score", "p_value"]
    ks, n_nodes, phi_obs, null = _rich_club_curves(g, null_samples, seed, n_jobs)
    if not ks:
        return pd.DataFrame(columns=columns)
    mean, sd, z_obs, _ = _z_scores(phi_obs, null)
    extreme = (np.abs(null - mean) >= np.abs(phi_obs - mean) - 1e-12).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = np.where(mean > 0, phi_obs / mean, np.nan)
    return pd.DataFrame(
        {
            "k": ks,
            "n_nodes": n_nodes,
            "phi_obs": phi_obs,
            "phi_null_mean": mean,
            "phi_null_std": sd,
            "rho_rich": rho,
            "z_score": z_obs,
            "p_value": (extreme + 1) / (null_samples + 1),
        },
        columns=columns,
    )


def max_z_test(z_obs, z_null, candidates):
    """Max-statistic test over the candidate thresholds (one-sided, +1 correction).

    The observed statistic is the largest z among the candidates; its null distribution is the
    largest z of each null graph over the same candidates. Returns the index of the peak threshold,
    the observed maximum, the 95th percentile of the null maxima and the p-value.
    """
    idx = np.flatnonzero(candidates & ~np.isnan(z_obs))
    if idx.size == 0:
        return None
    peak = idx[np.nanargmax(z_obs[idx])]
    observed = float(z_obs[peak])
    null_max = np.nanmax(z_null[:, idx], axis=1)
    p_max = (np.sum(null_max >= observed - 1e-12) + 1) / (len(null_max) + 1)
    return int(peak), observed, float(np.quantile(null_max, 0.95)), float(p_max)


def rich_club_summary(
    networks: dict[str, nx.Graph],
    null_samples: int = 200,
    seed: int = 20261115,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Peak rich-club threshold of each network and its max-statistic test.

    Candidate thresholds: clubs of at least 5 players and at most half of the network, where the null
    mean is positive and the null sd is not 0.
    """
    summary_rows = []
    for name, g in networks.items():
        ks, n_nodes, phi_obs, null = _rich_club_curves(g, null_samples, seed, n_jobs)
        if not ks:
            continue
        mean, _, z_obs, z_null = _z_scores(phi_obs, null)
        candidates = (n_nodes >= 5) & (n_nodes <= len(g) * 0.5) & (mean > 0)
        result = max_z_test(z_obs, z_null, candidates)
        if result is None:
            continue
        peak, z_peak, z_crit, p_max = result
        extreme = np.sum(np.abs(null[:, peak] - mean[peak]) >= abs(phi_obs[peak] - mean[peak]) - 1e-12)
        summary_rows.append(
            {
                "network": name,
                "peak_k": int(ks[peak]),
                "elite_nodes": int(n_nodes[peak]),
                "phi_obs": float(phi_obs[peak]),
                "phi_null": float(mean[peak]),
                "rho_rich_peak": float(phi_obs[peak] / mean[peak]),
                "z_peak": z_peak,
                "thresholds_tested": int(np.sum(candidates & ~np.isnan(z_obs))),
                "z_max_null_95": z_crit,
                "p_max": p_max,
                "p_pointwise": float((extreme + 1) / (null_samples + 1)),
                "null_samples": null_samples,
            }
        )

    return pd.DataFrame(summary_rows)


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--samples", type=int, default=None, help="null graphs (default: test_null_samples)")
    parser.add_argument("--jobs", type=int, default=1, help="Number of parallel worker processes (default: 1)")
    parser.add_argument("--only", nargs="+", help="Run only on specified network names")
    args = parser.parse_args()
    samples = args.samples or cfg["test_null_samples"]

    net_names = args.only if args.only else NETWORKS
    print(f"Running rich-club analysis on {len(net_names)} networks with {samples} null models...")

    networks = {name: load_undirected(name) for name in net_names}
    summary = rich_club_summary(networks, null_samples=samples, seed=cfg["seed"], n_jobs=args.jobs)

    TABLES.mkdir(parents=True, exist_ok=True)
    out_csv = TABLES / "rich_club_summary.csv"
    summary.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Saved rich-club summary to {out_csv}:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
