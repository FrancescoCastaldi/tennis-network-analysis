import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release", ROOT / "scripts" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

BASE = "https://github.com/owner/repo"
CHANGELOG = f"""\
# Changelog

Intro text.

## [Unreleased]

### Added

- A new test.

### Fixed

- A wrong number.

## [0.2.0] - 2026-10-18

Second release.

### Added

- Something.

## [0.1.0] - 2026-10-17

First release.

### Added

- Start.

[Unreleased]: {BASE}/compare/v0.2.0...HEAD
[0.2.0]: {BASE}/compare/v0.1.0...v0.2.0
[0.1.0]: {BASE}/releases/tag/v0.1.0
"""
PROJECT = '[project]\nname = "x"\nversion = "0.3.0"\n'
INIT = '__version__ = "0.3.0"\n'
CITATION = "cff-version: 1.2.0\nversion: 0.3.0\ndate-released: 2026-10-23\n"
SUMMARY = "The tests of the cleaning choices. They hold."


def rolled():
    return release.roll_changelog(CHANGELOG, "0.3.0", "2026-10-23", SUMMARY)


def test_roll_moves_unreleased_under_the_new_version_with_its_summary():
    text = rolled()
    assert "## [Unreleased]\n\n## [0.3.0] - 2026-10-23\n\nThe tests of the cleaning choices." in text
    found = release.sections(text)
    assert list(found) == ["Unreleased", "0.3.0", "0.2.0", "0.1.0"]
    assert found["Unreleased"] == ""
    assert release.summary_of(found["0.3.0"]) == SUMMARY
    assert [g for g, _ in release.groups_of(found["0.3.0"])] == ["Added", "Fixed"]


def test_roll_rebuilds_every_link_reference():
    lines = [line for line in rolled().splitlines() if line.startswith("[")]
    assert lines == [
        f"[Unreleased]: {BASE}/compare/v0.3.0...HEAD",
        f"[0.3.0]: {BASE}/compare/v0.2.0...v0.3.0",
        f"[0.2.0]: {BASE}/compare/v0.1.0...v0.2.0",
        f"[0.1.0]: {BASE}/releases/tag/v0.1.0",
    ]


def test_rolled_changelog_passes_the_release_check():
    assert release.problems("v0.3.0", rolled(), PROJECT, INIT, CITATION) == []


@pytest.mark.parametrize(
    ("version", "summary", "fragment"),
    [
        ("0.3", SUMMARY, "not a version"),
        ("0.2.0", SUMMARY, "already in the changelog"),
        ("0.1.5", SUMMARY, "not above"),
        ("0.3.0", "  ", "needs a summary"),
    ],
)
def test_roll_refuses_a_bad_release(version, summary, fragment):
    with pytest.raises(ValueError, match=fragment):
        release.roll_changelog(CHANGELOG, version, "2026-10-23", summary)


def test_roll_refuses_an_empty_unreleased_section():
    empty = release.roll_changelog(CHANGELOG, "0.3.0", "2026-10-23", SUMMARY)
    with pytest.raises(ValueError, match="no entries"):
        release.roll_changelog(empty, "0.4.0", "2026-10-24", SUMMARY)


def test_check_reports_version_mismatches_and_a_missing_section():
    errors = release.problems("v0.4.0", rolled(), PROJECT, INIT, CITATION)
    assert any("pyproject.toml says 0.3.0" in e for e in errors)
    assert any("CITATION.cff says 0.3.0" in e for e in errors)
    assert any("no section [0.4.0]" in e for e in errors)
    assert release.problems("0.3", rolled(), PROJECT, INIT, CITATION) == ["tag '0.3' must look like v0.3.0"]


def test_check_wants_a_summary_and_a_link_reference():
    no_summary = rolled().replace(SUMMARY + "\n\n", "")
    assert any("no summary" in e for e in release.problems("v0.3.0", no_summary, PROJECT, INIT, CITATION))
    no_link = rolled().replace(f"[0.3.0]: {BASE}/compare/v0.2.0...v0.3.0\n", "")
    assert any("link reference" in e for e in release.problems("v0.3.0", no_link, PROJECT, INIT, CITATION))


def test_bump_version_rewrites_one_line():
    assert release.bump_version(PROJECT, "0.4.0", r'^version = "[^"]+"', 'version = "{version}"').count("0.4.0") == 1
    with pytest.raises(ValueError, match="no version line"):
        release.bump_version("nothing", "0.4.0", r"^version: \S+", "version: {version}")


def test_notes_have_the_summary_groups_downloads_and_credits():
    body = release.sections(rolled())["0.3.0"]
    notes = release.render_notes(
        "0.3.0",
        body,
        "v0.2.0",
        BASE,
        words=3991,
        assets=[("report-v0.3.0.pdf", "The report", "ab" * 32)],
        contributors=["Ada Lovelace", "Alan Turing"],
    )
    assert notes.startswith(SUMMARY)
    for fragment in (
        "## What is new",
        "## Fixes",
        "| Words | 3,991 of 5,000 |",
        f"| `report-v0.3.0.pdf` | The report | `{'ab' * 32}` |",
        "sha256sum -c SHA256SUMS.txt",
        "Ada Lovelace, Alan Turing",
        f"{BASE}/compare/v0.2.0...v0.3.0",
    ):
        assert fragment in notes


def test_tag_message_starts_with_a_title_and_lists_the_changes():
    message = release.tag_message("0.3.0", release.sections(rolled())["0.3.0"])
    assert message.startswith("v0.3.0: The tests of the cleaning choices\n\n")
    assert "What is new:\n- A new test." in message
    assert message.endswith("- A wrong number.\n")


def test_the_real_files_agree_on_the_current_version():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    versions = release.versions_in(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        (ROOT / "src" / "tennis_networks" / "__init__.py").read_text(encoding="utf-8"),
        (ROOT / "CITATION.cff").read_text(encoding="utf-8"),
    )
    assert len(set(versions.values())) == 1, versions
    assert release.HEADING.search(changelog).group("name") == "Unreleased"


def test_groups_follow_the_order_of_keep_a_changelog():
    body = """Summary.

### Fixed

- b

### Added

- a

### Extra

- e
"""
    assert [g for g, _ in release.groups_of(body)] == ["Added", "Fixed", "Extra"]
