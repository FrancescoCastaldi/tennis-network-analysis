# Data

Source files and the edge lists built from them. The provenance, licences and checksums are in
[docs/data.md](../docs/data.md).

**The files in `raw/` are never edited.** `tests/test_data.py` checks their SHA-256 digests.

## `raw/`

| Path | Content |
|---|---|
| `raw/networks/1_direct_wins.mat` | Michieli (2018) M1: directed wins |
| `raw/networks/2_direct_points.mat` | Michieli (2018) M2: opponents weighted by ATP points |
| `raw/networks/3_undirect_unweighted.mat` | Michieli (2018) M3: undirected, unweighted |
| `raw/networks/4_extended_undirect_unweighted.mat` | Michieli (2018) M4: extended with Davis Cup, Challenger and Futures |
| `raw/networks/readme_michieli.docx` | Notes that came with the Michieli matrices |
| `raw/tennisdata/` | 45 season spreadsheets (`.xlsx`): 26 ATP seasons (2000 to 2025) and 19 WTA seasons (2007 to 2025) |
| `raw/tennisdata/manifest.csv` | Source URL, size and SHA-256 digest of each spreadsheet |

## `processed/`

Edge lists have the columns `source,target,weight`. The weight is the number of victories of the
target over the source, and edges run from the loser to the winner.

| File pattern | Content |
|---|---|
| `michieli_1_wins.csv`, `michieli_2_points.csv`, `michieli_3_undirected.csv`, `michieli_4_extended.csv` | The four reference networks |
| `td_atp_2000_2006.csv`, `td_atp_2007_2012.csv`, `td_atp_2013_2018.csv`, `td_atp_2019_2025.csv` | ATP eras |
| `td_atp_clay.csv`, `td_atp_grass.csv`, `td_atp_hard.csv` | ATP surfaces, 2000 to 2025 |
| `td_atp_2007_2025.csv`, `td_wta_2007_2025.csv` | ATP and WTA tours, 2007 to 2025 |
| `<network>_ranks.csv` | One row per player (`player,rank`) with the median official ranking used for the ranking tiers |
| `td_matches.csv` | The cleaned match table the comparative networks are built from |

The network identifiers and the files they load are in
[config/README.md](../config/README.md#network-identifiers).
