"""Prepare, check and describe a release of the project.

A release is a pull request that rolls the changelog and bumps the version, followed by an annotated
tag on `main` that the `Release` workflow turns into a GitHub release with notes and assets.

    python scripts/release.py prepare 0.3.0 --summary "One or two sentences on what this release is."
    python scripts/release.py check v0.3.0
    python scripts/release.py notes v0.3.0 [--assets dist]
    python scripts/release.py tag v0.3.0 [--push]

`prepare` moves the `Unreleased` section of CHANGELOG.md under the new version, with the summary as its
first paragraph, rebuilds the link references at the bottom and bumps the version in pyproject.toml,
`tennis_networks/__init__.py` and CITATION.cff. Only the standard library is used.
"""

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "src" / "tennis_networks" / "__init__.py"
CITATION = ROOT / "CITATION.cff"
REPORT = ROOT / "report" / "main.tex"

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
HEADING = re.compile(r"^## \[(?P<name>[^\]]+)\](?: - (?P<date>\d{4}-\d{2}-\d{2}))?\s*$", re.MULTILINE)
LINK = re.compile(r"^\[[^\]]+\]: https?://\S+\s*$", re.MULTILINE)
BASE = re.compile(r"^\[Unreleased\]: (?P<base>https?://\S+?)/compare/", re.MULTILINE)
# Titles of the Keep a Changelog groups as they appear in the notes of a release.
GROUPS = {
    "Added": "What is new",
    "Changed": "What changed",
    "Performance": "Performance",
    "Fixed": "Fixes",
    "Security": "Security",
    "Deprecated": "Deprecated",
    "Removed": "Removed",
}
ASSETS = {
    "report": ("report-v{v}.pdf", "The report, compiled from `report/main.tex` at this tag"),
    "results": ("results-v{v}.tar.gz", "`results/` and the generated tables and figures of the report"),
    "sums": ("SHA256SUMS.txt", "SHA-256 of the files above"),
}


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def sections(text):
    """Map each heading of the changelog (`Unreleased` or a version) to its body, in file order."""
    found = list(HEADING.finditer(text))
    out = {}
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        body = LINK.sub("", text[m.end() : end])
        out[m.group("name")] = body.strip()
    return out


def summary_of(body):
    """The paragraph before the first group of a release: what the release is about."""
    return re.split(r"^### ", body, maxsplit=1, flags=re.MULTILINE)[0].strip()


def groups_of(body):
    """List of (group title, bullets) of a release body, in the order of GROUPS."""
    parts = re.split(r"^### (.+)$", body, flags=re.MULTILINE)[1:]
    found = [(parts[i].strip(), parts[i + 1].strip()) for i in range(0, len(parts), 2) if parts[i + 1].strip()]
    order = list(GROUPS)
    return sorted(found, key=lambda g: order.index(g[0]) if g[0] in order else len(order))


def link_block(base, versions):
    """Link references of the changelog: Unreleased first, then each version against the one before it."""
    ordered = sorted(versions, key=version_key, reverse=True)
    lines = [f"[Unreleased]: {base}/compare/v{ordered[0]}...HEAD"]
    for i, v in enumerate(ordered):
        if i + 1 < len(ordered):
            lines.append(f"[{v}]: {base}/compare/v{ordered[i + 1]}...v{v}")
        else:
            lines.append(f"[{v}]: {base}/releases/tag/v{v}")
    return "\n".join(lines)


def roll_changelog(text, version, day, summary):
    """Move the `Unreleased` section under `version`, add the summary and rebuild the link references."""
    if not SEMVER.match(version):
        raise ValueError(f"'{version}' is not a version such as 0.3.0")
    if not summary.strip():
        raise ValueError("a release needs a summary: one or two sentences on what it is about")
    found = sections(text)
    released = [name for name in found if name != "Unreleased"]
    if version in released:
        raise ValueError(f"version {version} is already in the changelog")
    if released and version_key(version) <= max(map(version_key, released)):
        raise ValueError(f"version {version} is not above {max(released, key=version_key)}")
    if not groups_of(found.get("Unreleased", "")):
        raise ValueError("the Unreleased section has no entries to release")
    base = BASE.search(text).group("base")
    head = next(m for m in HEADING.finditer(text) if m.group("name") == "Unreleased")
    following = HEADING.search(text, head.end())
    start, end = head.start(), following.start() if following else len(text)
    body = LINK.sub("", text[head.end() : end]).strip()
    rolled = f"## [Unreleased]\n\n## [{version}] - {day}\n\n{summary.strip()}\n\n{body}\n\n"
    rest = LINK.sub("", text[end:]).rstrip()
    return text[:start] + rolled + (rest + "\n\n" if rest else "") + link_block(base, released + [version]) + "\n"


