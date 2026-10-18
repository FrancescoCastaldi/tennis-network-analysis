# Interactive Notebooks

Interactive walkthroughs and visual inspection pipelines for team presentations and oral exam demonstrations.

## Files

* `full_pipeline.ipynb`: Sequential, executable demonstration of the entire pipeline from raw data parsing to hypothesis testing and figure generation.
  * Features a `QUICK` switch:
    * `QUICK = True`: Executes with lightweight null-model samples (~5 iterations) in under 2 minutes for live demos.
    * `QUICK = False`: Executes full Monte Carlo simulation replicating all frozen report tables.

## Setup

Install optional notebook dependencies:

```bash
pip install -e ".[dev,notebook]"
jupyter lab notebooks/full_pipeline.ipynb
```
