"""Rich-club coefficient and elite closure against null models (course slide L06).

Measures whether high-degree players form tightly interconnected subgraphs
beyond degree-sequence expectations (Colizza et al. 2006, Newman 2018 §7.8).
Normalised against degree-preserving configuration null models to explain
the positive assortativity and tournament seeding constraints of Hypothesis H2.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor

import networkx as nx
import numpy as np
import pandas as pd

from tennis_networks.config import TABLES
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


def normalized_rich_club(
    g: nx.Graph,
    null_samples: int = 200,
    seed: int = 20261115,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Computes observed phi(k) and normalises against degree-preserving configuration null models."""
    g_undir = g.to_undirected() if g.is_directed() else g
    obs_rc = compute_rich_club(g_undir)

    if not obs_rc:
        return pd.DataFrame(
            columns=["k", "n_nodes", "phi_obs", "phi_null_mean", "phi_null_std", "rho_rich", "z_score", "p_value"]
        )

    ss = np.random.SeedSequence(seed)
    children = ss.spawn(null_samples)
    tasks = [(g_undir, c) for c in children]

    if n_jobs > 1:
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            null_curves = list(executor.map(_sample_null_rich_club, tasks))
    else:
        null_curves = [_sample_null_rich_club(t) for t in tasks]

    rows = []
    for k, (n_nodes, phi_obs) in sorted(obs_rc.items()):
        null_vals = np.array([nc.get(k, 0.0) for nc in null_curves], dtype=float)
        null_mean = float(np.mean(null_vals))
        null_std = float(np.std(null_vals))

        if null_mean > 0:
            rho_rich = float(phi_obs / null_mean)
            z_score = float((phi_obs - null_mean) / (null_std + 1e-12))
        else:
            rho_rich = 1.0
            z_score = 0.0

        diffs = np.abs(null_vals - null_mean)
        obs_diff = abs(phi_obs - null_mean)
        extreme_count = int(np.sum(diffs >= obs_diff - 1e-12))
        p_val = float((extreme_count + 1) / (null_samples + 1))

        rows.append(
            {
                "k": k,
                "n_nodes": n_nodes,
                "phi_obs": phi_obs,
                "phi_null_mean": null_mean,
                "phi_null_std": null_std,
                "rho_rich": rho_rich,
                "z_score": z_score,
                "p_value": p_val,
            }
        )

    return pd.DataFrame(rows)


def rich_club_summary(
    networks: dict[str, nx.Graph],
    null_samples: int = 200,
    seed: int = 20261115,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Summarises peak rich-club regime (N_{>k} >= 5) across comparative networks."""
    summary_rows = []
    for name, g in networks.items():
        df = normalized_rich_club(g, null_samples=null_samples, seed=seed, n_jobs=n_jobs)
        if df.empty:
            continue

        # Filter for meaningful elite clubs (at least 5 nodes, at most 50% of the network)
        valid = df[(df["n_nodes"] >= 5) & (df["n_nodes"] <= len(g) * 0.5) & (df["phi_null_mean"] > 0)]
        if valid.empty:
            valid = df[df["phi_null_mean"] > 0]

        if not valid.empty:
            # Pick the peak z-score regime
            best_row = valid.loc[valid["z_score"].idxmax()]
            summary_rows.append(
                {
                    "network": name,
                    "peak_k": int(best_row["k"]),
                    "elite_nodes": int(best_row["n_nodes"]),
                    "phi_obs": float(best_row["phi_obs"]),
                    "phi_null": float(best_row["phi_null_mean"]),
                    "rho_rich_peak": float(best_row["rho_rich"]),
                    "z_peak": float(best_row["z_score"]),
                    "p_value": float(best_row["p_value"]),
                }
            )

    return pd.DataFrame(summary_rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=200, help="Number of null models (default: 200)")
    parser.add_argument("--jobs", type=int, default=1, help="Number of parallel worker processes (default: 1)")
    parser.add_argument("--only", nargs="+", help="Run only on specified network names")
    args = parser.parse_args()

    net_names = args.only if args.only else NETWORKS
    print(f"Running rich-club analysis on {len(net_names)} networks with {args.samples} null models...")

    networks = {name: load_undirected(name) for name in net_names}
    summary = rich_club_summary(networks, null_samples=args.samples, seed=20261115, n_jobs=args.jobs)

    TABLES.mkdir(parents=True, exist_ok=True)
    out_csv = TABLES / "rich_club_summary.csv"
    summary.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Saved rich-club summary to {out_csv}:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
