# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

The tennis-data cleaning stage now merges the malformed accented spelling of a player name found in one source spreadsheet, preventing duplicate nodes and inconsistent rankings in the generated WTA network artifacts. Directed Freeman centralization is normalized by the maximum total-degree star, and its interpretation is explicit in the report. The report has also been shortened while retaining its study design, measure interpretations, results, and limitations. The main ruleset requires one review and passing CI checks without administrator bypass.

### Changed
- Report prose tightened: emphatic wording, mechanical connectives and the bulleted lists in Sections 1, 2 and 5.1 are replaced by plain sentences. The small-world index and the normalized rich-club coefficient are shown as display equations with their symbols defined.
- Bibliography in one column, in order of first citation. The triad census, the small-world index and degree assortativity now have references.
- Clarify that report hypothesis labels use raw permutation p-values, and
  soften causal language about bracket seeding and grass-court reciprocity in
  response to review feedback on report interpretation.
- Keep student matricola numbers out of the tracked files. The report reads the author block from `private/authors.tex` when that file exists, and otherwise uses a public block with names and degree programme only. The privacy check covers every tracked file again, with no exemption for `report/main.tex`.
- Enlarge analytical figures and typography (`report_assets.py`): increased plot dimensions and font hierarchy across degree CCDFs, robustness curves, yearly time-series, the 2007-2012 elite core tournament network graph, triad spectrum, and homophily heatmaps for superior visual clarity and print legibility.
- Incorporate Top-10 Leaderboards table (`tab_top10.tex`) into the report, highlighting PageRank leaders and official rankings across all four ATP eras and the WTA tour.
- Compact and humanize report prose (`report/main.tex`): streamlined text across Sections 1 to 7 into natural, fluent academic prose matching student team standards, eliminating robotic jargon and maintaining 100% compliance with course rubric criteria, with word count comfortably under 5,000 words.
- Streamline report equations and tables: retain the essential directed PageRank recurrence equation while removing textbook formula displays, weaving standard definitions into natural academic prose.
- Redesign hypothesis and null model tables (`tab_null`, `tab_tests`, `tab_levels`): replace concatenated string blobs with structured tabular columns, grouped subheadings, and clear numeric fields.
- Widen the report figures, add a rich-club comparison plot, and split the longest results paragraphs while preserving their measures and findings.

- Condense repeated background, methods, results, and conclusion text while preserving the thirteen-network design, A/B/C measure explanations, key values, limitations, and course formatting.

### Fixed
- Report numbers and ranges now match `results/tables/`: HITS and core-periphery values, degree assortativity (0.03 to 0.16), the small-world index (below 1 in the four ATP eras), the targeted-attack resilience figures and the H1, H3 and H4 sensitivity wording.
- Report: Freeman centralization is defined for both uses (directed total degree for Table 5, undirected projection for the hypothesis tests), the sign of the rank correlations is explained, and the dependent variable of H6 is named.
- Report: two claims stated as fact are now hedged (the 2020 season and bracket seeding), and the claim of identical outputs across runs is reworded to the seeded, reproducible sense.
- Remove the duplicate explicit References heading so the bibliography shows one title with consistent spacing before its two-column list.

- Normalize directed Freeman centralization by the maximum total-degree star, so reciprocal and one-way stars score 1 and 0.5 respectively. Clarify the measure in the API, methodology and report, and correct the reported network range.
- Add `analysis --centralization-only` to reproduce a corrected centralization column without rerunning expensive null models or rewriting unrelated outputs.
- Skip file fingerprinting for the configured built-in karate fixture so the analysis stage can process the full network list.
- Require passing lint and tests, report build, PR metadata and latest-review approval checks on `main`, with no bypass actors.
- Document verified post-merge timesheet updates without assigning hours or guessing external sheet rows.
- `scripts/sync_sheet.py` no longer overwrites a fixed Attivita row with a hard-coded task, and fails instead of guessing the test count when pytest prints no summary.
- Normalize the source spelling `Raducànu E.` to `Raducanu E.` before building processed match and network files.
- `report_assets`: a table shows Holm-adjusted p-values only when every result file it draws from carries them, and otherwise shows the raw values under a raw heading, so stored results from before the correction are never labelled as adjusted. Tests in `tests/test_report_assets.py`.
- Report: the Reproducibility section is shortened from 108 to about 40 words so that the report with all open pull requests stays under 5,000 words.

