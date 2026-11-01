# `tennis_networks` package

The Python package behind the pipeline. Each stage is one module that reads its inputs and writes
its outputs, so a stage can be rerun on its own.

- API reference, with parameters and return values: [docs/API.md](../../docs/API.md)
- Pipeline flow and ownership of generated files: [docs/architecture.md](../../docs/architecture.md)

## Modules

### Data

| Module | Responsibility | Input | Output |
|---|---|---|---|
| `config.py` | Paths, seed and network specifications from `config/networks.json` | `config/networks.json` | path objects, seed `20261115` |
| `download.py` | Downloads the ATP and WTA season files from tennis-data.co.uk | remote URLs | `data/raw/tennisdata/` |
| `michieli.py` | Converts the Michieli (2018) MATLAB matrices into edge lists | `data/raw/networks/*.mat` | `data/processed/michieli_*.csv` |
| `tennisdata.py` | Cleans the season spreadsheets and builds the comparative networks | `data/raw/tennisdata/*.xlsx` | `data/processed/td_*.csv` |
| `loaders.py` | Builds NetworkX graphs (directed, undirected, weighted) from the specifications | `data/processed/*.csv` | `nx.DiGraph`, `nx.Graph` |

### Measures and null models

| Module | Responsibility | Output |
|---|---|---|
| `measures.py` | Density, strongly connected components, PageRank, k-cores, modularity, robustness | node and summary statistics |
| `nullmodels.py` | Degree-preserving edge swaps and significance against them (course slide L04) | null distributions |
| `inference.py` | Shared helpers for the result tables: p-values, Holm adjustment | table columns |
| `analysis.py` | Full measure and null-model suite for every network | `results/tables/global_measures.csv`, `results/null_models/` |
| `structure.py` | HITS, Borgatti-Everett core-periphery, small-world sigma, structural equivalence | `results/tables/structure_summary.csv` |
| `rich_club.py` | Rich-club coefficient and elite closure against configuration nulls | `results/tables/rich_club_summary.csv` |
| `topology.py` | Power-law fits, compactness, ranking-band homophily with permutation nulls | `results/tables/powerlaw_fits.csv`, `compactness.csv`, `homophily_*.csv` |

### Hypotheses

| Module | Hypotheses | Output |
|---|---|---|
| `hypotheses.py` | H1 to H4: permutation tests on the comparative networks | `results/tables/hypothesis_tests.csv` |
| `triads.py` | H5: triad census and the cyclic-to-transitive ratio | `results/tables/triads_*.csv` |
| `qap.py` | Quadratic Assignment Procedure and permutation regression (library, no output of its own) | correlations and p-values |
| `levels.py` | H6 (monadic), H7 (dyadic), H8 (mixed) | `results/tables/levels_tests.csv` |
| `sensitivity.py` | Reruns H1, H3, H4 with retirements dropped, walkovers kept, carpet counted as hard | `results/tables/sensitivity_*.csv` |

### Validation and reporting

| Module | Responsibility | Output |
|---|---|---|
| `reproduce.py` | Compares the pipeline with the figures of Michieli (2018) | `results/tables/michieli_reproduction.csv` |
| `source_check.py` | Agreement of tennis-data.co.uk with Michieli network 1 | `results/tables/td_michieli_*.csv` |
| `report_assets.py` | Turns the result tables into LaTeX tables and vector figures | `report/tables/`, `report/figures/` |
| `wordcount.py` | Counts the words of the report against the 5,000-word limit | count on stdout, exit code 1 above the limit |

## Running a module

Every stage runs as a module:

```bash
python -m tennis_networks.analysis
python -m tennis_networks.hypotheses
python -m tennis_networks.levels
python -m tennis_networks.report_assets
python -m tennis_networks.wordcount
```

`python -m tennis_networks.analysis --only <id>` runs one network. The identifiers are listed in
[`config/README.md`](../../config/README.md#network-identifiers).
