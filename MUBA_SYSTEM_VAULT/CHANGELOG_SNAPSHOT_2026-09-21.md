# MUBA Stable Snapshot Changelog — 2026-09-21

This file records major GitHub-visible changes included in the stable snapshot captured by this Vault.

## DEV Translator / Android
### PR #79 — Persistent V2 chat mode
Made DEV translation easier by selecting a destination once and then typing Turkish without repeatedly invoking an inline-bot prefix.

### PR #80 — Official-channel lock
Restricted V2 DEV translation to the official MUBA Telegram channel numeric ID and failed closed elsewhere.

### PR #89 — Android dialog normalization
Corrected Android V3 dialog-ID comparison.

### PR #90 — Native whole-chat translation preservation
Kept Telegram's native whole-chat translation entry point available in the exact MUBA dialog while preserving the outgoing translate-before-send behavior and normal behavior in other dialogs.

### GitHub Android build
Workflow run #18 completed successfully and produced artifact `MUBA-V3-Android-APK`.

## Assistant
### PR #91 — Assistant content evolution
Added paged Story Mode, distinct topic context, expanded Community Guide, persistent-category development-log UI, and CREATE → SHARE content/copy actions across five languages.

## Guardian
### PR #92 — START/STOP protection synchronization
Aligned Guardian PAUSED/ACTIVE state with actual runtime protection and added repeated transition regression coverage.

### PR #93 — Violation history / quieter DEV reports
Stopped successful DEV management/manual actions from generating report noise. Added richer violation identity details, categorized violation history, report-language state and duplicate language-prompt suppression.

## Snapshot result
Stable main SHA after PR #93:
`602ebffe23de7373e7ee513af33dea219fe6deba`

This Vault refresh was branched from that exact SHA.
