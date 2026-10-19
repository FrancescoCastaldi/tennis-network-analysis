# Project Report

Source code, compiled output, generated tables, and vector figures for the course project report.

## Files and Directories

* `main.tex`: Master LaTeX document adhering to the official course template (A4 single column, 12 pt, 3 cm margins, <= 5,000 words).
* `main.pdf`: Locally compiled or CI-generated PDF, excluded from Git.
* `tables/`: Generated LaTeX table fragments included via `\input`:
  * `tab_networks.tex`: Inventory of four reference matrices and nine comparative networks.
  * `tab_reproduction.tex`: Replication of Michieli (2018) baseline figures.
  * `tab_global.tex`: Cohesion, distance, PageRank, and community metrics.
  * `tab_top10.tex`: Top-10 PageRank players per era and tour.
  * `tab_null.tex`: Null-model comparisons (Maslov-Sneppen edge swaps).
  * `tab_structure.tex`: Advanced structural properties (HITS, Borgatti-Everett, small-world).
  * `tab_tests.tex`: Empirical tests of hypotheses H1 to H5.
  * `tab_levels.tex`: Multi-level hypothesis tests H5 to H8.
* `figures/`: Vector PDF figures (and companion PNG files):
  * `fig_degree_ccdf.pdf`: Degree CCDF on log-log scales across networks.
  * `fig_robustness.pdf`: Targeted vs random node removal percolation curves.
  * `fig_yearly.pdf`: Annual PageRank concentration and degree centralization.
  * `fig_network_core_2007_2012.pdf`: Elite-core visualization and 16-class triad spectrum.

## Compilation and Word Count

Compile the PDF from the repository root (requires a LaTeX installation and `latexmk`):

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd report/main.tex
```

The tables and figures already present can be compiled without rerunning the statistical pipeline.
To regenerate those assets deliberately, run `python -m tennis_networks.report_assets`; never edit
them by hand.

Check the current word count and remaining budget from the repository root:

```bash
python -m tennis_networks.wordcount
```

The command exits with status 1 above the 5,000-word limit. Counts and PDF page totals change with
the report, so use the command output rather than a fixed count in this guide.