### Added

- Run manifests record configuration, environment, and input fingerprints for analysis runs.
- Hypothesis result tables now include Holm-adjusted p-values alongside the raw permutation values.
- End-to-end and cross-worker reproducibility checks cover the analysis entry point and null models.

- QAP regression collinearity diagnostics: predictor correlations and design-matrix condition numbers are recorded for H6, and the report qualifies the interpretation of PageRank and wins when they are not independently identified. Optional `sensitivity --scopes` diagnostics summarize season and surface subsets without changing the baseline sensitivity results.
- Horizontal project banner: SVG vector graphic (`docs/assets/banner.svg`) with glowing court geometry and network player nodes, plus AI-rendered widescreen artwork (`docs/assets/banner.png`), embedded in `README.md` alongside updated test suite (178/178) and report word count (4,425/5,000) metrics.
- Report Part A (Introduction, Problem and Motivation) from the draft by Shivam Kumar, condensed to about 355 words so that the whole report, with the open PRs, stays under the 5,000 word ceiling: the paragraphs listing H1 to H8 became one pointer to Section 5, and the prior-work and rationale paragraphs were shortened.
- AI agent configuration and rules: `.cursorrules`, `.github/copilot-instructions.md`, and updated `CLAUDE.md` and `AGENTS.md` explicitly requiring dedicated feature branches and mandatory Pull Request workflows with template compliance and metadata.

