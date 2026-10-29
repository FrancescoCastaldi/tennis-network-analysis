# Architecture and artifact flow

The project is a local Python research pipeline. NetworkX graphs and pandas tables connect the
stages; CSV files provide the traceable boundary between analysis and the LaTeX report.
There is no application server, database service or credential-dependent runtime.

## Where to start

| Goal | Entry point |
|---|---|
| Set up the environment or rerun a stage | [Root README](../README.md#quick-start) |
| Understand the scientific model | [methodology.md](methodology.md) |
| Trace original data and cleaning rules | [data.md](data.md) |
| Reuse graph and statistical functions | [API.md](API.md) |
| Understand design choices and report ownership | [decisions.md](decisions.md) |
| Write or review a contribution | [CONTRIBUTING.md](../CONTRIBUTING.md) |

## Pipeline and artifacts

```text
data/raw/networks/*.mat       data/raw/tennisdata/<tour>/*.xls*
          | michieli                    | tennisdata
          v                             v
data/processed/michieli_*.csv  data/processed/td_*.csv and *_ranks.csv
          |                             |
          +----------+------------------+
                     | config/networks.json
                     v
  reproduce / analysis / hypotheses / structure / triads / levels / topology
                     |
                     v
             results/tables/ and related analysis outputs
                     | report_assets
                     v
             report/tables/ + report/figures/
                     | included by report/main.tex
                     v
             wordcount check + LaTeX compilation
                     |
                     v
                 report/main.pdf
```

| Stage | Responsibility and main outputs |
|---|---|
| `download` | Optional acquisition of seasonal spreadsheets and their manifest in `data/raw/tennisdata/` |
| `michieli` | Converts all four reference matrices to processed edge lists |
| `tennisdata` | Cleans played matches; builds nine comparative networks, ranking files, summaries and source-overlap checks |
| `reproduce` | Compares reference-network measures with Michieli (2018) |
| `analysis` | Computes configured network/node measures, null distributions and robustness outputs |
| `hypotheses` | H1-H4, yearly statistics and undirected null comparisons |
| `source_check` | Agreement of the two sources on loser-winner pairs and on player wins |
| `sensitivity` | H1, H3 and H4 rerun under each cleaning choice; the baseline must reproduce `hypothesis_tests.csv` |
| `structure` | HITS, discrete/continuous core-periphery and other structural comparisons |
| `topology` | Power-law fits, compactness and ranking-band homophily |
| `triads` | Network and season triad statistics, 16-class spectrum and H5 |
| `levels` | Monadic H6, dyadic H7 and mixed H8 |
| `report_assets` | Reads analysis tables and generates LaTeX tables and PDF/PNG figures |
| `wordcount` | Checks the report source against the 5,000-word limit; does not run analysis |

`config/networks.json` contains 12 specifications: the karate-club fixture, two reference
networks and nine comparative networks. The report's source-data inventory contains 13 networks
because it also catalogs the two reference matrices that are not configured for the main analysis.
Conversion, inventory and statistical analysis therefore do not have identical scopes.

## Module boundaries

- `config` owns paths, configuration loading and global seeding.
- `loaders` turns configuration entries into simple NetworkX graphs.
- `measures`, `nullmodels` and `qap` supply reusable calculations.
- `tennisdata` also exposes match preparation helpers used by the hypothesis modules.
- Executable analysis modules orchestrate these helpers and persist their outputs.
- `report_assets` is the presentation boundary. It consumes results instead of silently rerunning
  expensive hypothesis tests during a PDF build.

See the [package module index](../src/tennis_networks/README.md) for the complete module list.

## Configuration and reproducibility

The canonical seed is in [config/networks.json](../config/networks.json). Network entries select
processed files and may override null-model sample sizes. Command-line sample reductions are for
development checks, not substitutes for the frozen report calculations.

Paths default to the repository root. The optional `TENNIS_NETWORKS_ROOT` process environment
variable redirects them to another workspace and must be set before imports. An alternate
workspace needs the corresponding configuration, input data and output directories; this variable
does not download or copy data. See [config/README.md](../config/README.md).

The [raw-data tests](../tests/test_data.py) check SHA-256 digests and dataset invariants.
Randomized calculations receive explicit seeds. Parallel null sampling has deterministic worker
streams for a fixed execution mode, but is not sample-for-sample identical to sequential sampling.
Each analysis run writes `results/run_manifest.json` with the configuration hash, Git commit,
Python/platform versions, and SHA-256 fingerprints of the processed inputs. The raw p-values in
the hypothesis tables remain unchanged; each table also contains `p_value_holm` and
`significant_holm`, computed with a Holm step-down correction across the tests in that table.

## File ownership and safe reruns

- Treat `data/raw/` as immutable. Do not run the optional downloader over the committed sources
  during ordinary documentation or report work.
- Regenerate `data/processed/` through its conversion modules, not manual edits.
- Treat `results/`, `report/tables/` and `report/figures/` as generated artifacts. Change their
  producing code and rerun the matching stage when an analysis change is intended.
- Quick and single-network runs can overwrite shared result files. Use a separate workspace for
  experiments and review the Git diff before retaining generated outputs.
- Edit report prose in `report/main.tex`. Rebuilding its PDF from existing tables and figures does
  not require a full Monte Carlo analysis.

## Quality gates

The [CI workflow](../.github/workflows/ci.yml) runs Ruff lint and format checks, pytest with coverage,
and the report word-limit check. A dependent job compiles the report and uploads the PDF artifact.
Local commands and test side effects are described in [tests/README.md](../tests/README.md).
