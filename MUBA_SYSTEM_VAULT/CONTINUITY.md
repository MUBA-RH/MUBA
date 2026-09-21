# MUBA Continuity Contract

MUBA must remain understandable and recoverable even if the current AI/developer is unavailable.

## Durable knowledge locations
1. GitHub source history and stable commits.
2. This passive Vault branch.
3. GitHub workflows/tests/build definitions.
4. External provider accounts/secrets owned by DEV, kept outside Git.
5. Any future explicitly configured persistent runtime database/storage.

## Anti-amnesia rule
No critical production rule should exist only in chat memory.

Accepted system behavior belongs in one or more of:
- code;
- tests;
- GitHub technical documentation;
- release/recovery manifest;
- external provider configuration under DEV control.

## Handover rule
A replacement AI/developer must:
1. read START_HERE;
2. inspect actual GitHub state;
3. identify the current stable main SHA;
4. ask which path DEV wants;
5. avoid changing anything until that path is explicit.

## State warning
MUBA currently supports an in-memory repository fallback. Chat history or RAM state is not a disaster-recovery database. Any feature requiring durable history across restarts must have a verified persistent repository configuration.