- `sensitivity` module: H1, H3 and H4 rerun with retirements dropped, walkovers kept, or carpet merged with hard courts, with the seed and permutations of `hypotheses`; the baseline must reproduce `hypothesis_tests.csv`. Outputs `results/tables/sensitivity_*.csv`, `tab_sensitivity.tex`, new paragraph and Table 3 in the report. Tests in `tests/test_sensitivity.py`.
- `source_check` module and `fig_sources`: agreement of tennis-data.co.uk with Michieli network 1 on loser-winner pairs and on the wins of players whose career lies in the common window. Tests in `tests/test_source_check.py`.
- Makefile targets `source-check` and `sensitivity`, both part of `make all`.
- Release process: `scripts/release.py` (`prepare`, `check`, `notes`, `tag`), the `Release` workflow that verifies an annotated `vX.Y.Z` tag, reruns tests and the PDF build and publishes a GitHub release with grouped notes, `report-vX.Y.Z.pdf`, `results-vX.Y.Z.tar.gz` and `SHA256SUMS.txt`, `.github/release.yml` for generated notes, Makefile targets `release-check` and `release-notes`, a Releases section in README, CONTRIBUTING and AGENTS. Tests in `tests/test_release.py`.
- GitHub project `SNA Tennis` (private, linked to the repository) with the fields `Role`, `Phase`, `Area`, `Words` and `Target` next to `Status`; `AGENTS.md`, `CONTRIBUTING.md` and `README.md` say that every PR and issue belongs to it.
- `tennis_networks.topology` (role B2): maximum-likelihood power-law fits of the degree distribution with likelihood-ratio tests against lognormal, exponential and truncated power law (package `powerlaw`, new dependency), compactness of the undirected giant component, and ranking-band homophily (top 10, 11-100, others) with 999 label permutations, over all players and among players with a similar number of opponents. Outputs `powerlaw_fits.csv`, `compactness.csv`, `homophily_bands.csv`, `homophily_mixing.csv`; `make topology`; `tests/test_topology.py`.
- `report_assets`: `tab_topology.tex`, `tab_abc.tex` (phenomenon, measure and interpretation for every family of measures) and `fig_core_homophily` (core of the 2007-2012 network and band mixing ratios).
- `report/main.tex`: Table 3 (A, B, C), Table 5 and Figure 2, a power-law test in the degree-distribution paragraph, a distance comparison with a random graph and a paragraph on ranking-band homophily; bibliography entry `clauset2009`.
- `clustering_variants` in `src/tennis_networks/reproduce.py` and `results/tables/michieli_clustering_variants.csv`: eight definitions of the average clustering of the reference network M3 (0.010 to 0.477), none of which gives the 0.07 of Michieli (2018). Test in `tests/test_reproduce.py`.
- Pre-rendered execution outputs in `notebooks/full_pipeline.ipynb` with all tables, rich-club metrics, charts, and embedded figures saved in place for instant interactive viewing directly on GitHub.
- Rich-club coefficient and elite closure analysis module in `src/tennis_networks/rich_club.py`, measuring normalized rich-club coefficients against configuration null models to explain tournament seeding constraints and Hypothesis H2 positive assortativity. Tests in `tests/test_rich_club.py` with 5 unit tests.
- Peak threshold degree $k^*$, elite club size $N_{>k^*}$, normalized coefficient $\rho_{\text{rich}}$, and peak $z$-scores integrated into `tab_structure.tex` via `src/tennis_networks/report_assets.py`.
- Makefile target `rich-club` to compute normalized rich-club profiles across all 9 comparative networks with multiprocessing support.
- Citation and theoretical discussion for Colizza et al. (2006) rich-club ordering in Section 5 of `report/main.tex`.
- Automated repository security, privacy, and anti-leak test suite in `tests/test_security_privacy.py`, verifying absence of student ID numbers (AGENTS.md rule 12), absence of `.env` files and private keys, hardcoded API tokens, mandatory `.gitignore` exclusions, and zero unescaped em-dash artifacts in LaTeX report text.
- Security audit step running `pip-audit` against the PyPA/OSV vulnerability database in `.github/workflows/ci.yml`, with `pip-audit>=2.7` added to `dev` dependencies in `pyproject.toml`.
- Pre-commit security hooks in `.pre-commit-config.yaml`: `detect-private-key`, `check-merge-conflict`, and `check-case-conflict`.
- A fixed pull request template with nine sections (summary, classification, stages touched, effect on results, reproducibility, checks, report impact, credit, review) and the `PR check` workflow: `scripts/check_pr_body.py` rejects a title that is not a Conventional Commit, unresolved choices, empty fields, unticked checks and a CI result other than green. Tests in `tests/test_check_pr_body.py`.
- `CLAUDE.md`, which imports `AGENTS.md`, and a `Pull requests` section in `AGENTS.md`: fixes go on the branch of the open PR, every PR action gets a context comment, merges are squash with CI green and an approval from another member.
- Approval policy that GitHub cannot enforce on a private repository without a paid plan: the `Approval gate` workflow shows a check `Approved by another reviewer` (an approval of the latest commit by someone other than the author, no change requested), and the `Main audit` workflow opens an issue when a commit reaches `main` without an approved PR. Both run `scripts/pr_policy.py`, tested in `tests/test_pr_policy.py`.

### Changed

- Report tightened from 19 to 17 pages (layout and two redundant tables), with the analysis unchanged: compact paragraph and section spacing, figures at 0.68 of the text width, two-column references, and smaller float separation. Every table and figure is now referenced in the text.
- READMEs across the repository rewritten for structure and layout: consistent sections, tables and contents, and facts checked against the code. Corrected stale counts (tests, report tables and figures, word count), the list of test files, the modules and the files each stage produces, and the report status.
- `scripts/sync_sheet.py` reads the sheet ID from `SNA_SHEET_ID` and the gsheets CLI from `GSHEETS_CMD`: the local Windows path and the sheet ID are no longer in the source. Its `--skip-tests` option is removed.
- Test count in the README and the report updated from 186 to 190 (the suite now includes `tests/test_sync_sheet.py`).

