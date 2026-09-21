# Current Stable MUBA System

## Stable recovery anchor
Repository: MUBA-RH/MUBA
Stable main SHA captured by this Vault: `602ebffe23de7373e7ee513af33dea219fe6deba`
Default production branch: main

This Vault branch was refreshed from that stable source tree and then received passive documentation only.

## Current production surfaces

### Website
Root `index.html` is the GitHub Pages website. Official MUBA links include X, Telegram and the GitHub Pages website. Website code is part of the snapshot.

### Telegram Bot API runtime
Primary integration: `telegram-bot/bot_mention.py`.
The bot is webhook-based. Guardian, Assistant, Studio and the layered MUBA brain are wired through this runtime.

### Private MUBA Assistant
The private Assistant supports:
- English
- Turkish
- Chinese
- Arabic
- Hindi

Current content includes identity/origin/difference/purpose/community/future guidance, Story Mode, MUBA Daily, Community Guide, Security Check, Studio access, CREATE → SHARE examples and other MUBA-specific natural interaction.

PR #91 added:
- paged Story Mode with previous/next navigation;
- distinct present-day topic context;
- expanded Community Guide;
- categorized development log;
- Studio-adjacent CREATE → SHARE content and copy actions;
- five-language parity for the new surfaces.

### Guardian
Guardian is the main-group security and management layer. Numeric DEV authority and the authorized main-group boundary are deterministic.

PR #92 synchronized START/STOP runtime behavior:
- #STOP sets the protected brain/group state to paused and Guardian non-command security/moderation processing stops;
- #START resumes protection;
- repeated START/STOP state transitions are tested;
- #SECURITY reports runtime protection ON/OFF consistently.

PR #93 improved DEV reporting:
- successful DEV management/manual actions do not create private report noise;
- real violations can include Telegram username/display name and numeric user ID;
- violation categories are stored in MUBA state;
- report language is stored in MUBA state;
- duplicate language-selection prompts are suppressed;
- violation history is browsable by category with previous/next controls.

Important persistence boundary: MUBA state defaults to in-memory storage unless `MUBA_MEMORY_FILE` is configured. Therefore any history stored through the state repository is durable across restarts only when a persistent repository path/storage is actually configured and verified.

### MUBA Studio
Studio remains the creation/media surface. It is not an authority source for CA, identity, DEV authority or security truth.

### Layered brain
`muba_brain.py` is the stable adapter.
`muba_core/` owns deterministic coordination and decision logic.
`layers/` contains specialist policy/semantic layers.
`state/` contains repository abstractions.

### DEV translation systems
The repository contains:
- the earlier DEV MTProto translator path;
- the isolated Android V3 translation path.

These are DEV workflow tools, not replacements for Guardian or Assistant.

### Android V3
`android-v3/` and related docs/workflows preserve the Android user-client translation architecture. GitHub Actions can build the standalone APK without placing secrets in source.

### CI
`.github/workflows/telegram-bot-tests.yml` protects the Telegram runtime.
`.github/workflows/muba-v3-android-cloud-build.yml` builds/validates the isolated Android V3 client path.

## Operational limitations
- External provider credentials/settings are not stored in Vault.
- Some runtime state is memory-only unless persistent storage is configured.
- External APIs may fail independently.
- A Git snapshot cannot recreate account ownership or provider secrets.
- Repository state and live provider state must both be verified during recovery.
