# Recovery Runbook

## Restore Current MUBA
If DEV selects RESTORE CURRENT MUBA:
1. Do not build V2.
2. Verify ownership/access to GitHub and required external provider accounts.
3. Verify anchor commit d09aad85380ac87586e3656f796fc27967d75856.
4. Inspect RELEASE_MANIFEST.json and files at that exact commit.
5. Restore/deploy from that immutable commit or a branch created from it; do not redesign during recovery.
6. Recreate required environment configuration from the operator's secure provider/secret store. Never commit credentials.
7. Run repository CI/tests.
8. Verify website independently.
9. Verify Telegram webhook/runtime independently.
10. Live-test Guardian, private Assistant, group #MUBA ASSISTANT and Studio as applicable.
11. Provider changes are handled only through a new branch/test/PR protocol while preserving the anchor.
12. Declare restored stable only after verification.

## V2 rollback
Keep BLUE deployable while GREEN is developed. Remove GREEN external-action authority first, return routing/scheduling/publishing authority to BLUE, then verify BLUE health. Migrations remain backward-compatible until rollback is retired. No destructive production-state migration without tested backup/restore.

This Vault preserves code references, architecture and procedure. It cannot contain provider credentials or guarantee future third-party compatibility. Real disaster-recovery testing is mandatory.