- Report quality: the reference list has a `References` heading, ATP and WTA are defined at first use, the Introduction ends with a roadmap of the sections, and Measures and Results is split into five subsections. No number, result or figure changes.
- Report, Area B (Datasets, Validity and Reliability, Measures and Results): hypotheses are run-in headings with one verdict line each, spelling is harmonized to British forms, claims stated more strongly than the evidence are hedged, and one duplicated word is removed. No number, test or figure changes.
- Report wording: removed stylised phrasing (rhetorical contrasts, inflated adjectives, participle tails) in favour of plain academic sentences. No number, result or claim changes.
- The submission PDF of the report, named as the exam rules require, is kept in `report/submission/` (force-added despite the ignore rule for `report/main.pdf`).
- Report layout follows the course template (`Network_Analysis_Project_Template.tex`): the template title block and section order, plain black headings, run-in paragraph headings, page numbers only. The custom title page and table of contents are removed, and the Reproducibility section is merged into Validity and Reliability. The 3 cm margins required by the course page stay, where the template uses 1 in.
- Report structure and presentation: clarified the introduction, research questions, null-model methodology and limitations; added a reproducibility section, a sober title page with headers and table of contents, and a generated H1-H8 summary table with Holm-adjusted p-values.
- `hypotheses` exposes `season_series`, `h1_rows`, `h3_rows` and `h4_rows` so that `sensitivity` reuses the same tests; `tennisdata.played` takes `keep_walkovers`. Saved results are unchanged.
- Report, Validity and Reliability: the cross-source paragraph cites the new figure, and the Tools, construct validity and Datasets prose is shortened (about 100 words) to make room for the sensitivity paragraph.
- `README.md` brought up to date: an At a glance table, final results of H1 to H8 with their numbers (H5 p = 0.010, H2 z = 16 to 35), network structure, rich-club and data validity, the rich-club step in the pipeline table, the layout and the status of each report section.
- `AGENTS.md` and `CONTRIBUTING.md`: every PR must carry labels (role, phase, type), an assignee, a milestone, reviewers from the other group B members and a complete description when it is opened. `scripts/check_pr_body.py` now checks the labels, the assignee and the milestone (and that they agree with the Classification table), and the `PR check` workflow also runs on `labeled`, `assigned` and `milestoned` events. Tests in `tests/test_check_pr_body.py`.
- One null-graph count for every significance test in the report: `test_null_samples` in `config/networks.json` (200) is now the default of `hypotheses` (H2) and `triads` (triad ratios and the triad spectrum, which used 20 by default and 5 and 15 in the saved results). `make triads JOBS=n` runs the triad null graphs on n cores.
- Results regenerated with 200 null graphs per test and the report numbers updated: H5 p = 0.010 (was 0.020 from an older run) and 0.100 for the tours, triad-ratio z from -7.0 to -36.7, null-model and small-world ranges in Section 5, and H5 in the Critique.

### Performance

- `triads.cyclic_ratio` counts the 030C and 030T triads directly from the asymmetric triangles instead of running the full 16-class census, with identical counts and about 45 times faster (0.15 s against 6.8 s on the hard-court network). This makes 200 null graphs per network practical.

### Fixed