def bump_version(text, version, pattern, template):
    """Replace the first match of `pattern` (a regex with one group around the old version) in `text`."""
    new, count = re.subn(pattern, template.format(version=version), text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"no version line matching {pattern!r}")
    return new


def versions_in(project, init, citation):
    """The version written in pyproject.toml, in `__init__.py` and in CITATION.cff."""
    return {
        "pyproject.toml": re.search(r'^version = "([^"]+)"', project, re.MULTILINE).group(1),
        "__init__.py": re.search(r'^__version__ = "([^"]+)"', init, re.MULTILINE).group(1),
        "CITATION.cff": re.search(r"^version: (\S+)", citation, re.MULTILINE).group(1),
    }


def problems(tag, changelog, project, init, citation):
    """Reasons why `tag` cannot be released; an empty list means the files agree."""
    version = tag[1:] if tag.startswith("v") else tag
    errors = []
    if not tag.startswith("v") or not SEMVER.match(version):
        return [f"tag '{tag}' must look like v0.3.0"]
    for name, found in versions_in(project, init, citation).items():
        if found != version:
            errors.append(f"{name} says {found}, the tag says {version}")
    found = sections(changelog)
    body = found.get(version)
    if body is None:
        errors.append(f"CHANGELOG.md has no section [{version}]; run `scripts/release.py prepare {version}`")
        return errors
    if not summary_of(body):
        errors.append(f"CHANGELOG.md [{version}] has no summary paragraph under its heading")
    if not groups_of(body):
        errors.append(f"CHANGELOG.md [{version}] has no entries")
    if not HEADING.search(changelog) or HEADING.search(changelog).group("name") != "Unreleased":
        errors.append("CHANGELOG.md must start with an [Unreleased] section")
    if f"[{version}]: " not in changelog:
        errors.append(f"CHANGELOG.md has no link reference for [{version}]")
    return errors


def render_notes(version, body, previous, base, words=None, assets=None, contributors=()):
    """Markdown of the GitHub release: summary, grouped changes, report snapshot, downloads, credits."""
    lines = [summary_of(body), ""]
    for title, bullets in groups_of(body):
        lines += [f"## {GROUPS.get(title, title)}", "", bullets, ""]
    if words is not None:
        lines += ["## Report snapshot", "", "| | |", "|---|---|", f"| Words | {words:,} of 5,000 |", ""]
    if assets:
        lines += ["## Downloads", "", "| File | What it is | SHA-256 |", "|---|---|---|"]
        for name, what, digest in assets:
            lines.append(f"| `{name}` | {what} | `{digest[:16]}` |")
        lines += ["", "Check a download with `sha256sum -c SHA256SUMS.txt`.", ""]
    if contributors:
        lines += ["## Contributors", "", ", ".join(contributors), ""]
    compare = f"{base}/compare/{previous}...v{version}" if previous else f"{base}/commits/v{version}"
    lines += [
        "## Full changelog",
        "",
        f"[{previous or 'first commit'}...v{version}]({compare}). To cite this work use `CITATION.cff`.",
        "",
    ]
    return "\n".join(lines)


def tag_message(version, body):
    """Message of the annotated tag: a title line, the summary and the grouped changes in plain text."""
    first = summary_of(body).split(". ")[0].rstrip(".")
    lines = [f"v{version}: {first}", "", summary_of(body), ""]
    for title, bullets in groups_of(body):
        lines += [f"{GROUPS.get(title, title)}:", bullets, ""]
    return "\n".join(lines).rstrip() + "\n"


def git(*args, check=True):
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if check and done.returncode:
        raise RuntimeError(done.stderr.strip() or f"git {' '.join(args)} failed")
    return done.stdout.strip()


