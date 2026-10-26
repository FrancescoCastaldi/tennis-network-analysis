# GitHub Copilot Instructions for tennis-network-analysis

This repository requires all contributions to follow a strict Pull Request workflow.

## Git and Pull Request Workflow
- Never commit or push directly to `main`. Pushing to `main` is blocked by GitHub repository rulesets.
- Always create a dedicated branch from `main`: `git checkout -b <type>/<topic>` where type is one of `feat`, `fix`, `docs`, `report`, `chore`, `test`.
- Push the branch and create a Pull Request against `main` using `.github/pull_request_template.md`.
- Fill all 9 sections of the PR template in English. The `PR check` CI workflow enforces this.
- Set PR labels: `role: <A|B1|B2|B3|C>`, `phase: <setup|analysis|writing|delivery>`, `type: <task|bug|report>`.
- Set assignee to the human contributor login and set the matching milestone (`Setup`, `Analysis`, `Writing`, or `Delivery`).
- Add the PR to project 3: `gh project item-add 3 --owner FrancescoCastaldi --url <PR_URL>`.

## Quality Gates
- Verify formatting and linting: `ruff check .` and `ruff format --check .`
- Run test suite: `pytest`
- Verify report word count: `python -m tennis_networks.wordcount`
- Never edit files in `results/` or `report/tables/` directly; run the corresponding `python -m tennis_networks.<module>` stage.
- English only, no em dashes, en dashes or double hyphens.
- Update `CHANGELOG.md` under `[Unreleased]` for all user-visible changes.
