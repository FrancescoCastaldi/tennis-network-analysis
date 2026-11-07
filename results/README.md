# Results

The numbers and figures produced by the pipeline. Everything here is deterministic: the seed is
`20261115` and the configuration is in [`config/networks.json`](../config/networks.json).

Do not edit these files by hand. Change the code and rerun the stage that owns the file.

## `tables/`

**Hypothesis tests**

| File | Produced by | Content |
|---|---|---|
| `hypothesis_tests.csv` | `hypotheses` | H1, H3 and H4 permutation tests, H2 against the nulls in eight networks; raw and Holm-adjusted p-values |
| `triads_h5.csv` | `triads` | H5 test on the cyclic-to-transitive ratio |
| `levels_tests.csv` | `levels` | H6 (monadic), H7 (dyadic) and H8 (mixed) tests |
| `sensitivity_tests.csv`, `sensitivity_variants.csv` | `sensitivity` | H1, H3, H4 under each cleaning choice |

**Measures**

| File | Produced by | Content |
|---|---|---|
| `global_measures.csv` | `analysis` | Cohesion, distances, reciprocity, modularity, PageRank summaries |
| `structure_summary.csv` | `structure` | HITS, core-periphery and small-world results |
| `hits_top10.csv`, `structural_equivalence_pairs.csv` | `structure` | Top players by HITS and equivalence pairs |
| `rich_club_summary.csv` | `rich_club` | Rich-club peak and elite closure |
| `powerlaw_fits.csv`, `compactness.csv`, `homophily_bands.csv`, `homophily_mixing.csv` | `topology` | Degree fits, compactness and ranking-band homophily |
| `triads_by_season.csv`, `triads_networks.csv`, `triads_spectrum_2007_2012.csv` | `triads` | Triad census by season, network and spectrum |
| `surface_profiles.csv` | `levels` | Surface profile of each player |
| `yearly_statistics.csv`, `null_undirected.csv` | `hypotheses` | Season statistics and the undirected null summary |

**Validation against Michieli (2018)**

| File | Produced by | Content |
|---|---|---|
| `michieli_reproduction.csv` | `reproduce` | Published figures against the pipeline |
| `michieli_clustering_variants.csv` | `reproduce` | Eight definitions of average clustering for M3 |
| `td_validity_michieli.csv`, `td_michieli_pairs.csv`, `td_michieli_players.csv` | `source_check` | Cross-source agreement |
| `td_networks_summary.csv` | `tennisdata` | Size and volume of each comparative network |

**Node and robustness tables**

| Pattern | Produced by | Content |
|---|---|---|
| `<network>_nodes.csv` | `analysis` | Per-player measures (PageRank, degree, ranking) for each network |
| `<network>_robustness.csv` | `analysis` | Largest connected component after targeted and random removal |

## `figures/`

One degree plot and one robustness plot per network, as PNG (for example `td_atp_grass_degree.png`).
These are previews. The figures in the report are in `report/figures/`.

## `null_models/`

One CSV per network with the null distribution used for the z-scores and empirical p-values
(for example `td_atp_clay_null.csv`).
