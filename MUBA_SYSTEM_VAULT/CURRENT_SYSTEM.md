# Current Stable MUBA System

## Stable recovery anchor
Repository: MUBA-RH/MUBA  
Stable main SHA captured by this Vault: `ce5b1da6bd1881cff098bf33b941f641f45b5622`  
Default production branch: `main`

This Vault branch contains the source snapshot through PR #103 plus passive recovery/continuity documentation. Vault remains outside the production runtime.

## Current production surfaces

### Website
Root `index.html` is the GitHub Pages website. It is a living MUBA hub containing:
- public MUBA identity and knowledge;
- Development Log;
- Web Studio;
- MUBA Gallery;
- MUBA TWT;
- official X and Telegram links.

The website Development Log reads the canonical `muba_history.json` timeline.

### Telegram Bot API runtime
Primary integration: `telegram-bot/bot_mention.py`.

The webhook runtime wires Guardian, private Assistant, Studio, Gallery, MUBA Updates and the layered local brain.

### Private MUBA Assistant
Supports English, Turkish, Chinese, Arabic and Hindi.

Current content includes identity/origin/difference/purpose/community/future guidance, Story Mode, MUBA Daily, Community Guide, Security Check, Studio access, CREATE → SHARE and MUBA Updates.

MUBA Updates uses the same canonical history source as the website and Daily. Per-user seen-state controls NEW / UPDATED / IMPROVED / FIXED badges.

### Guardian
Guardian remains the main-group security and management layer with deterministic DEV authority and group boundary.

Current behavior includes:
- START/STOP runtime synchronization;
- fake/unverified CA, suspicious link, phishing/scam and flood controls;
- categorized violation history;
- private DEV reporting;
- report language state;
- successful routine DEV controls remaining quiet.

### MUBA Studio
Studio creates Meme, Image, Sticker and Reaction visuals through Web and Telegram surfaces.

Current rules:
- original MUBA identity guidance is preserved;
- visible text is disabled by default unless explicitly requested;
- Meme / Image / Sticker / Reaction use distinct quality guidance;
- public Web Studio has isolated daily quota controls;
- Telegram Studio remains available.

### MUBA Gallery
`telegram-bot/muba_gallery.py` is the shared archive layer for successful Web Studio and Telegram Studio creations.

Public metadata does not store Telegram IDs, usernames or raw prompts.

Visibility states:
- `public`
- `hidden`
- `rejected`

Only DEV can change Gallery visibility through the private Assistant moderation controls. Hidden/rejected records remain preserved but are not publicly listed or served.

### Canonical MUBA History
`muba_history.json` is the single append-only user-facing development timeline.

Consumers:
- Website Development Log;
- Assistant MUBA Updates;
- MUBA Daily Development Log / Updates.

The Continuity CI gate fails user-facing PRs that omit a new history record and rejects silent rewriting/removal of established history entries.

### Runtime state / persistence
`telegram-bot/muba_brain.py` uses:
1. explicit `MUBA_MEMORY_FILE`;
2. a state file beside configured `MUBA_GALLERY_DIR`;
3. mounted Render `/var/data` when detected;
4. in-memory fallback.

`/health/state` exposes only persistence/backend booleans, not filesystem paths.

Persistent storage must still be verified in the live deployment; source support alone does not prove provider disk configuration.

### Layered brain
`muba_brain.py` is the stable adapter.  
`muba_core/` owns deterministic coordination and decision logic.  
`layers/` contains specialist policy/semantic layers.  
`state/` contains repository abstractions.

### DEV translation / Android V3
Earlier MTProto translator and isolated Android V3 translation paths remain separate from Guardian and Assistant.

Android V3 build architecture and cloud build workflow remain preserved. No API hash, session, phone, 2FA, signing secret or bot credential belongs in Vault.

### CI
Current quality surfaces include:
- `.github/workflows/telegram-bot-tests.yml`;
- `.github/workflows/muba-continuity-gate.yml`;
- `.github/workflows/muba-web-smoke.yml`;
- `.github/workflows/muba-v3-android-cloud-build.yml`.

Runtime dependencies are pinned to the known-green package versions captured by PR #103.

## Operational limitations
- Provider credentials/settings are not stored in Vault.
- Persistent runtime behavior depends on provider storage actually being mounted/configured.
- External APIs may fail independently.
- A Git snapshot cannot recreate account ownership or provider secrets.
- GitHub branch protection/rulesets require repository administration and must be verified independently.
