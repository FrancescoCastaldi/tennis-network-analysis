# AGENTS.md

Guidance for coding assistants working in this repository. Humans: see CONTRIBUTING.md.

- Everything in the repository is in English: code, comments, docs, commit messages and the report.
- Never edit `report/tables/`, `report/figures/` or `results/` by hand; change the code and rerun
  the matching `python -m tennis_networks.<module>`.
- Keep every random draw on the seed in `config/networks.json`.
- Never modify `data/raw/`; tests check its SHA-256 digests.
- Run `ruff check .`, `ruff format --check .` and `pytest` before declaring a change done.
- Update `CHANGELOG.md` under `[Unreleased]` for every user-visible change.
- No student ID numbers, emails or private notes in the repository.
- Do not use em dashes, en dashes or double hyphens to join sentences; use commas, colons or brackets.
- No credentials are needed; never add `.env` files.

## Releases

- Releases follow SemVer and are made only with `scripts/release.py` and the `Release` workflow; steps in
  `CONTRIBUTING.md`. Never create a release or a tag by hand, never use a lightweight tag, never move,
  delete or reuse a published tag: fix forward with a patch release.
- A release is a PR `chore(release): vX.Y.Z` from a branch `chore/release-vX.Y.Z`, with the same labels,
  assignee, milestone and reviewers as any PR. It is merged first, then the annotated tag is pushed from `main`.
- Release at the end of each phase (milestone Setup, Analysis, Writing, Delivery) and whenever a snapshot
  must be shared or cited. Minor step when a change moves a result, the report or the pipeline, patch step
  for fixes that move nothing, `1.0.0` for the report as submitted.
- A release must be rich and explained, as for a project meant to be reused:
  - the changelog section opens with a summary paragraph for a reader who has not followed the work, then
    the entries grouped under Added, Changed, Fixed and so on, each one saying what changed and why it matters;
  - the annotated tag message and the GitHub release title start with `vX.Y.Z:` and the first sentence of
    the summary;
  - the release carries `report-vX.Y.Z.pdf`, `results-vX.Y.Z.tar.gz` and `SHA256SUMS.txt`, and its notes list
    the report snapshot (words), the checksums, the contributors and the compare link;
  - `pyproject.toml`, `__init__.py`, `CITATION.cff` and the changelog link references agree with the tag;
    `scripts/release.py check` verifies it and the workflow refuses a tag that does not pass.
- After the workflow ends, open the release page and check the notes, the assets and the compare link. Report
  in the PR comment what you saw. No AI signature, em dash or local file path in tags, notes or titles.

## Pull requests

- Work through pull requests. Push fixes to the branch of the open PR; do not create extra branches or
  worktrees for a fix. One piece of work, one PR.
- Fill every section of `.github/pull_request_template.md`. The `PR check` workflow fails on an
  incomplete body or a title that is not a Conventional Commit.
- Set the metadata of every PR when you open it, not later:
  - labels: one `role: <A|B1|B2|B3|C>` (the role of the author), one `phase: <setup|analysis|writing|delivery>`
    and one `type: <task|bug|report>` (`report` for changes to `report/main.tex`, `bug` for a wrong number
    or a pipeline failure, `task` otherwise), plus `documentation`, `maintenance` or `dependencies` when
    they apply;
  - assignee: the member who wrote the change, never an assistant;
  - milestone: the one of the phase (`Setup`, `Analysis`, `Writing` or `Delivery`), the same as the
    Milestone row of the PR body;
  - reviewers: request a review from the group B members other than the author (roles B1, B2, B3), and
    from the owner of any section of another role that the PR edits;
  - description: the whole template, the issue number in **Closes:** when an issue exists, and the context
    comment below.
  Check with `gh pr view <number> --json labels,assignees,milestone,reviewRequests` before saying a PR is
  ready: a PR without labels, assignee, milestone or reviewers is not ready.
- Every time you act on a PR (review, fix, answer, merge), post one context comment on it with
  `gh pr comment <number> --body-file <file>`. It has these headings, in this order:
  1. `Context`: what the PR does and what was asked, in two or three sentences.
  2. `Findings and fixes`: a table with finding, action taken and commit hash; findings left as they
     are get the technical reason.
  3. `Checks run`: each command with its result (ruff, pytest, word count, CI).
  4. `Open points`: what is left, who acts next, and whether the PR is ready to merge.
- Answer each inline review thread separately, citing the commit that fixes it.
- Credit the author of the change in the comment and keep them as author of the squashed commit.
- Every change to the repository goes through a pull request: no push to `main`, no branch without a
  PR, one branch per PR named `<type>/<topic>`. Fixes after a review go on the same branch.
- Merge with squash only when all of these hold: CI is green, the PR body is complete (`PR check`) and
  another member has approved the latest commit (`Approved by another reviewer` is green; check
  `gh pr view <number> --json reviewDecision,reviews`). The author cannot approve their own PR, and an
  assistant never approves or merges on behalf of the reviewer. If the owner waives the approval,
  record it in the context comment.
- If the `CI` workflow or GitHub Actions is disabled, say so in the comment and ask before enabling it.
- No AI signature, `Co-Authored-By` trailer for an assistant, em dash or local file path in commits,
  comments or logs.
