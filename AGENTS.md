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
