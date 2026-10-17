# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/FrancescoCastaldi/tennis-network-analysis/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/FrancescoCastaldi/tennis-network-analysis/releases/tag/v0.1.0
