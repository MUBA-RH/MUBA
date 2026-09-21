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

## License
Do not select a software license implicitly. License choice changes third-party reuse rights and remains a DEV decision.
