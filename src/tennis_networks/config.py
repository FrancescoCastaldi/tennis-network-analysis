"""Project paths and the study configuration (config/networks.json)."""

import json
import os
import platform
import random
import subprocess
import sys
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
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
RUN_MANIFEST = RESULTS / "run_manifest.json"


def load_config(path=None):
    """Read the configuration file: seed, null-model sizes and the list of networks."""
    path = Path(path) if path else ROOT / "config" / "networks.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def seed_everything(seed):
    """Seed the global generators; functions that draw random numbers also take the seed explicitly."""
    random.seed(seed)
    np.random.seed(seed)


def write_run_manifest(stage, config_path=None, input_paths=(), output_path=None, extra=None):
    """Write configuration, environment, and input fingerprints for one pipeline stage."""
    config_file = Path(config_path) if config_path else ROOT / "config" / "networks.json"
    config_bytes = config_file.read_bytes()
    inputs = []
    for path in input_paths:
        path = Path(path)
        if path.exists() and path.is_file():
            inputs.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "size": path.stat().st_size,
                    "sha256": sha256(path.read_bytes()).hexdigest(),
                }
            )
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None

    def package_version(name):
        try:
            return version(name)
        except PackageNotFoundError:
            return None

    manifest = {
        "stage": stage,
        "git_commit": commit,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {
            name: package_version(name) for name in ("networkx", "numpy", "scipy", "pandas", "matplotlib", "powerlaw")
        },
        "config": {
            "path": str(config_file.relative_to(ROOT)),
            "sha256": sha256(config_bytes).hexdigest(),
        },
        "inputs": inputs,
    }
    if extra:
        manifest["extra"] = extra
    destination = Path(output_path) if output_path else RUN_MANIFEST
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return destination
