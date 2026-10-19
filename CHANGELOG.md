# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Continuous core-periphery model (Borgatti & Everett 1999) in `src/tennis_networks/structure.py` (`continuous_core_periphery`), maximizing Pearson correlation $\rho(A, c c^T)$ via exact analytical gradient optimization under L-BFGS-B with bounds, support for weighted graphs, input validation, and full table integration in `results/tables/structure_summary.csv` and `report/tables/tab_structure.tex`.
- 16-class Holland-Leinhardt triad census z-score spectrum against the configuration model in `src/tennis_networks/triads.py` (`triad_census_spectrum`), with empirical p-values and comprehensive test coverage in `tests/test_triads.py`.
- Dual null model comparison engine in `src/tennis_networks/nullmodels.py` (`compare_dual_null_models` and `erdos_renyi_null`), evaluating topological metrics against both degree-preserving configuration models and Erdős-Rényi $G(n, m)$ baselines, with test coverage in `tests/test_nullmodels.py`.
- Parallelization option (`n_jobs`) for Monte Carlo null model sampling across CPU cores in `src/tennis_networks/nullmodels.py` and `triads.py` via `ProcessPoolExecutor` with deterministic independent RNG streams.
- Automated Google Sheet synchronization CLI script in `scripts/sync_sheet.py` using `gsheets.cmd` to update dashboard metrics (word count 3,016, 63/63 tests passing) and task progress in spreadsheet `1dP7wSrawDRVBZ_0TUiQTd1p2IdShwmcEY7R-W1mpBec`.
- High-resolution dual-panel visualization of the 2007-2012 golden era elite core ($N=12$) and 16-class triad census z-score spectrum in `report/figures/fig_network_core_2007_2012.pdf` and `.png`, integrated into `src/tennis_networks/report_assets.py` and referenced in `report/main.tex`.

### Changed

- Polished narrative, structural rigor, and mathematical definitions in Part B (Sections 3, 4, and 5) of `report/main.tex`:
  - Formalized directed graph model $G = (V, E, W)$, in/out-strength formulas, tournament bracket constraints ($N \in \{32, 48, 64, 96, 128\}$), and seeding separation rules in Section 3.
  - Articulated construct validity, error classification (omission/commission), baseline reproduction fidelity against Michieli (2018), and clustering metric discrepancy resolution in Section 4.
  - Enhanced Section 5 with explicit PageRank formulation, domain mechanics linking negative degree assortativity in null models to tournament bracket seeding, core-periphery dynamics (both discrete $\phi$ and continuous $\rho$), and multi-level hypothesis evaluations (H1-H8).
  - Maintained word budget at exactly 3,016 words out of 5,000 (1,984 words reserved for Roles A and C) with zero AI punctuation artifacts (no em/en-dashes).

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

[Unreleased]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.3...HEAD
[0.2.3]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/releases/tag/v0.1.0
