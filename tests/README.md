# Tests

The test suite checks data integrity, the mathematics of the measures and null models, the hypothesis
tests, the generated report assets and the repository workflows.

## Running the tests

```bash
pytest                       # the whole suite
pytest -v tests/test_data.py  # one file, verbose
pytest --collect-only -q     # count the tests without running them
```

The other quality gates, from the repository root:

```bash
ruff check .
ruff format --check .
python -m tennis_networks.wordcount
```

## What each file covers

**Data and processing**

| File | Scope |
|---|---|
| `test_data.py` | SHA-256 digests of the raw files, row counts, node lists, parser invariants |
| `test_tennisdata.py` | Spreadsheet cleaning, Greenset merge, carpet filter, walkover handling |
| `test_source_check.py` | Agreement of tennis-data.co.uk with Michieli network 1 |
| `test_reproduce.py` | Replication of the published figures of Michieli (2018) |
| `test_run_analysis.py` | End-to-end checks of the analysis entry point |

**Measures and models**

| File | Scope |
|---|---|
| `test_measures.py` | Directed and undirected metrics against toy graphs and the karate-club graph |
| `test_nullmodels.py` | Degree preservation, Erdős-Rényi baseline and parallel sampling |
| `test_structure.py` | HITS, discrete and continuous core-periphery, small-world sigma |
| `test_rich_club.py` | Rich-club coefficient and the peak threshold test |
| `test_topology.py` | Power-law fits, compactness, ranking-band homophily |

**Hypotheses**

| File | Scope |
|---|---|
| `test_hypotheses.py` | Tests H1 to H4 and the permutation engines |
| `test_sensitivity.py` | Sensitivity of H1, H3 and H4 to the cleaning choices |
| `test_triads.py` | Cyclic and transitive ratios, null spectrum, H5 |
| `test_qap.py` | QAP correlation and permutation regression |
| `test_levels.py` | Multi-level tests H6, H7 and H8 |

**Report and repository workflows**

| File | Scope |
|---|---|
| `test_report_assets.py` | Generated tables and figures, headers, no NaN values |
| `test_report_numbers.py` | Each number quoted in `report/main.tex` recomputed from `results/tables/` and compared with the text |
| `test_version.py` | The package version agrees with the project metadata |
| `test_security_privacy.py` | No student IDs, credentials, `.env` files or private keys in the repository |
| `test_release.py` | Release script and tag checks |
| `test_check_pr_body.py` | Pull request body checks (`PR check` workflow) |
| `test_pr_policy.py` | Approval gate rules (`Approval gate` workflow) |
| `test_sync_sheet.py` | Parser of the pytest summary used by the sheet sync script |

`conftest.py` holds the shared fixtures.

## Side effects on generated files

`test_report_assets.py` sends the report generators to a temporary folder, so the suite should not
touch `report/tables/` or `report/figures/`. Run `git status` after the suite anyway: a changed file
there means a test is writing outside its temporary folder. Raw input files in `data/raw/` must never change.
See [architecture](../docs/architecture.md#file-ownership-and-safe-reruns) for the difference between
immutable inputs, generated outputs and report prose.
