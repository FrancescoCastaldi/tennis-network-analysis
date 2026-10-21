"""Pull request policy: approval by another reviewer, and an audit of what reaches main.

GitHub cannot block a merge on this private repository (branch protection needs a paid plan),
so two workflows run these checks and make a missing approval visible:

    python scripts/pr_policy.py approval --repo OWNER/NAME --pr 9
    python scripts/pr_policy.py audit --repo OWNER/NAME --sha <commit on main>

Both need the gh CLI and a GH_TOKEN. The exit status is 1 when the policy is broken.
Only the standard library is used.
"""

import argparse
import json
import os
import subprocess
import sys

BOTS = {"dependabot[bot]"}


def latest_reviews(reviews):
    """Last decisive review of each reviewer: APPROVED or CHANGES_REQUESTED; a dismissal clears it."""
    latest = {}
    for review in reviews:
        login = review["user"]["login"]
        state = review["state"]
        if state in {"APPROVED", "CHANGES_REQUESTED"}:
            latest[login] = review
        elif state == "DISMISSED":
            latest.pop(login, None)
    return latest


def approval_problems(author, head_sha, reviews):
    """Why the pull request cannot be merged yet; an empty list means it can."""
    if author in BOTS:
        return []
    latest = latest_reviews(reviews)
    others = {login: r for login, r in latest.items() if login != author}
    problems = []
    for login, review in sorted(others.items()):
        if review["state"] == "CHANGES_REQUESTED":
            problems.append(f"{login} requested changes: resolve them and ask for a new review.")
    approved = [login for login, r in others.items() if r["state"] == "APPROVED"]
    current = [login for login in approved if others[login]["commit_id"] == head_sha]
    if approved and not current:
        problems.append(f"The approval of {', '.join(sorted(approved))} is on an older commit: ask for a new review.")
    if not approved:
        problems.append("No approval yet: a reviewer other than the author must approve the latest commit.")
    return problems


def audit_problems(pull, reviews):
    """Problems of the pull request that produced a commit on main; `pull` is None for a direct push."""
    if pull is None:
        return ["The commit reached main without a pull request."]
    return approval_problems(pull["user"]["login"], pull["head"]["sha"], reviews)


def gh_json(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def report(lines):
    print("\n".join(lines))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def run_approval(repo, number, fetch=gh_json):
    pull = fetch(f"repos/{repo}/pulls/{number}")
    reviews = fetch(f"repos/{repo}/pulls/{number}/reviews?per_page=100")
    problems = approval_problems(pull["user"]["login"], pull["head"]["sha"], reviews)
    report(["Approved by another reviewer."] if not problems else ["Approval missing:", *[f"- {p}" for p in problems]])
    return 1 if problems else 0


def run_audit(repo, sha, fetch=gh_json, open_issue=None):
    pulls = [p for p in fetch(f"repos/{repo}/commits/{sha}/pulls") if p.get("merged_at")]
    pull = pulls[0] if pulls else None
    reviews = fetch(f"repos/{repo}/pulls/{pull['number']}/reviews?per_page=100") if pull else []
    problems = audit_problems(pull, reviews)
    if not problems:
        report([f"Commit {sha[:7]} came from an approved pull request."])
        return 0
    title = f"Merge without approval: {sha[:7]}"
    body = "\n".join(
        [
            f"Commit {sha} on main does not follow the pull request policy:",
            *[f"- {p}" for p in problems],
            "",
            "Open a follow-up pull request if the change needs review, or note here why it was fine.",
        ]
    )
    report([title, *[f"- {p}" for p in problems]])
    (open_issue or gh_issue)(repo, title, body)
    return 1


def gh_issue(repo, title, body):
    subprocess.run(["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    approval = sub.add_parser("approval", help="check that another reviewer approved the latest commit")
    approval.add_argument("--repo", required=True)
    approval.add_argument("--pr", required=True, type=int)
    audit = sub.add_parser("audit", help="check that a commit on main came from an approved pull request")
    audit.add_argument("--repo", required=True)
    audit.add_argument("--sha", required=True)
    args = parser.parse_args(argv)
    if args.command == "approval":
        return run_approval(args.repo, args.pr)
    return run_audit(args.repo, args.sha)


if __name__ == "__main__":
    sys.exit(main())
