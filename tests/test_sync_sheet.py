import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_sheet", ROOT / "scripts" / "sync_sheet.py")
sync_sheet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_sheet)


def test_all_passing_summary_counts_every_test():
    assert sync_sheet.parse_pytest_summary("186 passed in 30.12s") == (186, 186)


def test_failures_are_part_of_the_total():
    assert sync_sheet.parse_pytest_summary("3 failed, 183 passed in 2.00s") == (183, 186)


def test_output_without_a_summary_is_rejected_instead_of_guessed():
    with pytest.raises(ValueError):
        sync_sheet.parse_pytest_summary("ERROR: file not found")


def test_script_has_no_local_path_or_sheet_id_in_source():
    source = (ROOT / "scripts" / "sync_sheet.py").read_text(encoding="utf-8")
    assert "D:\\" not in source
    assert "1dP7wSrawDRVBZ" not in source


def test_timesheet_manifest_contains_only_verified_updates_without_hours():
    import json

    manifest = json.loads((ROOT / "config" / "timesheet_updates.json").read_text(encoding="utf-8"))
    assert manifest["sheet"] == "SNA - UNIBO"
    assert manifest["timesheet_tab"] == "Attivita"
    assert [(entry["date"], entry["activity"], entry["status"]) for entry in manifest["entries"]] == [
        ("2026-11-01", "PR #36 merged", "Done"),
        ("2026-11-01", "PR #40 merged", "Done"),
        ("2026-11-01", "PR #41 merged", "Done"),
    ]
    assert all(entry["hours"] is None for entry in manifest["entries"])
