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

## Pull requests

- Work through pull requests. Push fixes to the branch of the open PR; do not create extra branches or
  worktrees for a fix. One piece of work, one PR.
- Fill every section of `.github/pull_request_template.md`. The `PR check` workflow fails on an
  incomplete body or a title that is not a Conventional Commit.
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
