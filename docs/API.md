# Python API reference

`tennis_networks` is a research package, not a web service. Import functions from their modules;
there is no HTTP API or package-root facade. The signatures below describe the current
implementation, not a stable third-party compatibility contract.

For pipeline stages and file ownership, see [architecture.md](architecture.md). Mathematical
definitions and hypothesis design are in [methodology.md](methodology.md).

## Conventions

- Graphs are simple NetworkX `Graph` or `DiGraph` objects unless stated otherwise.
- In the directed match model, `source` is the loser, `target` is the winner and `weight` counts wins.
- Pass the seed from `config/networks.json` to stochastic functions, including APIs whose default is
  `seed=0` or `seed=None`.
- Return types below describe runtime objects; most functions do not declare type annotations.
- Graph statistics generally expect non-empty, non-degenerate inputs. Small or constant samples
  can produce `NaN`; the functions do not all perform comprehensive input validation.

## Read-only example

This uses the built-in test graph and does not regenerate study artifacts:

```python
from tennis_networks.config import load_config
from tennis_networks.loaders import load_network
from tennis_networks.measures import global_measures, node_measures

cfg = load_config()
spec = next(item for item in cfg["networks"] if item["id"] == "example_karate")
graph = load_network(spec)
summary = global_measures(graph)  # dict of network statistics
centralities = node_measures(graph, cfg["seed"])  # DataFrame indexed by node
assert summary["nodes"] == 34
```

## Configuration and graph loading

Sources: [config.py](../src/tennis_networks/config.py),
[loaders.py](../src/tennis_networks/loaders.py).

| Function | Parameters | Returns |
|---|---|---|
| `load_config(path=None)` | Optional string or `Path`; defaults to `config/networks.json` under the project root | Parsed configuration `dict` |
| `seed_everything(seed)` | Integer seed for Python's `random` and NumPy's legacy global generator | `None` |
| `load_network(spec)` | Configuration `dict` with `id`, optional `directed`, and either `file` or `builtin="karate_club"` | `nx.Graph` or `nx.DiGraph`, with `graph["id"]` set |
| `load_undirected(name)` | Processed CSV filename stem, without `.csv` | Unweighted `nx.Graph` projection |

`load_network` reads CSV or GraphML relative to `data/processed/`, collapses parallel edges and
removes self-loops. CSV weights are loaded when a `weight` column exists.

`config` exposes `ROOT`, `RAW`, `PROCESSED`, `RESULTS`, `TABLES`, `FIGURES`, `NULL_MODELS` and
`REPORT` as `Path` objects. Set the optional `TENNIS_NETWORKS_ROOT` process environment variable
**before importing the package** to use a separate workspace. No credentials or `.env` file are
needed.

## Match preparation

Source: [tennisdata.py](../src/tennis_networks/tennisdata.py).

| Function | Parameters | Returns |
|---|---|---|
| `clean_name(name)` | Name-like value | Whitespace-normalized `str` |
| `load_matches(tours=("atp", "wta"))` | Iterable of raw spreadsheet subdirectory names | `DataFrame` of matches |
| `played(matches)` | Match `DataFrame` | Filtered `DataFrame`, excluding walkovers and invalid player pairs |
| `edge_list(matches)` | Match `DataFrame` | Aggregated `DataFrame` with `source`, `target`, `weight` |
| `to_graph(matches)` | Match `DataFrame` | Weighted `nx.DiGraph` |
| `subsets(matches)` | Played matches | `dict[str, DataFrame]` for the nine comparative networks |
| `player_rank(matches)` | Matches with winner/loser ranking columns | Median-ranking `Series`, indexed by player |
| `validity_against_michieli(matches)` | Matches; requires processed Michieli network 1 | Tuple of overlap-check `DataFrame` and list of missing player names |

`load_matches` returns `tour`, `year`, `date`, `surface`, `series`, `round`, `winner`, `loser`,
`wrank`, `lrank` and `comment`. Tours are uppercase in this table; `year` is the season filename,
not necessarily the calendar year of `date`. See [data.md](data.md) for cleaning and provenance.

## Network and node measures

Source: [measures.py](../src/tennis_networks/measures.py). Here `g` is a graph and `seed` is an
integer. Individual measures decide whether to use direction and weights; an undirected
projection is not applied automatically to every function.

