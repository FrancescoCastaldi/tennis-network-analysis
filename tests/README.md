# Test Suite

Automated verification suite validating data integrity, mathematical correctness, hypothesis models, and report assets.

## Test Structure

| Test File | Verification Scope |
|---|---|
| `test_data.py` | SHA-256 hashes of raw files, row counts, node lists, parser invariants |
| `test_tennisdata.py` | Spreadsheet cleaning, Greenset merge, carpet filter, walkover handling |
| `test_measures.py` | Directed/undirected metrics against known toy and karate-club graphs |
| `test_nullmodels.py` | Degree preservation, Erdős-Rényi baseline, dual comparisons and parallel sampling |
| `test_hypotheses.py` | Hypothesis testing functions H1 to H4 and permutation engines |
| `test_structure.py` | HITS, discrete and continuous core-periphery, small-world sigma |
| `test_triads.py` | Cyclic/transitive ratios, 16-class null spectrum and H5 |
| `test_qap.py` | QAP correlation and permutation regression |
| `test_levels.py` | Multi-level hypothesis tests H6, H7 and H8 |
| `test_report_assets.py` | Generated tables and figures, headers and no NaN leakage |
| `test_version.py` | Package version agrees with the project metadata |

## Running Tests

Execute the complete test suite:

```bash
pytest
```

Run with verbose output or on a specific test file:

```bash
pytest -v
pytest tests/test_data.py
```

Get the current test count without running the tests:

```bash
pytest --collect-only -q
```

Run the other repository quality gates from the repository root:

```bash
ruff check .
ruff format --check .
python -m tennis_networks.wordcount
```

## Generated-artifact side effects

`test_report_assets.py` calls report generators and rewrites some files in `report/tables/` and
`report/figures/`. Figure rendering can produce a Git diff even when the tests pass. Check
`git status` after running the suite; do not include incidental regenerated artifacts in an
unrelated documentation change.

Raw input files must remain unchanged. See [architecture.md](../docs/architecture.md#file-ownership-and-safe-reruns)
for the distinction between immutable inputs, generated outputs and report prose.
