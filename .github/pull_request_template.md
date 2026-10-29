<!--
Fill every section. Write "N/A" with a reason instead of deleting a section.
Keep the bold labels: the PR check reads them.
The title must be a Conventional Commit, it becomes the squash commit.
Example: fix(triads): count 030C and 030T without the full census
Replace each choice such as "yes / no" with one value.
-->

## 1. Summary

**Why:**

**What changes:**

-

**Closes:** #

## 2. Classification

| Field | Value |
|---|---|
| Role | A / B1 / B2 / B3 / C |
| Phase | setup / analysis / writing / delivery |
| Milestone | Setup / Analysis / Writing / Delivery |
| Type | feat / fix / perf / refactor / test / docs / report / chore / ci / build / style |
| Breaking for results or commands | yes / no |

## 3. Stages touched

- [ ] `config/networks.json`
- [ ] data: `download`, `michieli`, `tennisdata`
- [ ] `analysis`, `nullmodels`, `measures`
- [ ] `hypotheses` (H1 to H4)
- [ ] `structure`, `triads` (H5)
- [ ] `levels`, `qap` (H6 to H8)
- [ ] `report_assets`
- [ ] `report/main.tex`
- [ ] tests
- [ ] documentation
- [ ] CI or tooling

## 4. Effect on results

- [ ] No number in `results/`, `report/tables/` or `report/figures/` changes
- [ ] Numbers change (fill the table)

| Item | Before | After | File |
|---|---|---|---|
| | | | |

**Conclusion changes:** yes / no

**Reason if yes:**

**Seed unchanged (20261115):** yes / no

**Null graphs per significance test:**

## 5. Reproducibility

**Commands run:**

```bash

```

**Environment:**

- [ ] Every changed file in `results/`, `report/tables/` and `report/figures/` was produced by the stage that owns it, never edited by hand
- [ ] `data/raw/` untouched
- [ ] Rerunning the stage gives the same numbers (serial and parallel where it applies)
- [ ] Differences in files I did not intend to change were checked and are floating point or rendering noise

## 6. Checks

| Check | Result |
|---|---|
| `ruff check .` | passed / failed |
| `ruff format --check .` | passed / failed |
| `pytest` | passed / total |
| `python -m tennis_networks.wordcount` | words / 5,000 |
| CI on the last commit (lint, tests, PDF build) | green / red / not run |

- [ ] `git status` is clean after `pytest` (tests do not rewrite `report/`)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`, in `Added`, `Changed`, `Fixed` or `Removed`
- [ ] README, `docs/` or `config/README.md` updated if a command, option, output or default changed
- [ ] The linked issue and `SNA Tennis` project item have the current role, phase, status and outputs
- [ ] If progress or metrics changed, the matching `SNA - UNIBO` spreadsheet row was updated, or the issue explains why it was not
- [ ] English only, no em dash, en dash or double hyphen between sentences
- [ ] No student ID, email, private note or local file path in files, logs or comments

## 7. Report impact

**Sections affected:**

**Word count before and after:**

- [ ] Every number quoted in the text matches `results/`
- [ ] Every new figure and table is referenced in the text

## 8. Credit and merge

**Authors and co-authors:**

<!-- Merge: squash, after CI is green and one other member has approved. Add Co-authored-by lines to the squash message when someone else contributed. -->

## 9. Review (filled by the reviewer)

- [ ] I read the diff
- [ ] I checked the numbers in section 4 against the files
- [ ] I ran the commands of section 5 or the CI covers them
- [ ] I checked the report references and generated-artifact ownership
- [ ] I checked the linked issue, project item and spreadsheet handoff
- [ ] Requested changes are resolved

Decision: approve / request changes
