# Timesheet synchronization

The `SNA - UNIBO` Google Sheet is an external planning asset. This repository does
not contain its credentials or a stable row and column mapping, so automation must
not guess which `Attivita` row to edit.

The verified updates that can be recorded without inventing hours are kept in
[`config/timesheet_updates.json`](../config/timesheet_updates.json). The manifest
records only dates, activities and completion status:

- PR #36 merged on 2026-11-01
- PR #40 merged on 2026-11-01
- PR #41 merged on 2026-11-01

Run `python scripts/sync_sheet.py --dry-run --sheet-id "$SNA_SHEET_ID"` to inspect
the dashboard writes. The script updates only `Panoramica!B5` and `Panoramica!F5`;
it does not write timesheet rows. To complete the timesheet update, a contributor
with access to the sheet must match each manifest entry to the existing `Attivita`
row, enter the verified date, activity and status, leave hours unchanged or blank,
and read the edited rows back. If the sheet owner supplies a stable row mapping,
it should be added to the manifest and reviewed before any row-writing automation
is enabled.
