# MUBA Recovery Runbook

## Path A — Restore Current MUBA
Use when DEV wants the preserved current MUBA, not V2.

Recovery anchor captured by this Vault:
`602ebffe23de7373e7ee513af33dea219fe6deba`

Steps:
1. Do not activate V2.
2. Verify GitHub access and external provider ownership.
3. Create recovery work from the exact stable anchor/snapshot.
4. Restore required environment/secrets from DEV-controlled provider secret stores; never copy secrets from documentation.
5. Run Telegram production tests.
6. Verify website independently.
7. Verify webhook/bot runtime independently.
8. Live-test Guardian state/authority.
9. Live-test private Assistant.
10. Verify Studio only if its provider configuration is available.
11. Rebuild Android V3 separately only if DEV needs it; Android V3 is not required for Bot API recovery.
12. Declare STABLE only after evidence.

## Path B — Build/Test V2
Keep current MUBA BLUE intact. Build candidate separately. No automatic promotion.

## Android V3 recovery
Use android-v3 source and GitHub workflow with securely supplied GitHub Actions secrets. Never reuse or expose production bot credentials.

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
- external billing/subscriptions.

Those remain DEV-controlled.
