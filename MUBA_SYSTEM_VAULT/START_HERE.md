# MUBA System Vault — START HERE

Status: PASSIVE RECOVERY AND DESIGN PACKAGE. It is not a runtime dependency.

## Operator interface
```ini
operator_interface.locale=tr-TR
operator_interface.response_language=tr
operator_interface.technical_terms=preserve
```
When interacting with the DEV, speak Turkish unless the DEV explicitly requests another language. Keep canonical technical documentation and code in English.

## First decision — mandatory
Before changing or deploying anything, ask the DEV exactly which path is wanted:
1. **RESTORE CURRENT MUBA** — restore/verify the preserved stable system only. Do not build V2.
2. **BUILD MUBA V2 / AUTONOMY** — first verify the stable foundation, then build V2 separately under the safety rules in this Vault.
3. **CREATE A NEW PROJECT FROM THIS ARCHITECTURE** — create an isolated project profile/repository/deployment; never rename or overwrite MUBA production in place. Follow PROJECT_PORTABILITY.md.
If the DEV does not choose, do nothing.

## Mandatory reading order
1. START_HERE.md
2. CURRENT_SYSTEM.md
3. MODULE_REGISTRY.md
4. ARCHITECTURE.md
5. DEVELOPMENT_PROTOCOL.md
6. CONTINUITY.md
7. RECOVERY.md
8. AUTONOMY_BLUEPRINT.md
9. OPERATOR_MANUAL.md
10. PROJECT_PORTABILITY.md
11. RELEASE_MANIFEST.json

## Non-negotiable
- Never assume V2 is wanted.
- Never modify production directly.
- Never replace a working module merely because another architecture is preferred.
- Establish the actual repository/deployment state before any change.
- Stable production must remain available during development, failure, repair, and maintenance.
- New development is isolated. No red/unknown CI merge.
- A rollback path must exist before migration.
- Guardian, Assistant, Studio, website and unrelated services must survive unrelated work.
- Never store secrets in this Vault.
- Repository reality outranks stale documentation. If they conflict, stop, verify, then update the Vault through the normal protocol.
- The DEV is final authority.

This package is designed to be portable to another competent AI/developer. The receiver must guide a non-specialist DEV one verified step at a time.