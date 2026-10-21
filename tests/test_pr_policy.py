import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pr_policy", ROOT / "scripts" / "pr_policy.py")
pr_policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr_policy)

HEAD = "c0ffee1"


def review(login, state, commit=HEAD):
    return {"user": {"login": login}, "state": state, "commit_id": commit}


def test_approval_by_another_reviewer_on_the_latest_commit_passes():
    assert pr_policy.approval_problems("francesco", HEAD, [review("gaetano", "APPROVED")]) == []


def test_no_review_is_rejected():
    assert pr_policy.approval_problems("francesco", HEAD, [])


def test_self_approval_does_not_count():
    problems = pr_policy.approval_problems("francesco", HEAD, [review("francesco", "APPROVED")])
    assert any("No approval yet" in p for p in problems)


def test_comment_only_review_does_not_count():
    assert pr_policy.approval_problems("francesco", HEAD, [review("gaetano", "COMMENTED")])


def test_approval_on_an_older_commit_is_stale():
    problems = pr_policy.approval_problems("francesco", HEAD, [review("gaetano", "APPROVED", commit="old")])
    assert any("older commit" in p for p in problems)


def test_changes_requested_after_an_approval_blocks():
    reviews = [review("gaetano", "APPROVED"), review("gaetano", "CHANGES_REQUESTED")]
    assert any("requested changes" in p for p in pr_policy.approval_problems("francesco", HEAD, reviews))


def test_new_approval_after_changes_requested_passes():
    reviews = [review("gaetano", "CHANGES_REQUESTED"), review("gaetano", "APPROVED")]
    assert pr_policy.approval_problems("francesco", HEAD, reviews) == []


def test_dismissed_review_is_cleared():
    reviews = [review("gaetano", "APPROVED"), review("gaetano", "DISMISSED")]
    assert pr_policy.approval_problems("francesco", HEAD, reviews)


def test_one_approval_is_enough_with_a_second_reviewer_commenting():
    reviews = [review("paolo", "COMMENTED"), review("gaetano", "APPROVED")]
    assert pr_policy.approval_problems("francesco", HEAD, reviews) == []


def test_dependabot_needs_no_approval():
    assert pr_policy.approval_problems("dependabot[bot]", HEAD, []) == []


def test_audit_flags_a_direct_push():
    assert pr_policy.audit_problems(None, []) == ["The commit reached main without a pull request."]


def test_audit_accepts_an_approved_pull_request():
    pull = {"number": 9, "user": {"login": "francesco"}, "head": {"sha": HEAD}}
    assert pr_policy.audit_problems(pull, [review("gaetano", "APPROVED")]) == []


def fake_fetch(pulls, reviews):
    def fetch(path):
        return pulls if path.endswith("/pulls") else reviews

    return fetch


def test_run_approval_exit_status(capsys):
    pull = {"user": {"login": "francesco"}, "head": {"sha": HEAD}}

    def fetch(path):
        return pull if path.endswith("/pulls/9") else [review("gaetano", "APPROVED")]

    assert pr_policy.run_approval("o/r", 9, fetch=fetch) == 0
    assert "Approved by another reviewer" in capsys.readouterr().out

    def fetch_none(path):
        return pull if path.endswith("/pulls/9") else []

    assert pr_policy.run_approval("o/r", 9, fetch=fetch_none) == 1


def test_run_audit_opens_an_issue_for_a_direct_push():
    issues = []
    status = pr_policy.run_audit(
        "o/r", "abcdef1234", fetch=fake_fetch([], []), open_issue=lambda repo, title, body: issues.append(title)
    )
    assert status == 1
    assert issues == ["Merge without approval: abcdef1"]


def test_run_audit_passes_for_an_approved_merge():
    merged = [{"number": 9, "merged_at": "2026-10-21", "user": {"login": "francesco"}, "head": {"sha": HEAD}}]
    issues = []

    def fetch(path):
        return merged if path.endswith("/pulls") else [review("gaetano", "APPROVED")]

    assert pr_policy.run_audit("o/r", "abcdef1234", fetch=fetch, open_issue=lambda *a: issues.append(a)) == 0
    assert issues == []
