# MUBA Stable Release Checklist

Use this checklist for meaningful stable milestones.

## Before merge
- Confirm the branch starts from current stable `main`.
- Confirm the change is isolated from production until merge.
- Add/adjust regression tests.
- Add a new `muba_history.json` record for user-facing changes.
- Confirm no established history record was rewritten.
- Confirm no credentials, tokens, sessions or private identifiers entered Git.
- Telegram Bot Tests: green.
- MUBA Continuity Gate: green when applicable.
- MUBA Web Smoke: green when applicable.

## Merge
- Merge only the reviewed green PR.
- Record the resulting `main` SHA.
- Do not auto-enable V2/autonomy work.

## After merge
- Confirm post-merge runtime tests are green.
- Confirm GitHub Pages deploy is green when web files changed.
- Confirm live website loads.
- Confirm Studio and Gallery endpoints still respond when they changed.
- Confirm `/health/state` reports expected persistence.
- Refresh the passive MUBA System Vault for meaningful stable milestones.
- Export a new downloadable Vault package and checksum.

## Rollback
If production validation fails:
- keep the last known-good SHA;
- revert the failing change rather than patching production blindly;
- preserve failure evidence;
- fix in an isolated branch and repeat the full green path.
