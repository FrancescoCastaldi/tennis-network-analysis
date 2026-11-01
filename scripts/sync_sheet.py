"""Synchronize the project dashboard with the group's Google Sheet.

Usage:
    python scripts/sync_sheet.py [--sheet-id ID] [--dry-run]

Environment:
    SNA_SHEET_ID   Google Sheet ID, used when --sheet-id is not given.
    GSHEETS_CMD    Command of the gsheets CLI (default: gsheets).

This script:
1. Runs the pytest suite and reads the passed and total test counts.
2. Computes the report word count against the 5,000-word limit.
3. Writes both figures into the dashboard (Panoramica) of the Google Sheet.

Task rows in Attivita are updated by hand: a fixed row number would overwrite
whatever task holds that row after the sheet is next edited.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_TEX = REPO_ROOT / "report" / "main.tex"
DEFAULT_GSHEETS_CMD = "gsheets"


def get_word_count() -> int:
    """Computes the LaTeX report word count."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from tennis_networks.wordcount import count

    if not REPORT_TEX.exists():
        raise FileNotFoundError(f"Report file not found: {REPORT_TEX}")
    return count(REPORT_TEX.read_text(encoding="utf-8"))


def parse_pytest_summary(output: str) -> tuple[int, int]:
    """Reads (passed, total) from the summary line of a pytest run, such as '186 passed in 30s'."""
    passed_match = re.search(r"(\d+)\s+passed", output)
    failed_match = re.search(r"(\d+)\s+failed", output)
    if passed_match is None and failed_match is None:
        raise ValueError("pytest printed no passed or failed count; the test suite did not run")
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    return passed, passed + failed


def get_test_counts() -> tuple[int, int]:
    """Runs pytest in the repo and returns (passed, total)."""
    pytest_exe = REPO_ROOT / ".venv" / "Scripts" / "pytest.exe"
    cmd = [str(pytest_exe) if pytest_exe.exists() else "pytest", "-q"]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    return parse_pytest_summary(proc.stdout + proc.stderr)


def run_gsheets_command(args: list[str], dry_run: bool = False) -> str:
    """Executes a gsheets command, resolving the CLI from GSHEETS_CMD or the PATH."""
    name = os.environ.get("GSHEETS_CMD", DEFAULT_GSHEETS_CMD)
    if dry_run:
        print(f"[DRY-RUN] Would execute: {' '.join([name, *args])}")
        return "OK (dry-run)"
    executable = shutil.which(name)
    if executable is None:
        raise SystemExit(f"gsheets CLI not found: set GSHEETS_CMD to its path (looked for '{name}')")
    cmd = [executable, *args]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode != 0:
        print(f"Error running gsheets command: {proc.stderr}", file=sys.stderr)
        proc.check_returncode()
    return proc.stdout.strip()


def sync_to_sheets(sheet_id: str, words: int, passed: int, total: int, dry_run: bool = False) -> None:
    """Writes the word count (Panoramica B5) and the test status (Panoramica F5)."""
    formatted_words = f"{words:,}".replace(",", ".")
    test_str = f"{passed}/{total} Test OK"

    print(f"Syncing to Google Sheet ({sheet_id}):")
    print(f"  - Word Count: {formatted_words} (Limit: 5.000 max)")
    print(f"  - Test Suite: {test_str}")

    # The leading apostrophe keeps the word count as text, so the locale does not parse it as a date.
    run_gsheets_command(["mutate", "write", sheet_id, "Panoramica!B5", f"'{formatted_words}"], dry_run=dry_run)
    run_gsheets_command(["mutate", "write", sheet_id, "Panoramica!F5", test_str], dry_run=dry_run)
    print("Google Sheet sync completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sheet-id", default=os.environ.get("SNA_SHEET_ID"), help="Google Sheet ID")
    parser.add_argument("--dry-run", action="store_true", help="Print operations without modifying sheet")
    args = parser.parse_args()
    if not args.sheet_id:
        parser.error("give --sheet-id or set SNA_SHEET_ID")

    words = get_word_count()
    print("Running pytest to verify test suite status...")
    passed, total = get_test_counts()
    sync_to_sheets(args.sheet_id, words, passed, total, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
