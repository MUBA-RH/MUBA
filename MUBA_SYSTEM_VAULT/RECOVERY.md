# Recovery Runbook
If DEV chooses RESTORE CURRENT MUBA: do not build V2.
1. Verify ownership/access to GitHub and required provider accounts.
2. Verify anchor d09aad85380ac87586e3656f796fc27967d75856 exists.
3. Inspect RELEASE_MANIFEST and files at that exact commit.
4. Restore/deploy from the immutable anchor or a branch from it; do not redesign during recovery.
5. Recreate required credentials only from the operator's secure provider/secret store; never commit them.
6. Run CI/tests.
7. Verify website and Telegram webhook/runtime.
8. Live-test Guardian, private Assistant, group #MUBA ASSISTANT and Studio as applicable.
9. Record discrepancies. Provider compatibility changes require a new isolated branch/test/PR.
10. Declare restored stable only after verification.

V2 rollback: keep BLUE deployable while GREEN is developed. Revoke GREEN external-action authority first, restore BLUE routing/authority, verify BLUE health, then repair GREEN. Database migrations remain backward-compatible until rollback is retired. No destructive production migration without tested backup/restore.

This Vault preserves code context/procedure, not provider credentials and not a guarantee that future third-party APIs remain compatible.