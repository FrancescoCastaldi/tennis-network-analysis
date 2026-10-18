# Project Report

Source code, compiled output, generated tables, and vector figures for the course project report.

## Files and Directories

* `main.tex`: Master LaTeX document adhering to the official course template (A4 single column, 12 pt, 3 cm margins, <= 5,000 words).
* `main.pdf`: Compiled PDF report deliverable (13 pages).
* `tables/`: Generated LaTeX table fragments included via `\input`:
  * `tab_networks.tex`: Summary of the 13 networks studied.
  * `tab_reproduction.tex`: Replication of Michieli (2018) baseline figures.
  * `tab_global.tex`: Cohesion, distance, PageRank, and community metrics.
  * `tab_top10.tex`: Top-10 PageRank players per era and tour.
  * `tab_null.tex`: Null-model comparisons (Maslov-Sneppen edge swaps).
  * `tab_structure.tex`: Advanced structural properties (HITS, Borgatti-Everett, small-world).
  * `tab_tests.tex`: Empirical tests of hypotheses H1 to H4.
  * `tab_levels.tex`: Multi-level hypothesis tests H5 to H8.
* `figures/`: Vector PDF figures (and companion PNG files):
  * `fig_degree_ccdf.pdf`: Degree CCDF on log-log scales across networks.
  * `fig_robustness.pdf`: Targeted vs random node removal percolation curves.
  * `fig_yearly.pdf`: Annual PageRank concentration and degree centralization.

## Compilation and Word Count

Compile the PDF:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Check word budget:

```bash
python -m tennis_networks.wordcount
```
*(Currently 4,039 words out of 5,000, leaving 961 words for Sections 1, 2, 6, and 7).*
