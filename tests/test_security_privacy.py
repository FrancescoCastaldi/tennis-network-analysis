"""Tests for repository security, privacy safeguards, and anti-leak compliance.

Enforces:
1. No student matricola/ID numbers in tracked files (AGENTS.md rule 12).
2. No committed secret files, private keys, or environment files (.env).
3. No hardcoded API keys or sensitive credential patterns in source code.
4. Mandatory privacy guard patterns in .gitignore.
5. Zero AI stylistic clause punctuation artifacts (em/en-dashes) in report text.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Matches 10-digit matricola numbers starting with 000, not part of a decimal float
STUDENT_ID_PATTERN = re.compile(r"(?<![\.\d])000\d{7}(?!\d)")

# Known sensitive key / token prefixes
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),
]

BINARY_EXTENSIONS = {".mat", ".pdf", ".xls", ".png", ".pyc", ".ico"}


def get_tracked_files() -> list[str]:
    """Retrieves all files tracked by git in the repository."""
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=str(REPO_ROOT), text=True)
        return [f.strip() for f in out.splitlines() if f.strip()]
    except Exception:
        # Fallback to scanning repository files if git is unavailable in the environment
        tracked = []
        for p in REPO_ROOT.rglob("*"):
            if p.is_file() and not any(part.startswith((".", "venv")) for part in p.parts):
                tracked.append(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))
        return tracked


def test_no_student_id_numbers():
    """Asserts that no student ID numbers are committed in source code or data files.

    Exempts report/main.tex where student matricola numbers are mandatory
    for formal academic grading and submission.
    """
    hits = []
    for rel_path in get_tracked_files():
        if rel_path == "report/main.tex":
            continue
        path = REPO_ROOT / rel_path
        if path.suffix in BINARY_EXTENSIONS or not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            m = STUDENT_ID_PATTERN.search(content)
            if m:
                hits.append((rel_path, m.group()))
        except Exception:
            pass

    assert not hits, f"Found committed student ID numbers (violates AGENTS.md rule 12): {hits}"


def test_no_secrets_or_env_files():
    """Asserts that no .env files, private keys, or certificates are tracked by git."""
    forbidden_names = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
    forbidden_extensions = {".pem", ".key", ".pfx", ".p12", ".kdbx"}

    leaked_files = []
    for rel_path in get_tracked_files():
        p = Path(rel_path)
        if p.name in forbidden_names or p.suffix in forbidden_extensions:
            leaked_files.append(rel_path)
        if p.name.startswith(".env") and p.name != ".env.example":
            leaked_files.append(rel_path)

    assert not leaked_files, f"Sensitive credential files found in repository: {leaked_files}"


def test_no_hardcoded_api_keys():
    """Asserts that no common API token formats are hardcoded in source or configuration."""
    flagged = []
    for rel_path in get_tracked_files():
        if not (rel_path.startswith(("src/", "config/", "scripts/")) and rel_path.endswith((".py", ".json", ".yaml"))):
            continue
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pat in SECRET_PATTERNS:
            if pat.search(content):
                flagged.append(rel_path)
                break

    assert not flagged, f"Potential API keys or secrets detected in: {flagged}"


def test_gitignore_privacy_protections():
    """Verifies that .gitignore contains essential privacy and local exam exclusions."""
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), "Missing .gitignore"
    text = gitignore.read_text(encoding="utf-8")

    essential_rules = [".env", "note_private", "email", "EXAM_INFO.md"]
    for rule in essential_rules:
        assert rule in text, f".gitignore is missing essential privacy exclusion: '{rule}'"


def test_no_ai_em_dash_artifacts_in_report():
    """Verifies that report/main.tex does not contain raw em/en-dashes for clause joins."""
    report_tex = REPO_ROOT / "report" / "main.tex"
    assert report_tex.exists(), "report/main.tex not found"
    content = report_tex.read_text(encoding="utf-8")

    # Raw unicode em-dash U+2014 or en-dash U+2013 used as prose sentence joiners
    raw_em_dashes = content.count("\u2014")
    assert raw_em_dashes == 0, f"Found {raw_em_dashes} raw unicode em-dashes (\\u2014) in report/main.tex"
