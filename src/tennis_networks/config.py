"""Project paths and the study configuration (config/networks.json)."""

import json
import os
import random
from pathlib import Path

import numpy as np

# The repository root; override with TENNIS_NETWORKS_ROOT to run on a copy of the data elsewhere.
ROOT = Path(os.environ.get("TENNIS_NETWORKS_ROOT", Path(__file__).resolve().parents[2]))
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
NULL_MODELS = RESULTS / "null_models"
REPORT = ROOT / "report"


def load_config(path=None):
    """Read the configuration file: seed, null-model sizes and the list of networks."""
    path = Path(path) if path else ROOT / "config" / "networks.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def seed_everything(seed):
    """Seed the global generators; functions that draw random numbers also take the seed explicitly."""
    random.seed(seed)
    np.random.seed(seed)
