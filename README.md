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

## At a glance

| | |
|---|---|
| Networks | 13: 4 reference networks (Michieli) and 9 comparative networks built from 114,084 played matches (68,972 ATP, 45,112 WTA) |
| Hypotheses | 8 tested: 6 supported, 1 not supported (H1), 1 rejected in the opposite direction (H2) |
| Reproducibility | one seed (`20261115`), 132 tests, CI on every push, every table and figure generated from `results/` |
| Report | `report/main.tex`, 4,014 of 5,000 words; Introduction and Problem and Motivation still to be written |
| Deadline | 27 November 2026, 23:59 (course exam session) |
| Version | 0.2.7, see the [changelog](CHANGELOG.md) |

## The model

A **node** is a player. A **directed edge** goes from the loser to the winner of at least one
official main-draw singles match, **weighted** by the number of wins in the period. PageRank on this
graph rewards wins against players who themselves win often.

| Source | Networks | Use |
|---|---|---|
| Michieli (2018), arXiv:1804.08138 | M1 wins, M2 points, M3 undirected, M4 extended (1968 to 2017/18, no dates) | Historical baseline, reproduction of the paper |
| [tennis-data.co.uk](http://www.tennis-data.co.uk/) | 4 ATP eras (2000-2025), 3 ATP surfaces, ATP and WTA 2007-2025 | Comparative study, hypotheses H1-H8 |

## Main results

Hypotheses, tested on the nine comparative networks:

| Hypothesis | Test | Outcome |
|---|---|---|
| H1: prestige more concentrated in 2007-2018 (Big Three) than 2019-2025 | season permutation | not supported (top-10 PageRank share 0.265 against 0.234, p = 0.060) |
| H2: networks more disassortative than the configuration model | 200 degree-preserving nulls | rejected in the opposite direction: observed assortativity is higher than the null in all nine networks (z = 16 to 35), as expected if seeding keeps strong players apart until the late rounds |
| H3: grass is smaller and more centralized than clay and hard | match permutation, size-corrected | supported (p = 0.005 to 0.015) |
| H4: WTA prestige less concentrated than ATP | paired sign-flip over seasons | supported for PageRank (p = 0.016), not for centralization (p = 0.17) |
| H5: more rigid hierarchy (fewer cyclic triads) in 2007-2012 | season permutation of 030C/030T | supported (cyclic ratio 0.184 against 0.211, p = 0.010) |
| H6 (monadic): PageRank explains the ranking beyond wins | permutation regression | supported (p = 0.001 in every era, wins add nothing) |
| H7 (dyadic): head-to-head dominance carries over between surfaces | QAP | supported (r = 0.12 to 0.15, p = 0.001) |
| H8 (mixed): players with the same surface profile meet more often | QAP | supported (r = 0.06, p = 0.001) |

Structure of the networks:

- All nine are sparse but compact: 62% to 70% of the players are in the giant strongly connected component and two players are 2.4 to 3.3 wins apart on average.
- None is scale-free: bracket sizes and calendars cap how many opponents a player can meet.
- A dense core of 16% to 20% of the players, almost all in the official top 100, holds most of the matches, and the rich-club coefficient shows elite closure in every network (peak 1.05 to 1.22, z = 13 to 27).

Validity of the data:

- The pipeline reproduces the figures of Michieli (2018) on M1, M3 and M4, with one exception: the average clustering of M3 is 0.311 here against 0.07 in the paper, and no standard definition gives the published value.
- tennis-data.co.uk and Michieli agree on 97.6% of the loser-winner pairs and 99.3% of the players over their common window (2000 to August 2017). For players whose whole career falls in the window, wins in the two sources correlate at r = 0.94 and 90.9% of the pairs between them have the same number of wins.
- Sensitivity to the cleaning choices (retirements dropped, walkovers kept, carpet counted as hard): every H3 and H4 verdict holds at the 5% level, while H1 is borderline (p = 0.036 without retirements, 0.053 with walkovers, 0.060 in the report). See `results/tables/sensitivity_tests.csv`.

Every number above is in [`results/tables/hypothesis_tests.csv`](results/tables/hypothesis_tests.csv), [`results/tables/triads_h5.csv`](results/tables/triads_h5.csv), [`results/tables/levels_tests.csv`](results/tables/levels_tests.csv), [`results/tables/rich_club_summary.csv`](results/tables/rich_club_summary.csv), [`results/tables/michieli_reproduction.csv`](results/tables/michieli_reproduction.csv) and [`results/tables/td_validity_michieli.csv`](results/tables/td_validity_michieli.csv).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                             # 132 unit tests and checks on the committed data
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
| Source agreement with Michieli | `python -m tennis_networks.source_check` | `results/tables/td_michieli_*.csv` |
| Sensitivity of H1, H3, H4 to the cleaning choices | `python -m tennis_networks.sensitivity` | `results/tables/sensitivity_*.csv` |
| Structure: HITS, equivalence, core-periphery, small-world | `python -m tennis_networks.structure` | `results/tables/structure_summary.csv` |
| Triad census and H5 | `python -m tennis_networks.triads` | `results/tables/triads_*.csv` |
| Rich-club coefficient and elite closure | `python -m tennis_networks.rich_club` | `results/tables/rich_club_summary.csv` |
| Degree-distribution fits, compactness, ranking-band homophily | `python -m tennis_networks.topology` | `results/tables/powerlaw_fits.csv`, `compactness.csv`, `homophily_bands.csv`, `homophily_mixing.csv` |
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
notebooks/               the full pipeline as a notebook, with outputs rendered
scripts/                 checks run by the pull request workflows
tests/                   unit tests and data checks (pytest)
results/                 tables (CSV) and figures produced by the pipeline
report/                  LaTeX report: main.tex, generated tables/ and figures/
docs/                    data provenance, methodology and design decisions
.github/                 CI, pull request template and checks, issue templates
CHANGELOG.md             changes by version (Keep a Changelog); CITATION.cff to cite the work
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
change the code and run `make report-assets`. The report has eight tables and four figures, all
generated. CI builds the PDF on every push and attaches it to the run as an artifact.

## Group project structure and report authoring

The report is co-authored by the five group members based on the three course grading pillars:

| Area | Weight | Lead | Report Sections | Status |
|---|---|---|---|---|
| Context & Problem | 20% | Shivam Kumar (Role A) | Introduction, Problem and Motivation | To be written (~950 words, briefing in `docs/`) |
| Datasets & Validity | 60% (part 1) | Francesco Castaldi (Role B1) | Datasets, Validity and Reliability | Written; pipeline, tests and CI active |
| Measures | 60% (part 2) | Jacopo Bonifazi (Role B2) | Measures and Results (measures) | Written; rich-club extension integrated |
| Hypotheses & Tests | 60% (part 3) | Gaetano Muscarello (Role B3) | Measures and Results (tests) | Written; H1 to H8 tested and in the report |
| Interpretation & Critique | 20% | Paolo Fusco (Role C) | Conclusion, Critique | Drafted; to align with the research questions of Role A |

Roles B2 and B3 hold the editorial ownership of Section 5 (*Measures and Results*) and decide how to revise or condense it within the overall 5,000-word limit. About 1,000 words remain for Role A.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for roles, branches, commits and the review checklist.

## Authors

Jacopo Bonifazi, Francesco Castaldi, Paolo Fusco, Shivam Kumar, Gaetano Muscarello.

Code under the [MIT License](LICENSE). Datasets belong to their authors, see [docs/data.md](docs/data.md).
