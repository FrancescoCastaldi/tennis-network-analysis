"""Check that a pull request title and body follow .github/pull_request_template.md.

Run by the `PR check` workflow, which passes the title and body in the PR_TITLE and PR_BODY
environment variables. Locally:

    python scripts/check_pr_body.py --title "fix(triads): speed up the census" --body-file body.md

The exit status is 1 when anything is missing. Only the standard library is used.
"""

import argparse
import os
import re
import sys
from pathlib import Path

TITLE = re.compile(r"^(feat|fix|perf|refactor|test|docs|report|chore|build|ci|style)(\([a-z0-9_./,-]+\))?!?: \S.*$")

SECTIONS = {
    1: "Summary",
    2: "Classification",
    3: "Stages touched",
    4: "Effect on results",
    5: "Reproducibility",
    6: "Checks",
    7: "Report impact",
    8: "Credit and merge",
    9: "Review",
}

ROLES = {"A", "B1", "B2", "B3", "C"}
PHASES = {"setup", "analysis", "writing", "delivery"}
MILESTONES = {"Setup", "Analysis", "Writing", "Delivery"}
TYPES = {"feat", "fix", "perf", "refactor", "test", "docs", "report", "chore", "ci"}

# Choices of the template that the author must replace with one value.
MENUS = (
    "A / B1 / B2 / B3 / C",
    "setup / analysis / writing / delivery",
    "Setup / Analysis / Writing / Delivery",
    "feat / fix / perf",
    "yes / no",
    "passed / failed",
    "passed / total",
    "words / 5,000",
    "green / red / not run",
)

HEADING = re.compile(r"^## (\d+)\. (.+?)\s*$", re.MULTILINE)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
CHECKBOX = re.compile(r"^- \[([ xX])\] (.*)$", re.MULTILINE)
STOP = re.compile(r"^(\*\*|\||- \[|```|## )")


def split_sections(body):
    """Map section number to its text; also return the headings found, in order."""
    found = list(HEADING.finditer(body))
    sections = {}
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(body)
        sections[int(m.group(1))] = (m.group(2), body[m.end() : end])
    return sections


def label_value(text, label):
    """Text written after the bold label `**label:**`, or None when the label is missing."""
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*[ \t]*(.*)$", text, re.MULTILINE)
    if not m:
        return None
    value = [m.group(1)]
    for line in text[m.end() :].splitlines()[1:]:
        if STOP.match(line.strip()):
            break
        value.append(line)
    joined = "\n".join(value)
    joined = re.sub(r"^\s*-\s*$", "", joined, flags=re.MULTILINE)
    return joined.strip()