- `rich_club`: the peak threshold k* is chosen among 88 to 282 candidates per network, so its pointwise p-value did not account for the choice. The summary now adds a max-statistic test (largest z of each null graph over the same thresholds, one-sided, +1 correction): new columns `thresholds_tested`, `z_max_null_95`, `p_max`, `p_pointwise` and `null_samples`. Seed and null graphs are read from `config/networks.json`; the null sd uses ddof=1 like the rest of the package (peak z changes by at most 0.07). Every network keeps p = 0.005 (z 13.0 to 27.3 against 95% null maxima of 2.8 to 3.1). New row in `tab_structure.tex`; report text updated.
- Report, Section 5 (role B3): H1 notes that the shortened 2020 season raises the 2019-2025 mean; H3 says grass is more centralized than its size implies, not in absolute terms; H5 separates the comparison with random outcomes (0.333) from the configuration model and reads the triad spectrum correctly (030T is also below the null); H6 states standardised coefficients, 999 permutations and the collinearity of PageRank and wins; p-values 0.757 (H1) and 0.167 (H4) rounded correctly; the null-model test covers eight networks, not nine.
- Report, Section 5: the seeding explanation of the positive assortativity and of the rich-club closure is presented as plausible but untested, in line with the Critique (the configuration model has no bracket rules).
- Report, Datasets and Validity sections: the test count (47) is now 129, the unsourced reason for the end of ATP carpet in 2009 is removed, the clustering discrepancy with Michieli (2018) cites the eight definitions tried instead of a guess about the original scripts, and the PageRank top ten is described as the same set with the first five in the same order.
- Report typography: page ranges and year ranges in the Conclusion, the Critique and the bibliography use a single hyphen like the rest of the text.
- Redacted student ID number from author metadata in `report/main.tex` to strictly uphold AGENTS.md rule 12 and academic privacy before final delivery.
- `nullmodels.null_statistics` and `triads.triad_census_spectrum` give the same result for any `n_jobs`: every null graph now draws from its own child of the configuration seed, in serial runs too (serial and parallel runs used different random streams).
- The `triads` docstring said the directed null model keeps each player's wins and losses; it keeps the number of distinct opponents beaten and lost to.
- `tests/test_report_assets.py` writes the generated tables and figures to a temporary folder: running `pytest` no longer rewrites `report/figures/fig_network_core_2007_2012.*` and the committed copy is the one from the analysis run.
- `run_analysis.py` null models now reuse `tennis_networks.nullmodels`: no 15,000-swap cap (large networks were barely randomised), two-sided p-values with the +1 correction (they could be 0), each null graph generated once for all metrics, and statistics computed on the undirected projection used in the report. Density is no longer tested, since edge swaps keep it constant.
- `run_analysis.py` measures now match the report: betweenness ignores weights (wins were read as distances), core-periphery uses the Borgatti-Everett model of `structure.core_periphery` (was the top 20% by degree, now saved to `core_periphery.csv`), and small-world sigma uses `nullmodels.small_world_sigma` against the configuration model (was an analytical Erdos-Renyi baseline). Sampled distances leave out the distance of each source to itself and are flagged in `paths_sampled`; closeness is exact or skipped, never ranked on a random sample. Failed measures are reported as NaN with a warning instead of 0.

### Removed

- Report: the unreferenced H1-H8 summary table (its data is in the detailed test tables) and the top-10 PageRank table (the leaders are named in the text), to shorten the report. No test or result changes.
- `run_analysis.py` no longer writes `hypotheses_results.csv`: its placeholder marked H5 as supported without a test and measured H1 on the wrong statistic. H1-H8 come from `make hypotheses triads levels`.
- Unused loaders for `.mat` and `.edgelist` files, Michieli network 2 (symmetric weights, no winner) and the global NumPy seed in `run_analysis.py`; messages and comments are now in English.

## [0.2.7] - 2026-10-19

### Added

- Comprehensive CLI interface with `argparse` in `run_analysis.py`, adding flags for `--quick` smoke-test mode, `--network` single-target execution, custom sample counts (`--num-samples`, `--nswaps-factor`), `--skip-null`, and customizable output destination (`--output-dir`).
- Automated regression test suite in `tests/test_run_analysis.py` verifying CLI argument parsing, synthetic graph null model validation, and end-to-end smoke pipeline execution.

### Fixed

- Resolved computational bottleneck in `run_analysis.py` by bounding Monte Carlo edge swaps to scalable thresholds and implementing sampled betweenness and path lengths for networks exceeding 1,500 nodes.
- Anchored data paths and output directories to repository root `Path(__file__).resolve().parent`.
- Added `output/` to `.gitignore` to prevent generated analysis artifacts from polluting working tree status.

## [0.2.6] - 2026-10-19

### Fixed

- Sanitized and formatted `run_analysis.py` to satisfy Ruff linting and formatting rules (`SIM108`, `F841`, `W291`, `W293`, `E501`), resolving CI workflow failure in GitHub Actions.
- Synchronized package release version metadata to 0.2.6 across `pyproject.toml`, `CITATION.cff`, and `tennis_networks.__init__`.

