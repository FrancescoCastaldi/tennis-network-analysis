# Reproducible pipeline. Each target can also be run as `python -m tennis_networks.<module>`.
PY ?= python
JOBS ?= 1

.PHONY: help install data networks analysis hypotheses source-check sensitivity structure triads levels reproduce report-assets report wordcount test lint all

help:  ## List the targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install the package with development tools
	$(PY) -m pip install -e ".[dev]"
	pre-commit install

data:  ## Download the tennis-data.co.uk seasons (overwrites data/raw/tennisdata)
	$(PY) -m tennis_networks.download

networks:  ## Build every processed network from data/raw
	$(PY) -m tennis_networks.michieli
	$(PY) -m tennis_networks.tennisdata

reproduce:  ## Reproduce the figures of Michieli (2018)
	$(PY) -m tennis_networks.reproduce

analysis:  ## Measures, null models and robustness for every configured network
	$(PY) -m tennis_networks.analysis

hypotheses:  ## Tests of H1-H4
	$(PY) -m tennis_networks.hypotheses

source-check:  ## Agreement of tennis-data.co.uk with Michieli network 1
	$(PY) -m tennis_networks.source_check

sensitivity:  ## H1, H3, H4 under each cleaning choice (JOBS=n runs n variants at once)
	$(PY) -m tennis_networks.sensitivity --jobs $(JOBS)

structure:  ## HITS, structural equivalence, core-periphery, small-world
	$(PY) -m tennis_networks.structure

rich-club:  ## Normalized rich-club coefficient and elite closure against null models
	$(PY) -m tennis_networks.rich_club --jobs $(JOBS)

triads:  ## Triad census and hypothesis H5 (JOBS=n to use n cores)
	$(PY) -m tennis_networks.triads --jobs $(JOBS)

levels:  ## Monadic, dyadic (QAP) and mixed hypotheses H6-H8
	$(PY) -m tennis_networks.levels

report-assets:  ## LaTeX tables and PDF figures of the report
	$(PY) -m tennis_networks.report_assets

report: report-assets  ## Build report/main.pdf (needs latexmk)
	cd report && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

wordcount:  ## Check the 5,000-word limit
	$(PY) -m tennis_networks.wordcount

test:  ## Run the test suite
	$(PY) -m pytest

lint:  ## Lint and format check
	ruff check .
	ruff format --check .

all: networks reproduce analysis hypotheses source-check sensitivity structure triads levels report  ## Everything from the raw data to the PDF
