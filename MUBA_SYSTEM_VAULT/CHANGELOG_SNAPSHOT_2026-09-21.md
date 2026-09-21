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
Kept Telegram's native whole-chat translation entry point available in the exact MUBA dialog while preserving outgoing translate-before-send behavior.

### GitHub Android build
Workflow run #18 completed successfully and produced artifact `MUBA-V3-Android-APK`.

## Assistant / Guardian
### PR #91 — Assistant content evolution
Added paged Story Mode, distinct topic context, expanded Community Guide, Development Log and CREATE → SHARE across five languages.

### PR #92 — START/STOP synchronization
Aligned Guardian PAUSED/ACTIVE state with actual runtime protection and added repeated transition regression coverage.

### PR #93 — Violation history / quieter DEV reports
Added categorized violation history, report-language state and quieter successful DEV controls.

## Website / Studio
### PR #96 — Living MUBA website hub
Rebuilt the website into a living hub with dynamic knowledge, Development Log, Studio and MUBA TWT.

### PR #97 — Hero cleanup
Removed the mobile-heavy hero pillar cards.

### PR #98 — Direct Web Studio
Added protected direct Web Studio generation and same-page preview/download/TWT handoff.

### PR #99 / #100 — Web Studio production fixes
Corrected the Render service URL and backend startup import so Web Studio worked live.

### PR #101 — Text-free Studio default
Made Meme, Image, Sticker and Reaction outputs text-free unless visible writing is explicitly requested.

## Gallery / Update history
### PR #102 — MUBA Gallery and Assistant Updates
Added the shared Web/Telegram Gallery archive, manually scrollable public Gallery, short labels, format/source metadata, stronger Studio format guidance and central Assistant update/badge UI.

## Continuity
### PR #103 — MUBA Continuity
Added:
- canonical append-only `muba_history.json`;
- shared Website / Assistant / Daily history consumption;
- Continuity CI gate for future user-facing changes;
- Web Smoke CI;
- persistence-aware runtime state selection;
- DEV-only Gallery public/hidden/rejected moderation;
- exact dependency pinning from the known-green CI baseline;
- README, continuity standard and stable release/rollback documentation;
- broader runtime compile/regression coverage.

Superseded old PRs/issues were closed while preserving their history. Backup and Vault branches were not deleted.

## Snapshot result
Stable production main SHA after PR #103:

`cbdd3ddab1bce4d6deebebb2c77f4f9a7ed4cd33`

This Vault source snapshot includes that exact stable main state and remains passive/isolated from production.
