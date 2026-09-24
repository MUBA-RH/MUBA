# MUBA Recovery Runbook

## Path A — Restore Current MUBA
Use when DEV wants the preserved current MUBA, not V2.

Recovery anchor captured by this Vault:
`5fd6c7c253b89171d568f0cc70797843a379e48c`

Steps:
1. Do not activate V2.
2. Verify GitHub access and external provider ownership.
3. Create recovery work from the exact stable anchor/snapshot.
4. Restore required environment/secrets from DEV-controlled provider secret stores; never copy secrets from documentation.
5. Install the pinned Telegram runtime dependencies.
6. Run Telegram production regression tests.
7. Run MUBA Continuity and Web Smoke checks.
8. Verify GitHub Pages independently.
9. Verify webhook/bot runtime independently.
10. Verify `/health/state` and confirm whether state/Gallery storage is truly persistent.
11. Live-test Guardian state/authority.
12. Live-test private Assistant, MUBA Updates and MUBA Daily.
13. Live-test Studio and Gallery; verify hidden/rejected Gallery items are not publicly served.
14. Rebuild Android V3 separately only if DEV needs it; Android V3 is not required for Bot API recovery.
15. Declare STABLE only after evidence.

## Path B — Build/Test V2
Keep current MUBA intact. Build candidate separately. No automatic promotion.

## Android V3 recovery
Use `android-v3/` source and GitHub workflow with securely supplied GitHub Actions secrets. Never reuse or expose production bot credentials.

## Rollback
If a new release fails, restore authority/routing to the last verified stable main state. Do not stack speculative patches on failing production.

## External limits
The Vault cannot recreate:
- provider account ownership;
- bot tokens;
- Telegram user sessions;
- API hashes;
- signing keys;
- 2FA credentials;
- external billing/subscriptions;
- GitHub branch-protection administration.

Those remain DEV-controlled.
