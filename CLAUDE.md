@AGENTS.md

## Claude Code & AI Assistant Directives

- MANDATORY GIT WORKFLOW:
  1. NEVER commit or push directly to `main`. Direct push to `main` is strictly blocked by GitHub repository rulesets.
  2. ALWAYS work on a dedicated branch from up-to-date `main`:
     `git checkout main && git pull origin main && git checkout -b <type>/<topic>`
     Allowed types: `feat/`, `fix/`, `docs/`, `report/`, `chore/`, `test/`.
  3. ALWAYS push the branch and open a Pull Request immediately:
     `git push -u origin <type>/<topic>`
     `gh pr create --title "<type>(<scope>): <description>" --template .github/pull_request_template.md`
  4. Fill EVERY section of `.github/pull_request_template.md` in English. Never remove sections or leave empty menus.
  5. Set PR metadata immediately upon creation:
     `gh pr edit <pr-number> --add-label "role: <A|B1|B2|B3|C>,phase: <setup|analysis|writing|delivery>,type: <task|bug|report>" --add-assignee <author-login> --milestone <Milestone>`
     And add to the project:
     `gh project item-add 3 --owner FrancescoCastaldi --url <pr-url>`
  6. Request reviews from peer members (`bonfito`, `tanooom`, `FrancescoCastaldi`).
- VERIFICATION BEFORE ASKING FOR REVIEW:
  Run locally and ensure all pass:
  `ruff check .`
  `ruff format --check .`
  `pytest`
  `python -m tennis_networks.wordcount`
- REVIEWS AND CONTEXT COMMENTS:
  - Every PR action (review, fix, answer, merge) requires a context comment with headings: `Context`, `Findings and fixes`, `Checks run`, `Open points`.
  - Answer inline review comments separately, citing the fixing commit.
- MERGING:
  - Squash-merge into `main` only when CI is green, PR check is green, and peer review is approved.
  - The branch is deleted upon merge.
- Several `python -m tennis_networks.<module>` entry points have no `--help` and run the stage when called with it.
