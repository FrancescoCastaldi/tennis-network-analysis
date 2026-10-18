# Configuration

Central configuration schemas governing the study's networks, computational seeds, and simulation samples.

## Files

* `networks.json`: Defines the metadata, file paths, seed, and null-model sample sizes for every network:
  * Reference networks from Michieli (2018): `michieli_1_wins`, `michieli_3_undirected`.
  * Comparative networks from tennis-data.co.uk:
    * 4 ATP eras: `td_atp_2000_2006`, `td_atp_2007_2012`, `td_atp_2013_2018`, `td_atp_2019_2025`.
    * 3 ATP surfaces: `td_atp_clay`, `td_atp_grass`, `td_atp_hard`.
    * 2 Tour comparisons: `td_atp_2007_2025`, `td_wta_2007_2025`.
  * Deterministic random seed: `20261115`.
