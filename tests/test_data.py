"""Checks on the committed datasets: they must match the figures quoted in the report."""

import hashlib
import json

import pandas as pd
import pytest

from tennis_networks.config import PROCESSED, RAW, TABLES
from tennis_networks.wordcount import LIMIT, count

pytestmark = pytest.mark.data

MICHIELI_SHA256 = {
    "1_direct_wins.mat": "327b1fcd91d75251099d11e7a3479a48163c15c55eaf9ac18888efe6ce61623f",
    "2_direct_points.mat": "eb2104aa3a3097fab9dd0de8d06196748ea8ceb5cc23a190f8e18daf6aefbb4d",
    "3_undirect_unweighted.mat": "8e56e1a11d226f352c6cda500d19ff2550fc7d359847fd3a57ee9cb5f8cbb978",
    "4_extended_undirect_unweighted.mat": "071cbcc03a8e6bc6d0aa9421b0a17742b417ff3ad7bcf1c8ac5f7913132def36",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(("name", "digest"), MICHIELI_SHA256.items())
def test_michieli_raw_files_are_unchanged(name, digest):
    assert _sha256(RAW / "networks" / name) == digest


def test_tennisdata_raw_files_match_manifest():
    manifest = pd.read_csv(RAW / "tennisdata" / "manifest.csv")
    assert len(manifest) == 45
    for row in manifest.itertuples(index=False):
        assert _sha256(RAW.parent.parent / row.file) == row.sha256, row.file


def test_michieli_network_1_matches_the_paper():
    edges = pd.read_csv(PROCESSED / "michieli_1_wins.csv")
    assert len(set(edges["source"]) | set(edges["target"])) <= 4245
    assert edges["weight"].sum() == 151734


def test_tennisdata_networks_summary():
    s = pd.read_csv(TABLES / "td_networks_summary.csv").set_index("network")
    eras = [n for n in s.index if n.startswith("td_atp_20") and n != "td_atp_2007_2025"]
    assert s.loc[eras, "matches"].sum() == 68971
    assert s.loc["td_wta_2007_2025", "matches"] == 45110
    for name, row in s.iterrows():
        edges = pd.read_csv(PROCESSED / f"{name}.csv")
        assert len(edges) == row["edges"], name
        assert edges["weight"].sum() == row["matches"], name


def test_config_lists_existing_files():
    cfg = json.loads((RAW.parent.parent / "config" / "networks.json").read_text(encoding="utf-8"))
    for spec in cfg["networks"]:
        if "file" in spec:
            assert (PROCESSED / spec["file"]).exists(), spec["file"]


def test_report_is_within_the_word_limit():
    tex = (RAW.parent.parent / "report" / "main.tex").read_text(encoding="utf-8")
    assert count(tex) <= LIMIT
