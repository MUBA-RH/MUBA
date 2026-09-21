# MUBA Module Registry

This file maps the current source snapshot. It is a preservation index, not a refactor request.

## Public website / history
- `index.html` — GitHub Pages public MUBA hub.
- `muba_history.json` — canonical append-only public development timeline.
- `scripts/check_web.py` — website static/JavaScript smoke validation.
- `scripts/check_continuity.py` — history continuity/change gate.

## Telegram Bot API runtime
- `telegram-bot/bot_mention.py` — webhook integration, routing and feature wiring.
- `telegram-bot/webhook.py` — webhook compatibility/transport surface where retained.
- `telegram-bot/bot.py` — legacy/compatibility transport surface where retained.

## Guardian
- `telegram-bot/guardian.py` — numeric DEV authority, group security, control commands and moderation policy.

## Assistant / history
- `telegram-bot/assistant_mode.py`
- `telegram-bot/assistant_extras.py`
- `telegram-bot/human_catalog.py`
- `telegram-bot/human_conversation_pack.py`
- `telegram-bot/natural_chat.py`
- `telegram-bot/conversation_continuity.py`
- `telegram-bot/muba_daily.py`
- `telegram-bot/muba_updates.py`
- `telegram-bot/muba_history.py`
- `telegram-bot/system_transparency.py`
- `telegram-bot/system_notes.py`

## Studio / Gallery
- `telegram-bot/muba_studio.py` — MUBA visual generation policy and Studio UI.
- `telegram-bot/muba_gallery.py` — shared archive, labels, persistence detection and moderation visibility.

## Brain/core/state
- `telegram-bot/muba_brain.py` — stable public adapter and persistent-state selection.
- `telegram-bot/muba_core/*` — deterministic coordinator, decision engine, operations and contracts.
- `telegram-bot/layers/*` — specialist authority/security/identity/knowledge/context/social/risk/etc layers.
- `telegram-bot/state/*` — state repository abstraction.

## Translation
- `telegram-bot/dev_mtproto_translator.py` — DEV MTProto translation path.
- `telegram-bot/requirements-translator.txt` — translator dependencies.

## Android V3
- `android-v3/*` — isolated Telegram Android translation/send helpers and build scripts.
- `docs/MUBA_DEV_TRANSLATOR_V3_*.md` — architecture/build documentation.
- `.github/workflows/muba-v3-android-cloud-build.yml` — GitHub cloud APK build.

## CI / operational docs
- `.github/workflows/telegram-bot-tests.yml`
- `.github/workflows/muba-continuity-gate.yml`
- `.github/workflows/muba-web-smoke.yml`
- `telegram-bot/tests/*`
- `docs/MUBA_CONTINUITY.md`
- `docs/MUBA_GALLERY_STORAGE.md`
- `docs/STABLE_RELEASE_CHECKLIST.md`
- `README.md`

## Knowledge/history/source artifacts
- `codex-input/*`
- `telegram-bot/data/*`
- retained legacy MUBA brain/source notes under `telegram-bot/`

Do not assume legacy/source artifacts are runtime dependencies. Verify imports and tests before modifying or removing anything.

## Integration boundary
Guardian owns main-group security.  
Assistant owns private MUBA interaction.  
Studio owns media creation.  
Gallery owns generated-media archive visibility.  
Canonical History owns verified public development chronology.  
Android V3 owns the isolated DEV user-client translation workflow.

None of these should silently absorb another module's authority.
