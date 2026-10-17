# Methodology

## Networks

| Id | Nodes | Edges | Period |
|---|---|---|---|
| `atp_wins_direct` (M1) | players | loser to winner, weight = wins | 1968 to Aug 2017 |
| `atp_matches_undirect` (M3) | players | met at least once | 1968 to Aug 2017 |
| `td_atp_<era>` | players | loser to winner, weight = wins | 2000-06, 2007-12, 2013-18, 2019-25 |
| `td_atp_<surface>` | players | loser to winner, weight = wins | clay, grass, hard, 2000-2025 |
| `td_atp_2007_2025`, `td_wta_2007_2025` | players | loser to winner, weight = wins | 2007-2025 |

Measures that need an undirected graph (clustering, assortativity, k-cores) use the projection in
which two players are linked if they met at least once.

## Measures

| Phenomenon | Measure | Module |
|---|---|---|
| Size, cohesion, distances | density, reciprocity, largest SCC, average distance, diameter | `measures.global_measures` |
| Degree distribution | CCDF of distinct opponents | `report_assets.figure_degree` |
| Dominance and prestige | in-strength, PageRank, top-10 PageRank share, Gini, Freeman centralization, Spearman with ranking | `measures` |
| Elite core | k-core, Louvain communities and modularity | `measures` |
| Robustness | largest component after removal by PageRank vs random | `measures.robustness_curve` |
| Mixing | degree assortativity, ranking-band homophily | `measures` |
| Significance | configuration model by degree-preserving edge swaps, z-score, empirical p-value | `nullmodels` |

## Hypotheses and tests

| | Hypothesis | Statistic | Test |
|---|---|---|---|
| H1 | Prestige more concentrated in 2007-2018 than in 2019-2025 | top-10 PageRank share, degree centralization per season | permutation of season labels (999) |
| H2 | Networks more disassortative than the configuration model | degree assortativity | 200 degree-preserving null graphs per network |
| H3 | Grass smaller and more centralized than clay and hard | degree centralization, top-10 PageRank share | permutation of match surface labels (199), size-aware |
| H4 | WTA prestige less concentrated than ATP | same as H1, paired by season | random sign flips (9,990) |

Statistics that depend on network size are never compared directly across networks of different
size: tests compare seasons of similar size, or permute matches keeping group sizes and compare the
observed difference with the mean permuted difference.
