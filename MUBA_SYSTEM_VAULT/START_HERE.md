# MUBA System Vault — START HERE

Status: PASSIVE, ISOLATED RECOVERY / CONTINUITY / HANDOVER PACKAGE.

This Vault is intentionally kept outside the production runtime. It exists to preserve MUBA, explain MUBA, recover MUBA, and hand MUBA to another competent AI/developer if necessary. Nothing under MUBA_SYSTEM_VAULT may be imported by production code or required for normal operation.

## Operator interface
- Speak Turkish to the DEV by default unless the DEV asks for another language.
- Preserve canonical code, identifiers, comments, commit messages, schemas and technical documentation in English.
- User-facing product text may remain multilingual where the product requires it.

## First decision — mandatory
Before restoration or future architecture work, ask the DEV to choose exactly one path:
1. RESTORE CURRENT MUBA
2. BUILD / TEST MUBA V2 OR AUTONOMY IN ISOLATION
3. CREATE A NEW PROJECT FROM THIS ARCHITECTURE

If the DEV does not choose a path, do not activate, migrate or replace anything.

## Mandatory reading order
1. START_HERE.md
2. VAULT_SCOPE.md
3. PROJECT_IDENTITY.md
4. CURRENT_SYSTEM.md
5. TELEGRAM_SYSTEM.md
6. ANDROID_V3_APK.md
7. CODE_LANGUAGE_STANDARD.md
8. MODULE_REGISTRY.md
9. ARCHITECTURE.md
10. DEVELOPMENT_PROTOCOL.md
11. CONTINUITY.md
12. RECOVERY.md
13. OPERATOR_MANUAL.md
14. PROJECT_PORTABILITY.md
15. AUTONOMY_BLUEPRINT.md
16. CHANGELOG_SNAPSHOT_2026-09-21.md
17. RELEASE_MANIFEST.json

## Non-negotiable
- Current stable MUBA is the production baseline.
- Vault is passive and isolated.
- V2 never activates automatically.
- Never replace working production merely because a newer design exists.
- Never put credentials or secrets in Git/Vault.
- Verify repository reality before acting.
- Preserve rollback before migration.
- GitHub is the canonical development/source-control location for this package.
- The DEV is final authority.

## Permanent operating command
BAŞLA 🔥 MERGE 🟢 SİSTEMİ KORU 🛡️ STABİL 🔒

Meaning: start the requested scoped change, work in isolation, preserve the current stable system, test, validate, merge only when green, verify, and keep the resulting production stable.
