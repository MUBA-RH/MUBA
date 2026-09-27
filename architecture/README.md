# MUBA Ecosystem — Modular Architecture Staging

Status: ISOLATED / NON-PRODUCTION

This branch is the staging area for the MUBA ecosystem modularization. It does not replace or modify the production architecture until validation is complete.

## Target domains

- core
- assistant
- guardian
- creative
- daily-story
- web-distribution

## Migration invariants

1. Production behavior must remain unchanged.
2. Existing credentials, bot tokens, IDs, environment variables and public endpoints are reused; no credential rotation is implied by modularization.
3. Modules communicate through explicit interfaces instead of reaching into another module's internal implementation.
4. Migration is incremental. Each extracted module must pass regression checks before integration.
5. A failed validation stops migration; production remains on the existing stable baseline.
6. Vault remains passive and isolated. It is not a runtime dependency of this architecture.
7. MUBA-DAILY-STORY remains an existing external repository/runtime boundary until its integration contract is mapped and tested.

## Staging sequence

MAP -> SCAFFOLD -> MIGRATE ONE DOMAIN -> TEST -> COMPARE -> MERGE ONLY IF GREEN -> STABLE

No production source files are moved during the scaffold phase.
