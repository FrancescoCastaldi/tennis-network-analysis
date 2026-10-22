# Tennis Network Analysis

[![CI](https://github.com/FrancescoCastaldi/tennis-network-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/FrancescoCastaldi/tennis-network-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Structural analysis of professional tennis match networks, comparing historical eras, playing
surfaces and the men's (ATP) and women's (WTA) tours. Group project for the Network Analysis course
(Master's Degree in Computer Science, University of Bologna, A.Y. 2026/2027).

> **Research question.** How does the structure of professional tennis match networks differ across
> eras, surfaces and tours, and what do these differences reveal about competitive balance and
> dominance in the sport?

## The model

A **node** is a player. A **directed edge** goes from the loser to the winner of at least one
official main-draw singles match, **weighted** by the number of wins in the period. PageRank on this
graph rewards wins against players who themselves win often.

| Source | Networks | Use |
|---|---|---|
| Michieli (2018), arXiv:1804.08138 | M1 wins, M2 points, M3 undirected, M4 extended (1968 to 2017/18, no dates) | Historical baseline, reproduction of the paper |
| [tennis-data.co.uk](http://www.tennis-data.co.uk/) | 4 ATP eras (2000-2025), 3 ATP surfaces, ATP and WTA 2007-2025 | Comparative study, hypotheses H1-H8 |

## Main results (draft)

| Hypothesis | Test | Outcome |
|---|---|---|
| H1: prestige more concentrated in 2007-2018 (Big Three) than 2019-2025 | season permutation | not supported (p = 0.06) |
| H2: networks more disassortative than the configuration model | 200 degree-preserving nulls | rejected in the opposite direction (z = 15 to 38) |
| H3: grass is smaller and more centralized than clay and hard | match permutation, size-corrected | supported (p ≤ 0.015) |
| H4: WTA prestige less concentrated than ATP | paired sign-flip over seasons | supported for PageRank (p = 0.016) |
| H5: more rigid hierarchy (fewer cyclic triads) in 2007-2012 | season permutation of 030C/030T | supported (p = 0.020) |
| H6 (monadic): PageRank explains the ranking beyond wins | permutation regression | supported (p = 0.001) |
| H7 (dyadic): head-to-head dominance carries over between surfaces | QAP | supported (p = 0.001) |
| H8 (mixed): players with the same surface profile meet more often | QAP | supported (p = 0.001) |

Every number above is in [`results/tables/hypothesis_tests.csv`](results/tables/hypothesis_tests.csv), [`results/tables/triads_h5.csv`](results/tables/triads_h5.csv) and [`results/tables/levels_tests.csv`](results/tables/levels_tests.csv).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                             # unit tests and checks on the committed data
```

The processed networks and the results are committed, so the report can be rebuilt without
running the analysis.

**Notebook.** [`notebooks/full_pipeline.ipynb`](notebooks/full_pipeline.ipynb) runs every step below in
order and shows the main tables and figures after each one. Install the extra kernel with
`pip install -e ".[dev,notebook]"`, open the notebook on the `.venv` kernel and *Run All*. Set
`QUICK = True` for a test run in a few minutes (not for the numbers of the report).

To run everything from the raw files without the notebook:

```bash
make all                           # or the python -m commands below, one by one
```

| Step | Command | Writes |
|---|---|---|
| Download tennis-data.co.uk (optional, files are committed) | `python -m tennis_networks.download` | `data/raw/tennisdata/` |
| Convert the Michieli networks | `python -m tennis_networks.michieli` | `data/processed/michieli_*.csv` |
| Build the comparative networks | `python -m tennis_networks.tennisdata` | `data/processed/td_*.csv` |
| Reproduce the paper | `python -m tennis_networks.reproduce` | `results/tables/michieli_reproduction.csv` |
| Measures and null models | `python -m tennis_networks.analysis` | `results/` |
| Hypotheses H1-H4 | `python -m tennis_networks.hypotheses` | `results/tables/hypothesis_tests.csv` |
| Structure: HITS, equivalence, core-periphery, small-world | `python -m tennis_networks.structure` | `results/tables/structure_summary.csv` |
| Triad census and H5 | `python -m tennis_networks.triads` | `results/tables/triads_*.csv` |
| Hypotheses H6-H8 (monadic, dyadic, mixed) | `python -m tennis_networks.levels` | `results/tables/levels_tests.csv` |
| Report tables and figures | `python -m tennis_networks.report_assets` | `report/tables/`, `report/figures/` |
| Word limit | `python -m tennis_networks.wordcount` | exit code 1 above 5,000 words |

All random draws use the seed in [`config/networks.json`](config/networks.json) (`20261115`).
Most of the running time goes into the null models; `--samples` and `--null` lower it for quick checks.

## Repository layout

```text
config/networks.json     networks of the study, seed and null-model sizes
data/raw/                original files, never edited (provenance in docs/data.md)
data/processed/          CSV edge lists: source, target[, weight]
src/tennis_networks/     the Python package (one module per pipeline step)
tests/                   unit tests and data checks (pytest)
results/                 tables (CSV) and figures produced by the pipeline
report/                  LaTeX report: main.tex, generated tables/ and figures/
docs/                    data provenance, methodology and design decisions
```

## Documentation and orientation

- [Architecture and artifact flow](docs/architecture.md): where each stage reads and writes,
  configuration boundaries and safe reruns.
- [Python API reference](docs/API.md): reusable functions, parameters, return values and examples.
- [Documentation index](docs/README.md): provenance, methodology, design decisions and author briefings.
- [Test guide](tests/README.md): quality checks and generated-artifact side effects.

## Report

`report/main.tex` follows the official course template (A4, 12 pt, 3 cm margins, at most 5,000
words). Tables and figures are generated: never edit `report/tables/` or `report/figures/` by hand,
change the code and run `make report-assets`. CI builds the PDF on every push and attaches it to
the run as an artifact.

## Group project structure and report authoring

The report is co-authored by the five group members based on the three course grading pillars:

| Area | Weight | Lead | Report Sections | Status |
|---|---|---|---|---|
| Context & Problem | 20% | Shivam Kumar (Role A) | Introduction, Problem and Motivation | To be written (~950 words) |
| Datasets & Validity | 60% (part 1) | Francesco Castaldi (Role B1) | Datasets, Validity and Reliability | Drafted; pipeline and CI active |
| Measures | 60% (part 2) | Jacopo Bonifazi (Role B2) | Measures and Results (measures) | Initial technical scaffold provided |
| Hypotheses & Tests | 60% (part 3) | Gaetano Muscarello (Role B3) | Measures and Results (tests) | Initial technical scaffold provided |
| Interpretation & Critique | 20% | Paolo Fusco (Role C) | Conclusion, Critique | To be written (~950 words) |

The preliminary text in Section 5 (*Measures and Results*) is an initial technical working draft generated to summarize pipeline outputs. Roles B2 and B3 hold full editorial ownership to revise, reorganize, or condense this section as needed to balance the overall 5,000-word limit.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for roles, branches, commits and the review checklist. Work is tracked in
the private [`SNA Tennis` project](https://github.com/users/FrancescoCastaldi/projects/3).

## Authors

Jacopo Bonifazi, Francesco Castaldi, Paolo Fusco, Shivam Kumar, Gaetano Muscarello.

Code under the [MIT License](LICENSE). Datasets belong to their authors, see [docs/data.md](docs/data.md).