def table_rows(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def unchecked(text):
    return [m.group(2) for m in CHECKBOX.finditer(text) if m.group(1) == " "]


def checked(text):
    return [m.group(2) for m in CHECKBOX.finditer(text) if m.group(1) != " "]


def is_na(text):
    return re.search(r"^N/A\b", text, re.MULTILINE) is not None


def need_text(errors, text, label, section, minimum=1):
    value = label_value(text, label)
    if value is None:
        errors.append(f"Section {section}: the label **{label}:** is missing.")
    elif len(value) < minimum:
        errors.append(f"Section {section}: **{label}:** is empty (write N/A with a reason if it does not apply).")
    return value


def need_choice(errors, text, label, section, options):
    value = label_value(text, label)
    if value is None:
        errors.append(f"Section {section}: the label **{label}:** is missing.")
    elif not re.match(rf"^({'|'.join(options)})\b(?!\s*/)", value, re.IGNORECASE):
        errors.append(f"Section {section}: **{label}:** must start with {' or '.join(sorted(options))}.")


def check_summary(errors, text):
    need_text(errors, text, "Why", 1, minimum=10)
    need_text(errors, text, "What changes", 1, minimum=5)
    closes = label_value(text, "Closes")
    if closes is None:
        errors.append("Section 1: the label **Closes:** is missing.")
    elif not re.match(r"^(#\d+(,\s*#\d+)*|N/A.*)$", closes):
        errors.append("Section 1: **Closes:** needs issue numbers such as #12, or N/A.")


def check_classification(errors, text):
    values = {row[0]: row[1] for row in table_rows(text) if len(row) >= 2}
    rules = {
        "Role": (ROLES, True),
        "Phase": (PHASES, True),
        "Milestone": (MILESTONES, False),
        "Type": (TYPES, False),
        "Breaking for results or commands": ({"yes", "no"}, False),
    }
    for field, (allowed, several) in rules.items():
        value = values.get(field)
        if value is None:
            errors.append(f"Section 2: the row '{field}' is missing.")
            continue
        tokens = [t.strip() for t in value.split(",")] if several else [value.strip()]
        lowered = {a.lower(): a for a in allowed}
        if not all(t.lower() in lowered for t in tokens):
            errors.append(f"Section 2: '{field}' must be {' or '.join(sorted(allowed))}, found '{value}'.")


def check_stages(errors, text):
    if not checked(text):
        errors.append("Section 3: tick at least one stage touched.")


def check_results(errors, text):
    no_change = [t for t in checked(text) if t.startswith("No number")]
    change = [t for t in checked(text) if t.startswith("Numbers change")]
    if len(no_change) + len(change) != 1:
        errors.append("Section 4: tick exactly one of 'No number ... changes' and 'Numbers change'.")
    if change:
        rows = [r for r in table_rows(text)[1:] if len(r) >= 4]
        if not any(all(cell for cell in row[:4]) for row in rows):
            errors.append("Section 4: fill at least one row of the Before and After table.")
    need_choice(errors, text, "Conclusion changes", 4, {"yes", "no"})
    need_text(errors, text, "Reason if yes", 4)
    need_choice(errors, text, "Seed unchanged (20261115)", 4, {"yes", "no"})
    need_text(errors, text, "Null graphs per significance test", 4)


def check_reproducibility(errors, text):
    if is_na(text):
        return
    block = re.search(r"```[a-z]*\n(.*?)```", text, re.DOTALL)
    if not block or not block.group(1).strip():
        errors.append("Section 5: paste the commands run under **Commands run:**.")
    need_text(errors, text, "Environment", 5)
    for item in unchecked(text):
        errors.append(f"Section 5: not ticked: {item}")


def check_checks(errors, text):
    cells = {r[0].strip("`"): r[1] for r in table_rows(text)[1:] if len(r) >= 2}
    for command in ("ruff check .", "ruff format --check ."):
        if cells.get(command, "").lower() != "passed":
            errors.append(f"Section 6: '{command}' must be 'passed'.")
    if not re.search(r"\d", cells.get("pytest", "")) or "/ total" in cells.get("pytest", ""):
        errors.append("Section 6: write the pytest result with the number of tests, for example '77 passed'.")
    words = re.search(r"\d[\d,]*", cells.get("python -m tennis_networks.wordcount", ""))
    if not words or int(words.group().replace(",", "")) > 5000:
        errors.append("Section 6: the word count must be a number not above 5,000.")
    if cells.get("CI on the last commit (lint, tests, PDF build)", "").lower() != "green":
        errors.append("Section 6: CI on the last commit must be 'green' (a disabled workflow does not count).")
    for item in unchecked(text):
        errors.append(f"Section 6: not ticked: {item}")


def check_report(errors, text):
    if is_na(text):
        return
    need_text(errors, text, "Sections affected", 7)
    need_text(errors, text, "Word count before and after", 7)
    for item in unchecked(text):
        errors.append(f"Section 7: not ticked: {item}")


def check_credit(errors, text):
    need_text(errors, text, "Authors and co-authors", 8)


CHECKS = {
    1: check_summary,
    2: check_classification,
    3: check_stages,
    4: check_results,
    5: check_reproducibility,
    6: check_checks,
    7: check_report,
    8: check_credit,
}


def check(title, body):
    """Return the list of problems; an empty list means the pull request is complete."""
    errors = []
    if not TITLE.match(title.strip()):
        errors.append(
            "Title: use a Conventional Commit such as 'fix(triads): count 030C and 030T without the census' "
            "(types: feat, fix, perf, refactor, test, docs, report, chore, build, ci, style)."
        )
    body = COMMENT.sub("", body.replace("\r\n", "\n"))
    sections = split_sections(body)
    missing = [n for n in SECTIONS if n not in sections]
    if missing:
        errors.append(f"Body: missing sections {', '.join(map(str, missing))}. Keep the headings of the template.")
    if list(sections) != sorted(sections):
        errors.append("Body: the sections are out of order.")
    for number, run in CHECKS.items():
        if number not in sections:
            continue
        heading, text = sections[number]
        if not heading.startswith(SECTIONS[number]):
            errors.append(f"Section {number}: the heading must be '{SECTIONS[number]}', found '{heading}'.")
        for menu in MENUS:
            if menu in text:
                errors.append(f"Section {number}: replace the choice '{menu}' with one value.")
        run(errors, text)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--title", default=os.environ.get("PR_TITLE", ""))
    parser.add_argument("--body-file", default=None, help="read the body from a file instead of PR_BODY")
    args = parser.parse_args(argv)
    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else os.environ.get("PR_BODY", "")
    errors = check(args.title, body)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    lines = ["PR check passed."] if not errors else ["PR check found problems:", *[f"- {e}" for e in errors]]
    print("\n".join(lines))
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
