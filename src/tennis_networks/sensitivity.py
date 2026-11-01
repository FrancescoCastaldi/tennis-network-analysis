"""Sensitivity of the tests on eras, surfaces and tours (H1, H3, H4) to the cleaning choices of the report.

Run (after `python -m tennis_networks.tennisdata` and `python -m tennis_networks.hypotheses`):
    python -m tennis_networks.sensitivity [--jobs n]

The report drops walkovers, keeps retirements and leaves carpet out of the surface networks. Each variant
changes one choice and reruns the tests with the same seed and the same number of permutations, so a
difference comes from the data alone. The baseline must reproduce results/tables/hypothesis_tests.csv.

Outputs:
    results/tables/sensitivity_variants.csv   matches in each variant and change against the baseline
    results/tables/sensitivity_tests.csv      difference and p-value of each test in each variant
    results/tables/sensitivity_scopes.csv     season and surface scope diagnostics
"""

import argparse
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from tennis_networks import tennisdata as td
from tennis_networks.config import TABLES, load_config
from tennis_networks.hypotheses import h1_rows, h3_rows, h4_rows, season_series

VARIANTS = {
    "baseline": "Walkovers dropped, retirements kept (the report)",
    "no_retirements": "Retirements dropped as well",
    "walkovers_kept": "Walkovers kept",
    "carpet_as_hard": "Carpet merged with hard courts",
}
RETIREMENT_PREFIXES = ("retired", "rrtired")  # the second is a typo found in the source files


def build_variants(raw):
    """The match sets of the four variants, from the raw matches of both tours."""
    base = td.played(raw)
    retired = base["comment"].str.lower().str.startswith(RETIREMENT_PREFIXES)
    return {
        "baseline": base,
        "no_retirements": base[~retired],
        "walkovers_kept": td.played(raw, keep_walkovers=True),
        "carpet_as_hard": base.assign(surface=base["surface"].replace({"Carpet": "Hard"})),
    }


def build_scope_variants(matches):
    """Return pre-specified season and surface subsets for robustness checks."""
    atp = matches[matches["tour"] == "ATP"]
    return {
        "all_matches": matches,
        "atp_2000_2006": atp[atp["year"].between(2000, 2006)],
        "atp_2007_2012": atp[atp["year"].between(2007, 2012)],
        "atp_2013_2018": atp[atp["year"].between(2013, 2018)],
        "atp_2019_2025": atp[atp["year"].between(2019, 2025)],
        "atp_clay": atp[atp["surface"] == "Clay"],
        "atp_hard": atp[atp["surface"] == "Hard"],
        "atp_grass": atp[atp["surface"] == "Grass"],
    }


def run_tests(matches, n_perm, seed):
    """H1, H3 and H4 on one set of matches, as in `hypotheses`."""
    series = season_series(matches)
    return pd.DataFrame(h1_rows(series, n_perm, seed) + h3_rows(matches, n_perm, seed) + h4_rows(series, n_perm, seed))


def _run(job):
    name, matches, n_perm, seed = job
    return name, run_tests(matches, n_perm, seed)


def same_verdict(p_values, alpha=0.05):
    """True when every p-value falls on the same side of alpha."""
    return len({p < alpha for p in p_values}) == 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--perm", type=int, default=999, help="permutations per test (as in hypotheses)")
    parser.add_argument("--jobs", type=int, default=1, help="variants run in parallel")
    parser.add_argument("--scopes", action="store_true", help="also write season and surface scope diagnostics")
    args = parser.parse_args()
    seed = load_config()["seed"]
    variants = build_variants(td.load_matches())
    jobs = [(name, m, args.perm, seed) for name, m in variants.items()]
    if args.jobs > 1:
        with ProcessPoolExecutor(args.jobs) as pool:
            results = dict(pool.map(_run, jobs))
    else:
        results = dict(map(_run, jobs))

    # The baseline must give the saved tests of H1, H3 and H4 back: otherwise a difference is not the data.
    saved = pd.read_csv(TABLES / "hypothesis_tests.csv")
    saved = saved[saved["hypothesis"].isin(["H1", "H3", "H4"])].reset_index(drop=True)
    base = results["baseline"]
    if not (np.allclose(saved["diff"], base["diff"]) and np.allclose(saved["p_value"], base["p_value"])):
        raise ValueError("the baseline variant does not reproduce results/tables/hypothesis_tests.csv")

    n_base = len(variants["baseline"])
    pd.DataFrame(
        [
            {"variant": name, "description": VARIANTS[name], "matches": len(m), "change": len(m) - n_base}
            for name, m in variants.items()
        ]
    ).to_csv(TABLES / "sensitivity_variants.csv", index=False, encoding="utf-8")

    long = pd.concat(
        [
            df.assign(variant=name)[["variant", "hypothesis", "statistic", "comparison", "diff", "p_value"]]
            for name, df in results.items()
        ],
        ignore_index=True,
    )
    long.to_csv(TABLES / "sensitivity_tests.csv", index=False, encoding="utf-8")
    if args.scopes:
        scope_rows = [
            {
                "scope": name,
                "matches": len(scope),
                "seasons": scope["year"].nunique(),
                "surfaces": ",".join(sorted(scope["surface"].dropna().unique())),
                "tours": ",".join(sorted(scope["tour"].dropna().unique())),
            }
            for name, scope in build_scope_variants(variants["baseline"]).items()
        ]
        pd.DataFrame(scope_rows).to_csv(TABLES / "sensitivity_scopes.csv", index=False, encoding="utf-8")
    print(pd.read_csv(TABLES / "sensitivity_variants.csv").to_string(index=False))
    print(long.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