def previous_tag(tag):
    out = git("describe", "--tags", "--abbrev=0", f"{tag}^", check=False)
    return out or None


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_rows(directory, version):
    rows = []
    for key in ("report", "results", "sums"):
        pattern, what = ASSETS[key]
        path = Path(directory) / pattern.format(v=version)
        if path.exists():
            rows.append((path.name, what, sha256(path) if key != "sums" else ""))
    return [(n, w, d or "see the file") for n, w, d in rows]


def read(path):
    return path.read_text(encoding="utf-8")


def command_prepare(args):
    version = args.version.lstrip("v")
    day = args.date or date.today().isoformat()
    new_changelog = roll_changelog(read(CHANGELOG), version, day, args.summary)
    pyproject = bump_version(read(PYPROJECT), version, r'^version = "[^"]+"', 'version = "{version}"')
    init = bump_version(read(INIT), version, r'^__version__ = "[^"]+"', '__version__ = "{version}"')
    citation = bump_version(read(CITATION), version, r"^version: \S+", "version: {version}")
    citation = bump_version(citation, day, r"^date-released: \S+", "date-released: {version}")
    if args.dry_run:
        print(f"would release {version} on {day}")
        return 0
    for path, text in ((CHANGELOG, new_changelog), (PYPROJECT, pyproject), (INIT, init), (CITATION, citation)):
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"Prepared {version}. Open a release PR, merge it, then run: python scripts/release.py tag v{version} --push")
    return 0


def command_check(args):
    errors = problems(args.tag, read(CHANGELOG), read(PYPROJECT), read(INIT), read(CITATION))
    if not errors and args.tag_exists:
        if git("cat-file", "-t", args.tag, check=False) != "tag":
            errors.append(f"{args.tag} is a lightweight tag: create it annotated with `scripts/release.py tag`")
        on_main = subprocess.run(
            ["git", "merge-base", "--is-ancestor", f"{args.tag}^{{commit}}", "origin/main"], cwd=ROOT, check=False
        )
        if on_main.returncode:
            errors.append(f"{args.tag} is not on origin/main")
    print("\n".join(["Release check passed."] if not errors else ["Release check found problems:", *errors]))
    return 1 if errors else 0


def command_notes(args):
    version = args.tag.lstrip("v")
    changelog = read(CHANGELOG)
    body = sections(changelog)[version]
    base = BASE.search(changelog).group("base")
    previous = args.previous or previous_tag(args.tag)
    sys.path.insert(0, str(ROOT / "src"))
    from tennis_networks.wordcount import count

    # The words of the report as it is at the tag, not in the working tree.
    report = git("show", f"{args.tag}:report/main.tex", check=False) or read(REPORT)
    span = f"{previous}..{args.tag}" if previous else args.tag
    people = [line.split("\t", 1)[1] for line in git("shortlog", "-sn", span, check=False).splitlines() if "\t" in line]
    assets = asset_rows(args.assets, version) if args.assets else None
    print(render_notes(version, body, previous, base, count(report), assets, people))
    return 0


def command_tag(args):
    version = args.tag.lstrip("v")
    body = sections(read(CHANGELOG)).get(version)
    if body is None:
        print(f"no section [{version}] in CHANGELOG.md", file=sys.stderr)
        return 1
    done = subprocess.run(
        ["git", "tag", "-a", args.tag, "-F", "-"], cwd=ROOT, input=tag_message(version, body), text=True, check=False
    )
    if done.returncode == 0 and args.push:
        git("push", "origin", args.tag)
    return done.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="roll the changelog and bump the version")
    p.add_argument("version")
    p.add_argument("--summary", required=True)
    p.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(run=command_prepare)
    p = sub.add_parser("check", help="check that the files agree with a tag")
    p.add_argument("tag")
    p.add_argument("--tag-exists", action="store_true", help="also check that the tag is annotated and on main")
    p.set_defaults(run=command_check)
    p = sub.add_parser("notes", help="print the notes of the GitHub release")
    p.add_argument("tag")
    p.add_argument("--previous", default=None)
    p.add_argument("--assets", default=None, help="folder with the files attached to the release")
    p.set_defaults(run=command_notes)
    p = sub.add_parser("tag", help="create the annotated tag with a rich message")
    p.add_argument("tag")
    p.add_argument("--push", action="store_true")
    p.set_defaults(run=command_tag)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
