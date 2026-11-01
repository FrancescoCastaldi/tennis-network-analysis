# Configuration

`networks.json` is the single source of truth for which networks exist, how they are loaded, and the
seed and sample sizes used by the statistics.

## Network identifiers

The file lists 12 networks. The identifier is what the command line uses (`--only <id>`, `--network <id>`);
the file name is where the data lives in `data/processed/`. They are different fields.

| Group | Identifiers |
|---|---|
| Test fixture | `example_karate` (loaded from NetworkX) |
| Reference networks | `atp_wins_direct` (`michieli_1_wins.csv`), `atp_matches_undirect` (`michieli_3_undirected.csv`) |
| ATP eras | `td_atp_2000_2006`, `td_atp_2007_2012`, `td_atp_2013_2018`, `td_atp_2019_2025` |
| ATP surfaces | `td_atp_clay`, `td_atp_grass`, `td_atp_hard` |
| Tours | `td_atp_2007_2025`, `td_wta_2007_2025` |

## Fields

| Field | Meaning |
|---|---|
| `seed` | Random seed of every stochastic step, `20261115` |
| `null_model_samples` | Default number of null graphs for an analysis run |
| `test_null_samples` | Null graphs behind each significance test in the report (H2, triad ratios and spectrum). One value, so that all reported z-scores and p-values rest on the same number of draws |
| `betweenness_sample_threshold`, `betweenness_sample_size` | Node count above which betweenness is estimated on a sample, and the sample size |
| `networks[].id` | Unique identifier used in results and on the command line |
| `networks[].file` | Path of the CSV or GraphML file, relative to `data/processed/` |
| `networks[].builtin` | Use a built-in graph instead of a file (currently `karate_club`) |
| `networks[].directed`, `networks[].weighted` | Graph type. The loader reads the weight column when the CSV has one |
| `networks[].ranks` | Optional rank table with `player,rank` columns |
| `networks[].null_samples`, `networks[].small_world_samples` | Per-network sample sizes for the stages that use them |

## Changing the workspace

`tennis_networks.config` defines the paths. The optional environment variable `TENNIS_NETWORKS_ROOT`
replaces the repository root. Set it before importing the package. The new root must contain the
configuration and the input files that the stage needs. It does not copy data or isolate a run.

No credentials and no `.env` file are needed.

See [architecture](../docs/architecture.md) for which stage writes which output, and
[the configuration loader](../docs/API.md#configuration-and-graph-loading) in the API reference.