## [0.2.5] - 2026-10-19

### Added

- Python API reference with function contracts and a read-only example, plus an architecture guide covering pipeline stages, artifact ownership and safe reruns.
- Continuous core-periphery model (Borgatti & Everett 1999) in `src/tennis_networks/structure.py` (`continuous_core_periphery`), maximizing Pearson correlation $\rho(A, c c^T)$ via exact analytical gradient optimization under L-BFGS-B with bounds, support for weighted graphs, input validation, and full table integration in `results/tables/structure_summary.csv` and `report/tables/tab_structure.tex`.
- 16-class Holland-Leinhardt triad census z-score spectrum against the configuration model in `src/tennis_networks/triads.py` (`triad_census_spectrum`), with empirical p-values and comprehensive test coverage in `tests/test_triads.py`.
- Dual null model comparison engine in `src/tennis_networks/nullmodels.py` (`compare_dual_null_models` and `erdos_renyi_null`), evaluating topological metrics against both degree-preserving configuration models and Erdős-Rényi $G(n, m)$ baselines, with test coverage in `tests/test_nullmodels.py`.
- Parallelization option (`n_jobs`) for Monte Carlo null model sampling across CPU cores in `src/tennis_networks/nullmodels.py` and `triads.py` via `ProcessPoolExecutor` with deterministic independent RNG streams.
- Automated Google Sheet synchronization CLI script in `scripts/sync_sheet.py` using `gsheets.cmd` to update dashboard metrics (word count 3,016, 63/63 tests passing) and task progress in spreadsheet `1dP7wSrawDRVBZ_0TUiQTd1p2IdShwmcEY7R-W1mpBec`.
- High-resolution dual-panel visualization of the 2007-2012 golden era elite core ($N=12$) and 16-class triad census z-score spectrum in `report/figures/fig_network_core_2007_2012.pdf` and `.png`, integrated into `src/tennis_networks/report_assets.py` and referenced in `report/main.tex`.

### Changed

- Linked the new guides from the README, documentation index and package guide; aligned configuration IDs and methodology with the implemented helpers.
- Replaced stale fixed test and word counts with live-check commands, documented report-test side effects, refreshed the report asset index and corrected release comparison links.
- Polished narrative, structural rigor, and mathematical definitions in Part B (Sections 3, 4, and 5) of `report/main.tex`:
  - Formalized directed graph model $G = (V, E, W)$, in/out-strength formulas, tournament bracket constraints ($N \in \{32, 48, 64, 96, 128\}$), and seeding separation rules in Section 3.
  - Articulated construct validity, error classification (omission/commission), baseline reproduction fidelity against Michieli (2018), and clustering metric discrepancy resolution in Section 4.
  - Enhanced Section 5 with explicit PageRank formulation, domain mechanics linking negative degree assortativity in null models to tournament bracket seeding, core-periphery dynamics (both discrete $\phi$ and continuous $\rho$), and multi-level hypothesis evaluations (H1-H8).
  - Maintained word budget at exactly 3,016 words out of 5,000 (1,984 words reserved for Roles A and C) with zero AI punctuation artifacts (no em/en-dashes).

### Fixed

- Aligned `tennis_networks.__version__` with the project metadata and added a regression test to detect future drift.

## [0.2.4] - 2026-10-18

### Changed

- Condensed Section 5 (*Measures and Results*) in `report/main.tex` from 2,599 words down to 1,355 words, preserving all 8 tables, 3 figures, statistical test values, and formulas, recovering 1,244 words of margin (total report at 2,795 words out of 5,000).
- Fine-tuned LaTeX typography and phrasing in Section 5, eliminating all overfull and underfull box warnings in body text.

### Added

