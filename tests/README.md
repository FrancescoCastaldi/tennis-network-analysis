# Test Suite

Automated verification suite validating data integrity, mathematical correctness, hypothesis models, and report assets.

## Test Structure

| Test File | Verification Scope | Tests Count |
|---|---|---:|
| `test_data.py` | SHA-256 hashes of raw files, row counts, node lists, parser invariants | 9 |
| `test_tennisdata.py` | Spreadsheet cleaning, Greenset merge, carpet filter, walkover handling | 5 |
| `test_measures.py` | Directed/undirected metrics against known toy and karate club graphs | 7 |
| `test_nullmodels.py` | Degree preservation in edge swap randomization (Maslov-Sneppen) | 6 |
| `test_hypotheses.py` | Hypothesis testing functions H1 to H4, permutation engines | 3 |
| `test_structure.py` | HITS convergence, Borgatti-Everett fit, small-world sigma | 4 |
| `test_triads.py` | Triad census distribution (030C and 030T) and H5 permutation logic | 3 |
| `test_qap.py` | QAP correlation permutation and multiple regression correctness | 4 |
| `test_levels.py` | Multi-level hypothesis tests H6, H7, H8 execution and data outputs | 3 |
| `test_report_assets.py` | Report table generation, header integrity, no NaN leakage | 3 |

**Total**: 47 automated tests.

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
