# `tennis_networks` Package

Core Python package implementing the end-to-end network analysis pipeline for professional tennis match networks.

See the [Python API reference](../../docs/API.md) for parameters, return values and examples, and
[architecture guide](../../docs/architecture.md) for pipeline flow and generated-file ownership.

## Architecture and Modules

Every pipeline stage is encapsulated in a dedicated module:

| Module | Responsibility | Primary Input | Output |
|---|---|---|---|
| `config.py` | Central paths, random seed, and configuration constants | `config/networks.json` | Path objects, seed `20261115` |
| `download.py` | Downloads ATP and WTA seasonal files from tennis-data.co.uk | Remote URLs | `data/raw/tennisdata/` |
| `michieli.py` | Converts Michieli (2018) MATLAB matrices into CSV edge lists | `data/raw/networks/*.mat` | `data/processed/michieli_*.csv` |
| `tennisdata.py` | Cleans spreadsheets and constructs comparative networks | `data/raw/tennisdata/*.xlsx` | `data/processed/td_*.csv` |
| `loaders.py` | NetworkX graph loaders (directed, undirected, weighted) | `data/processed/*.csv` | `nx.DiGraph`, `nx.Graph` |
| `measures.py` | Graph metrics: density, SCC, PageRank, k-cores, modularity | Graphs | Node and summary statistics |
| `nullmodels.py` | Degree-preserving edge swaps, Erdős-Rényi baselines and optional parallel sampling | Graphs | Randomized null distributions and comparisons |
| `analysis.py` | Executes full topological and null-model suite | Graphs | `results/tables/global_measures.csv` |
| `reproduce.py` | Validates replication against Michieli (2018) | M1, M3, M4 | `results/tables/michieli_reproduction.csv` |
| `hypotheses.py` | Tests hypotheses H1 to H4 using permutation models | Comparative networks | `results/tables/hypothesis_tests.csv` |
| `structure.py` | HITS, core-periphery (Borgatti-Everett), small-world sigma | Comparative networks | `results/tables/structure_summary.csv` |
| `triads.py` | Triad census and H5 hierarchy rigidity analysis | Comparative networks | `results/tables/triads_*.csv` |
| `qap.py` | Quadratic Assignment Procedure and permutation regression | Dyadic matrices | Correlation, p-values |
| `levels.py` | Multi-level hypothesis tests (H6 monadic, H7 dyadic, H8 mixed) | Networks and profiles | `results/tables/levels_tests.csv` |
| `report_assets.py`| Compiles final LaTeX tables and vector Matplotlib figures | `results/tables/` | `report/tables/`, `report/figures/` |
| `wordcount.py` | Enforces the 5,000-word exam ceiling on LaTeX report | `report/main.tex` | Word count and remaining budget |

## Usage

Run any step as an executable module:

```bash
python -m tennis_networks.analysis
python -m tennis_networks.hypotheses --null 200
python -m tennis_networks.structure
python -m tennis_networks.triads
python -m tennis_networks.levels
python -m tennis_networks.report_assets
python -m tennis_networks.wordcount
```