| Function | Additional parameters | Returns |
|---|---|---|
| `degree_centralization(g)` | None | Freeman centralization `float`, or `NaN` for fewer than three nodes |
| `giant_component(g)` | None | Copy of the largest strongly connected component if directed, otherwise largest connected component |
| `path_stats(g)` | None | `(average_shortest_path, diameter)` on that component |
| `global_measures(g)` | None | `dict` of size, cohesion, distance, degree and component statistics |
| `triad_census(g)` | None | Triad-count `dict`; empty `dict` for an undirected graph |
| `node_measures(g, seed, bc_threshold=5000, bc_k=500)` | Betweenness sampling threshold and sample size | Centrality `DataFrame`, indexed by node |
| `communities(g, seed)` | None | `(list_of_node_sets, modularity)` using Louvain |
| `top_pagerank_share(g, k=10)` | Number of leading nodes | `float` share of total weighted PageRank |
| `gini(values)` | Non-negative numeric sequence instead of `g` | Gini `float`; `NaN` for empty or zero-total input |
| `robustness_curve(g, fractions, seed, order=None)` | Removal fractions and optional targeted node order | `DataFrame` indexed by `fraction`, columns `attack`, `random` |
| `rank_band(rank)` | Rank value instead of `g` | `"top10"`, `"11-100"` or `"others"` |
| `rank_band_assortativity(g, ranks)` | Player-keyed ranking values | Attribute-assortativity `float` on an undirected projection |
| `rank_correlation(scores, ranks)` | Player-keyed scores and ranking `Series`, instead of `g` | `(Spearman_correlation, matched_player_count)` |

`node_measures` includes degree/strength columns appropriate to the graph, betweenness, closeness,
PageRank, eigenvector centrality, clustering and k-core. Failed eigenvector calculations become
`NaN`. `robustness_curve` uses weak connectivity for directed graphs and normalizes component
sizes by the initial largest component.

## Null models

Source: [nullmodels.py](../src/tennis_networks/nullmodels.py).

| Function | Parameters | Returns |
|---|---|---|
| `degree_preserving_null(g, rng, swaps_per_edge=10)` | Graph, NumPy generator, swap multiplier | Unweighted null graph preserving node labels and degree sequence |
| `erdos_renyi_null(g, rng)` | Graph and NumPy generator | Unweighted `G(n, m)` graph matching nodes, edge count and directedness |
| `null_distribution(g, statistic, samples, seed, model="configuration", n_jobs=1)` | One graph-to-number callable and sample controls | NumPy array of sampled statistic values |
| `null_statistics(g, statistics, samples, seed, model="configuration", n_jobs=1)` | Mapping of names to graph-to-number callables | `DataFrame`, one row per null graph and one column per statistic |
| `compare_dual_null_models(g, statistics, samples, seed, n_jobs=1)` | Same statistic mapping and sample controls | `DataFrame` comparing configuration and Erdős-Rényi baselines |
| `compare_to_null(observed, null_values)` | Observed scalar and numeric null sample | `dict` with `observed`, `null_mean`, `null_sd`, `z`, `p_empirical` |
| `small_world_sigma(g, samples, seed)` | Graph and configuration-null sample controls | `dict` with `C`, `L`, `C_null`, `L_null`, `sigma` |

`model` can be `"configuration"`, `"erdos_renyi"` or a callable `(graph, rng) -> graph`. Null
graphs model topology and do not preserve match weights.

`n_jobs=1` runs sequentially; `-1` uses all available CPU cores. Parallel workers require
picklable statistics and model callables, so use module-level functions rather than lambdas.
Guard parallel script entry points with `if __name__ == "__main__":` on spawn-based platforms.
Sequential and parallel execution use different RNG streams; reproducibility assumes the same
seed, inputs and execution mode.

`compare_to_null` uses a two-sided empirical p-value with the +1 correction. Empty samples yield
`NaN` statistics; a zero or undefined null standard deviation yields a `NaN` z-score.
`compare_dual_null_models` prefixes the comparison columns with `cm_` and `er_`.

## Permutation and QAP tests

Sources: [hypotheses.py](../src/tennis_networks/hypotheses.py),
[qap.py](../src/tennis_networks/qap.py).

