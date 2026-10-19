# Configuration

`networks.json` is the canonical configuration for network selection, random seeds and sampling.

## Network identifiers

The file contains 12 specifications:

- Test fixture: `example_karate`, loaded from NetworkX.
- Reference networks: `atp_wins_direct` and `atp_matches_undirect`, loading
  `michieli_1_wins.csv` and `michieli_3_undirected.csv` respectively.
- ATP eras: `td_atp_2000_2006`, `td_atp_2007_2012`, `td_atp_2013_2018`, `td_atp_2019_2025`.
- ATP surfaces: `td_atp_clay`, `td_atp_grass`, `td_atp_hard`.
- Tour comparison: `td_atp_2007_2025`, `td_wta_2007_2025`.

Network IDs and processed filenames are different fields. Use the ID with
`python -m tennis_networks.analysis --only <id>`.

## Fields

| Field | Meaning |
|---|---|
| `seed` | Canonical random seed, currently `20261115` |
| `null_model_samples` | Default analysis null-sample count |
| `betweenness_sample_threshold`, `betweenness_sample_size` | Node-count threshold and sample size for approximate betweenness |
| `networks[].id` | Unique identifier used in results and CLI selection |
| `networks[].file` | CSV or GraphML path relative to `data/processed/` |
| `networks[].builtin` | Alternative to a file, currently `karate_club` |
| `networks[].directed`, `networks[].weighted` | Graph description; the loader reads weights when the CSV column exists |
| `networks[].ranks` | Optional CSV with `player,rank` columns |
| `networks[].null_samples`, `networks[].small_world_samples` | Per-network sample settings used by the relevant stage |

## Workspace paths

Paths are defined by `tennis_networks.config`. The optional `TENNIS_NETWORKS_ROOT` process
environment variable overrides the repository root and must be set before importing the package.
The alternate root must contain the configuration and input files required by the chosen stage.
It does not copy data or isolate a run automatically. No credentials or `.env` file are needed.

See [architecture.md](../docs/architecture.md) for output ownership and
[API.md](../docs/API.md#configuration-and-graph-loading) for the configuration loader.
