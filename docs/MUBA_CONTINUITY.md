# MUBA Continuity Standard

## Goal
Keep MUBA understandable, recoverable and historically consistent as the project evolves.

## Canonical history
`/muba_history.json` is the only canonical user-facing development timeline.

Consumers:
- public Website Development Log;
- Telegram Assistant MUBA Updates;
- MUBA Daily Development Log / Updates.

Do not maintain separate copies of the same development history.

## Change rule
Any user-facing change to the website, Telegram runtime, Assistant, Guardian, Studio, Gallery, brain/layers or Android client must add a new history entry in the same PR.

History is append-only:
- add new records;
- do not rewrite established history;
- corrections require a new correction/fix record rather than silently changing the old event.

CI validates this.

## Persistence
Runtime state should use persistent storage when one is available. Memory fallback keeps the application functional but is not disaster-recovery storage.

Gallery visibility states:
- `public` — visible on the website;
- `hidden` — retained but not publicly served;
- `rejected` — retained as a moderation decision and not publicly served.

## Merge discipline
- work from current stable `main`;
- isolate changes in a branch;
- preserve current behavior unless the requested change explicitly alters it;
- run all relevant tests;
- merge only when green;
- validate `main` after merge;
- refresh the passive Vault after meaningful stable milestones.

## GitHub limitation
Branch protection/rulesets require repository administration access. The connected GitHub App used by automated maintenance does not expose administration mutations. Continuity CI checks are therefore installed in-repository; repository-level required-check enforcement must be enabled through GitHub administration when available.

## License and protected reuse
`LICENSE.md` is the canonical MUBA source-availability notice.

MUBA is publicly viewable but reuse is permission-required. Changes to the license, authorization registry, permission template, permission gate or permission-model documentation are treated as user-facing continuity changes and must add a new `muba_history.json` record.

The official new-project Vault path is deny-by-default. A valid permission document must match an active SHA-256 approval fingerprint in the official authorization registry. MUBA's own restore path is not a third-party reuse path.

Third-party components continue under their own licenses and ownership.

## Automatic Vault refresh
Every push to `main` starts `MUBA Vault Auto Sync`.

The workflow does **not** immediately copy production. It first:
1. installs the pinned runtime dependencies;
2. compiles the production runtime modules;
3. runs the complete Telegram regression suite;
4. runs the public website smoke checker;
5. validates the canonical MUBA History schema.

Only a green run may synchronize `main` into `vault/system-vault-final`.

Vault-specific recovery material under `MUBA_SYSTEM_VAULT/` and the standalone export workflow are protected from source synchronization. The workflow updates the stable-main recovery SHA and automatic snapshot log, commits only to the passive Vault branch, and then creates a fresh ZIP plus SHA256 artifact in the same run.

A failed validation does not update the Vault. The workflow never writes back to `main` and never auto-activates V2/autonomy.

