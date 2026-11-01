# Notebooks

Walkthrough of the full pipeline, for reading, for presentations and for the oral exam.

## `full_pipeline.ipynb`

Runs the pipeline from the processed data to the hypothesis tests and the figures. Each step shows its
main table or figure. The outputs are saved in the notebook, so it can be read without running it.

The `QUICK` switch at the top controls how long the null models run:

| Setting | Use |
|---|---|
| `QUICK = True` | Short run for a live demonstration. The numbers are not the ones in the report |
| `QUICK = False` | Full run. Reproduces the tables in the report |

## Setup

```bash
pip install -e ".[dev,notebook]"
jupyter lab notebooks/full_pipeline.ipynb
```

Open the notebook on the `.venv` kernel and choose *Run All*.