- Author briefing guide for Shivam Kumar (Role A) in `docs/briefing_role_a.md` detailing theoretical foundations, literature benchmarks (Radicchi 2011, Michieli 2018), 3 research questions, and the multi-level hypothesis architecture (~950 words target across Sections 1 and 2).
- Author briefing guide for Paolo Fusco (Role C) in `docs/briefing_role_c.md` detailing empirical synthesis of findings and critical limitations (~950 words target across Sections 6 and 7).
- Updated `docs/README.md` index referencing the new role briefing guides.

## [0.2.3] - 2026-10-18

### Documentation

- Added comprehensive `README.md` documentation files across all repository folders (`src/`, `src/tennis_networks/`, `tests/`, `config/`, `data/`, `docs/`, `notebooks/`, `report/`, `results/`), describing folder purposes, contents, schemas, and execution commands.

## [0.2.2] - 2026-10-18

### Documentation

- Formalized collaborative team authoring and section ownership in `docs/decisions.md` (§5), `CONTRIBUTING.md`, and `README.md`, reflecting the official 20/60/20 grading pillars.
- Added explicit LaTeX comment blocks in `report/main.tex` identifying section lead authors and clarifying that Section 5 (*Measures and Results*) serves as an initial technical working scaffold owned by Roles B2 (Jacopo Bonifazi) and B3 (Gaetano Muscarello).

## [0.2.1] - 2026-10-18

### Added

- Privacy guardrails in `.gitignore` for academic exam specifications and personal notes (`EXAM_INFO.md`, `STUDY_INFO.md`, `email/`, `note_private/`).
- Architectural and workflow choices document in `docs/decisions.md` explaining the upfront pipeline strategy.
- Complete draft of Section 4 (Validity and Reliability) in `report/main.tex`, covering reference paper reproduction, source consistency, model construct validity and computational reliability.
- Computed results tables for structural measures (HITS, structural equivalence, core-periphery, small-world) and triad census / H5 hypothesis tests in `results/tables/`.
- LaTeX report integration in Section 5 (Measures and Results) of multi-level hypotheses (H5-H8) and structural properties with custom table generation (`tab_structure.tex`, `tab_levels.tex`).
- Dedicated unit test module `tests/test_report_assets.py` bringing the test suite to 47 passing tests.
- LaTeX float queue optimizations and column formatting eliminating underfull/overfull box warnings.

## [0.2.0] - 2026-10-18

### Added

- `structure` module: HITS hubs and authorities, structural equivalence with a QAP test against
  ranking gaps, Borgatti-Everett core-periphery compared with the k-core, small-world sigma on the
  nine comparative networks.
- `triads` module: ratio of cyclic to transitive triads against the directed configuration model,
  per-season series and hypothesis H5 (more rigid hierarchy in 2007-2012).
- `levels` module: hypotheses at the monadic (H6, permutation regression), dyadic (H7, QAP between
  surfaces) and mixed (H8, QAP on surface profiles) levels of course slide L04.
- `qap` module: QAP correlation and permutation regression, with unit tests.
- `notebooks/full_pipeline.ipynb`: the whole pipeline in one notebook, with a quick test mode;
  `notebook` optional dependencies and an nbstripout pre-commit hook.

## [0.1.0] - 2026-10-17

### Added

- `tennis_networks` package with one module per pipeline step: `download`, `michieli`, `tennisdata`,
  `reproduce`, `analysis`, `hypotheses`, `report_assets`, `wordcount`.
- Michieli (2018) networks converted from MATLAB, including the player names stored as a MATLAB
  string object; reproduction of the figures of the paper.
- Nine comparative networks from tennis-data.co.uk (ATP eras, ATP surfaces, ATP and WTA 2007-2025)
  with a consistency check against Michieli network 1.
- Node and network measures, degree-preserving null models, robustness curves.
- Tests of hypotheses H1-H4 and undirected clustering and transitivity against the same null graphs.
- Report draft with the Datasets and Measures and Results sections, generated tables and figures.
- Unit tests, data integrity checks (SHA-256 of raw files, edge and match counts), CI with lint,
  tests, word limit and PDF build.
- Contributing guide, issue and pull request templates, data provenance and methodology notes.

[Unreleased]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.5...HEAD
[0.2.5]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/releases/tag/v0.1.0
