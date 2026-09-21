# MUBA Module Registry

This file maps the complete current source snapshot. It is a preservation index, not a refactor request.

## Public website
- index.html
- GitHub Pages public MUBA website.

## Telegram Bot API runtime
- telegram-bot/bot_mention.py — webhook integration, routing and feature wiring.
- telegram-bot/webhook.py — webhook compatibility/transport surface.
- telegram-bot/bot.py — legacy/compatibility transport surface where retained.

## Guardian
- telegram-bot/guardian.py — numeric DEV authority, group security, control commands and moderation policy.

## Assistant
- telegram-bot/assistant_mode.py
- telegram-bot/assistant_extras.py
- telegram-bot/human_catalog.py
- telegram-bot/human_conversation_pack.py
- telegram-bot/natural_chat.py
- telegram-bot/conversation_continuity.py
- telegram-bot/muba_daily.py
- telegram-bot/system_transparency.py
- telegram-bot/system_notes.py

## Studio
- telegram-bot/muba_studio.py

## Brain/core/state
- telegram-bot/muba_brain.py — stable public adapter.
- telegram-bot/muba_core/* — deterministic coordinator, decision engine, operations and contracts.
- telegram-bot/layers/* — specialist authority/security/identity/knowledge/context/social/risk/etc layers.
- telegram-bot/state/* — state repository abstraction.

## Translation
- telegram-bot/dev_mtproto_translator.py — DEV MTProto translation path.
- telegram-bot/requirements-translator.txt — translator dependencies.

## Android V3
- android-v3/* — isolated Telegram Android translation/send helpers and build scripts.
- docs/MUBA_DEV_TRANSLATOR_V3_*.md — architecture/build documentation.
- .github/workflows/muba-v3-android-cloud-build.yml — GitHub cloud APK build.

## CI/tests
- .github/workflows/telegram-bot-tests.yml
- telegram-bot/tests/*
- telegram-bot/test_muba_brain.py

## Knowledge/history/source artifacts
- codex-input/*
- telegram-bot/data/*
- legacy MUBA brain/source notes under telegram-bot/

Do not assume legacy/source artifacts are runtime dependencies. Verify imports and tests before modifying or removing anything.

## Integration boundary
Guardian owns main-group security.
Assistant owns private MUBA interaction.
Studio owns media/content creation.
Android V3 owns the isolated DEV user-client translation workflow.
None of these should silently absorb another module's authority.
