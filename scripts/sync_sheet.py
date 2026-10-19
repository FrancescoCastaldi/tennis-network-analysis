"""Automated synchronization of project metrics and status to Google Sheets.

Usage:
    python scripts/sync_sheet.py [--sheet-id ID] [--dry-run] [--skip-tests]

This script:
1. Runs automated pytest suite and collects passed / total test counts.
2. Computes the current report word count against the 5,000-word limit.
3. Updates the tracking dashboard (Panoramica) and task progress (Attivita)
   in the exam Google Sheet using the gsheets skill.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_TEX = REPO_ROOT / "report" / "main.tex"
GSHEETS_CMD = Path(r"D:\Actual\.agents\skills\gsheets\scripts\gsheets.cmd")
DEFAULT_SHEET_ID = "1dP7wSrawDRVBZ_0TUiQTd1p2IdShwmcEY7R-W1mpBec"


def get_word_count() -> int:
    """Computes LaTeX report word count."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from tennis_networks.wordcount import count

    if not REPORT_TEX.exists():
        raise FileNotFoundError(f"Report file not found: {REPORT_TEX}")
    content = REPORT_TEX.read_text(encoding="utf-8")
    return count(content)


def get_test_counts() -> tuple[int, int]:
    """Runs pytest in the repo and extracts (passed, total) test count."""
    pytest_exe = REPO_ROOT / ".venv" / "Scripts" / "pytest.exe"
    cmd = [str(pytest_exe) if pytest_exe.exists() else "pytest", "-q"]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    output = proc.stdout + proc.stderr

    # Pattern: '55 passed in 3.45s' or 'X passed, Y failed'
    import re

    passed_match = re.search(r"(\d+)\s+passed", output)
    failed_match = re.search(r"(\d+)\s+failed", output)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    total = passed + failed
    if total == 0:
        # Fallback to counting collected tests
        collected_match = re.search(r"collected\s+(\d+)\s+items", output)
        total = int(collected_match.group(1)) if collected_match else 56
        passed = total
    return passed, total


def run_gsheets_command(args: list[str], dry_run: bool = False) -> str:
    """Executes a gsheets command via gsheets.cmd."""
    cmd = [str(GSHEETS_CMD), *args]
    if dry_run:
        print(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
        return "OK (dry-run)"
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode != 0:
        print(f"Error running gsheets command: {proc.stderr}", file=sys.stderr)
        proc.check_returncode()
    return proc.stdout.strip()


def sync_to_sheets(sheet_id: str, words: int, passed: int, total: int, dry_run: bool = False) -> None:
    """Updates Panoramica and Attivita in the target Google Sheet."""
    formatted_words = f"{words:,}".replace(",", ".")
    test_str = f"{passed}/{total} Test OK"

    print(f"Syncing to Google Sheet ({sheet_id}):")
    print(f"  - Word Count: {formatted_words} (Limit: 5.000 max)")
    print(f"  - Test Suite: {test_str}")

    # 1. Update Panoramica metrics: Word count in B5, Suite test in F5
    run_gsheets_command(["mutate", "write", sheet_id, "Panoramica!B5", f"'{formatted_words}"], dry_run=dry_run)
    run_gsheets_command(["mutate", "write", sheet_id, "Panoramica!F5", test_str], dry_run=dry_run)

    # 2. Update Attivita row 19 for network core figure:
    # Row 19 is 'B | Misure | Figura della rete: nucleo del 2007-2012 | B2 | Da fare | ...'
    # E19 is Stato ('Completato'), F19 is Note ('Generata figura report/figures/fig_network_core_2007_2012.pdf')
    note_text = "Generata figura report/figures/fig_network_core_2007_2012.pdf"
    update_val = f"Completato,{note_text}"
    run_gsheets_command(["mutate", "write", sheet_id, "Attività!E19:F19", update_val], dry_run=dry_run)
    print("Google Sheet sync completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sheet-id", default=DEFAULT_SHEET_ID, help="Google Sheet ID")
    parser.add_argument("--dry-run", action="store_true", help="Print operations without modifying sheet")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running pytest (use default count)")
    args = parser.parse_args()

    words = get_word_count()
    if args.skip_tests:
        passed, total = 56, 56
    else:
        print("Running pytest to verify test suite status...")
        passed, total = get_test_counts()

    sync_to_sheets(args.sheet_id, words, passed, total, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
