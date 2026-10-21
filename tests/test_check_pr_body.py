import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_pr_body", ROOT / "scripts" / "check_pr_body.py")
check_pr_body = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_pr_body)

TITLE = "fix(triads): count 030C and 030T without the full census"

BODY = """\
<!-- comment that must be ignored: yes / no -->

## 1. Summary

**Why:** The triad ratios rested on 5 null graphs, so the z-scores were unstable.

**What changes:**

- One null-graph count of 200 for every significance test.

**Closes:** #7

## 2. Classification

| Field | Value |
|---|---|
| Role | B3 |
| Phase | analysis |
| Milestone | Analysis |
| Type | fix |
| Breaking for results or commands | no |

## 3. Stages touched

- [x] `config/networks.json`
- [ ] data: `download`, `michieli`, `tennisdata`
- [x] `structure`, `triads` (H5)

## 4. Effect on results

- [ ] No number in `results/`, `report/tables/` or `report/figures/` changes
- [x] Numbers change (fill the table)

| Item | Before | After | File |
|---|---|---|---|
| H5 p-value, 2007-2012 | 0.020 | 0.010 | `results/tables/triads_h5.csv` |

**Conclusion changes:** no

**Reason if yes:** N/A

**Seed unchanged (20261115):** yes

**Null graphs per significance test:** 200

## 5. Reproducibility

**Commands run:**

```bash
python -m tennis_networks.triads --jobs -1
```

**Environment:** Python 3.14.6, networkx 3.7, scipy 1.18.1

- [x] Every changed file in `results/` was produced by the stage that owns it
- [x] `data/raw/` untouched

## 6. Checks

| Check | Result |
|---|---|
| `ruff check .` | passed |
| `ruff format --check .` | passed |
| `pytest` | 77 passed |
| `python -m tennis_networks.wordcount` | 3,884 / 5,000 |
| CI on the last commit (lint, tests, PDF build) | green |

- [x] `git status` is clean after `pytest`
- [x] `CHANGELOG.md` updated under `[Unreleased]`

## 7. Report impact

**Sections affected:** Measures and Results, Critique

**Word count before and after:** 3,884 and 3,884

- [x] Every number quoted in the text matches `results/`

## 8. Credit and merge

**Authors and co-authors:** Gaetano Muscarello

## 9. Review (filled by the reviewer)

- [ ] I read the diff

Decision: approve / request changes
"""


def problems(title=TITLE, body=BODY):
    return check_pr_body.check(title, body)


def test_complete_pull_request_passes():
    assert problems() == []


def test_shipped_template_is_rejected():
    template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    errors = problems(body=template)
    assert errors
    assert any("replace the choice" in e for e in errors)


@pytest.mark.parametrize(
    "title",
    ["Update stuff", "fix: ", "feature(triads): add x", "fix(triads) count triads"],
)
def test_title_must_be_a_conventional_commit(title):
    assert any(e.startswith("Title") for e in problems(title=title))


@pytest.mark.parametrize("title", ["feat: add x", "docs(readme): update", "fix(null-models)!: change default"])
def test_valid_titles(title):
    assert not any(e.startswith("Title") for e in problems(title=title))


def test_missing_section_is_reported():
    body = BODY.replace("## 7. Report impact", "## Report impact")
    assert any("missing sections 7" in e for e in problems(body=body))


@pytest.mark.parametrize(
    ("old", "new", "fragment"),
    [
        ("**Why:** The triad ratios rested on 5 null graphs, so the z-scores were unstable.", "**Why:**", "Why"),
        ("**Closes:** #7", "**Closes:** #", "Closes"),
        ("| Role | B3 |", "| Role | A / B1 / B2 / B3 / C |", "Role"),
        ("| Phase | analysis |", "| Phase | testing |", "Phase"),
        ("**Seed unchanged (20261115):** yes", "**Seed unchanged (20261115):** yes / no", "Seed"),
        ("| `pytest` | 77 passed |", "| `pytest` | passed / total |", "pytest"),
        ("| `ruff check .` | passed |", "| `ruff check .` | failed |", "ruff check"),
        ("| green |", "| not run |", "CI on the last commit"),
        (
            "`python -m tennis_networks.wordcount` | 3,884 / 5,000",
            "`python -m tennis_networks.wordcount` | 5,400 / 5,000",
            "word count",
        ),
    ],
)
def test_incomplete_fields_are_reported(old, new, fragment):
    assert old in BODY
    errors = problems(body=BODY.replace(old, new))
    assert any(fragment in e for e in errors), errors


def test_numbers_change_needs_a_filled_table_row():
    body = BODY.replace("| H5 p-value, 2007-2012 | 0.020 | 0.010 | `results/tables/triads_h5.csv` |", "| | | | |")
    assert any("Before and After" in e for e in problems(body=body))


def test_exactly_one_result_option_is_ticked():
    body = BODY.replace("- [ ] No number", "- [x] No number")
    assert any("exactly one" in e for e in problems(body=body))


def test_unticked_check_is_reported():
    body = BODY.replace("- [x] `git status` is clean after `pytest`", "- [ ] `git status` is clean after `pytest`")
    assert any("not ticked" in e for e in problems(body=body))


def test_not_applicable_section_is_accepted():
    start = BODY.index("## 7. Report impact")
    end = BODY.index("## 8. Credit and merge")
    body = BODY[:start] + "## 7. Report impact\n\nN/A: no change to the report.\n\n" + BODY[end:]
    assert problems(body=body) == []


def test_reviewer_section_is_not_checked():
    body = BODY.replace("- [ ] I read the diff", "- [ ] I read the diff\n- [ ] Another box")
    assert problems(body=body) == []


def test_main_exit_status(tmp_path, capsys):
    ok = tmp_path / "ok.md"
    ok.write_text(BODY, encoding="utf-8")
    assert check_pr_body.main(["--title", TITLE, "--body-file", str(ok)]) == 0
    assert "PR check passed" in capsys.readouterr().out
    assert check_pr_body.main(["--title", "bad title", "--body-file", str(ok)]) == 1