| Function | Parameters | Returns |
|---|---|---|
| `permutation_test(a, b, statistic, n_perm, seed)` | Two match tables and a table-to-number callable | `dict`: `diff`, `perm_mean_diff`, `p_value` |
| `group_permutation_test(x, y, n_perm, seed)` | Two numeric season-value sequences | `dict`: `diff`, `p_value` |
| `paired_signflip_test(diffs, n_perm, seed)` | Paired numeric differences | `dict`: `mean_diff`, `p_value` |
| `yearly(matches, tour, years, stat)` | Match table, uppercase tour, seasons, key in `MATCH_STATS` | Per-season `Series` |
| `qap_correlation(x, y, n_perm=999, seed=0)` | Equal-size square numeric matrices with the same player ordering | `dict`: `r`, `perm_mean`, `p_value` |
| `permutation_regression(y, x, names, n_perm=999, seed=0)` | Dependent vector, predictor matrix, predictor names | List of `dict` rows: `predictor`, `beta`, `p_value`, `r2` |

QAP excludes the diagonal and permutes rows and columns together. It raises `ValueError` for
incompatible matrix dimensions. Regression standardizes variables and includes an intercept;
use finite, non-constant input columns. All these tests use two-sided empirical p-values.

## Structural models and triads

Sources: [structure.py](../src/tennis_networks/structure.py),
[triads.py](../src/tennis_networks/triads.py).

| Function | Parameters | Returns |
|---|---|---|
| `hits_scores(g)` | Weighted directed graph | `(hub_series, authority_series)` |
| `core_periphery(und)` | Undirected graph | `(core_node_set, statistics_dict)` for the discrete degree-ordered model |
| `continuous_core_periphery(und, weight=None, max_iter=500)` | Undirected graph, optional weight-attribute name, optimizer iteration limit | `(coreness_dict, fit_float)`; scores normalized to `[0, 1]` |
| `meetings_graph(g)` | Directed graph with `weight` attributes | Undirected graph with summed `meetings` edge attributes |
| `structural_equivalence(und, players)` | Meetings graph and ordered list of existing players with nonzero opponent vectors | Cosine-similarity NumPy matrix, zero diagonal |
| `cyclic_ratio(g)` | Directed graph | `030C / 030T` as `float`, or `NaN` when the denominator is zero |
| `triad_census_spectrum(g, samples=20, seed=None, n_jobs=1)` | Directed graph and configuration-null controls | `DataFrame`: `triad`, `observed`, `null_mean`, `null_sd`, `z`, `p_empirical` |
| `season_ratios(matches, tour, years)` | Match table, uppercase tour and season sequence | Per-season cyclic-ratio `Series` |

The continuous core-periphery fit constructs a dense adjacency matrix; consider its memory
cost before applying it to large graphs. It rejects directed graphs. The triad spectrum rejects
undirected graphs and covers all 16 Holland-Leinhardt triad classes.

## Executable stages

The `main()` functions in `download`, `michieli`, `tennisdata`, `reproduce`, `analysis`,
`hypotheses`, `structure`, `triads`, `levels`, `report_assets` and `wordcount` are command-line
entry points, not separate service endpoints. Run stages with `python -m tennis_networks.<module>`;
see the [pipeline command table](../README.md#quick-start) and
[artifact flow](architecture.md#pipeline-and-artifacts).

Formatting and plotting helpers in `report_assets`, and stage-specific orchestration helpers,
are implementation details. Use `python -m tennis_networks.report_assets` to regenerate all report
assets together. This overwrites generated files; quick or partial runs must not replace the
frozen report results unintentionally.

## Topology

Source: [topology.py](../src/tennis_networks/topology.py). Run `python -m tennis_networks.topology [--perm 999]`.
Directed graphs are projected on the undirected graph in which two players are linked if they ever met.

| Function | Parameters | Returns |
|---|---|---|
| `degree_fit(g)` | Graph | `dict` with `alpha`, `xmin`, `ks_distance`, `n_tail`, `tail_share`, the ratio `R_vs_*` and p-value `p_vs_*` against lognormal, exponential and truncated power law, and a `verdict` |
| `power_law_verdict(row)` | One `degree_fit` result | `"plausible"`, `"not supported (alternative fits better)"` or `"inconclusive (short tail)"` |
| `compactness(g)` | Graph | `dict` with giant-component size, `avg_distance`, `diameter`, `global_efficiency`, `distance_ratio` to ln(N) / ln(k) |
| `band_homophily(g, ranks, n_perm, seed)` | Player-keyed ranking `Series`, permutations, seed | `(summary dict, list of band-pair rows)`: observed and expected matches, ratio, z and two-sided p with the +1 correction, under a null over all players (`_all`) and within degree deciles (`_deg`) |

Players without a ranking count in the band `others`. The bands of a period use each player's median ranking in it.
