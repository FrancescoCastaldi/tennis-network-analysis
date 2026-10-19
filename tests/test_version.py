import tomllib
from pathlib import Path

import tennis_networks


def test_package_version_matches_project_metadata():
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project = tomllib.loads(project_file.read_text(encoding="utf-8"))
    assert tennis_networks.__version__ == project["project"]["version"]
