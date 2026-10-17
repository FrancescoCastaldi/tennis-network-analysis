# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Privacy guardrails in `.gitignore` for academic exam specifications and personal notes (`EXAM_INFO.md`, `STUDY_INFO.md`, `email/`, `note_private/`).
- Architectural and workflow choices document in `docs/decisions.md` explaining the upfront pipeline strategy.
- Complete draft of Section 4 (Validity and Reliability) in `report/main.tex`, covering reference paper reproduction, source consistency, model construct validity and computational reliability.
- Computed results tables for structural measures (HITS, structural equivalence, core-periphery, small-world) and triad census / H5 hypothesis tests in `results/tables/`.

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

[Unreleased]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/releases/tag/v0.1.0
