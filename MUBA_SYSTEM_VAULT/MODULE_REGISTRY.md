# Module Registry

This registry maps the preserved system; it is not a refactor request.

- Website — index.html — public GitHub Pages surface.
- Telegram integration — telegram-bot/bot_mention.py — webhook app, routing, Guardian/Assistant/Studio wiring.
- Guardian — telegram-bot/guardian.py — DEV authority, group security and moderation.
- Assistant — assistant_mode.py, human_catalog.py, natural_chat.py, muba_daily.py, assistant_extras.py — five-language private MUBA interaction.
- Studio — muba_studio.py — media UI, quota and external image-generation integration.
- Brain adapter — muba_brain.py — stable API into the layered local system.
- Core registry — muba_core/registry.py — specialist layer discovery/loading.
- Specialist layers — telegram-bot/layers/* — authority, identity, security, knowledge and semantic/policy functions.
- State abstraction — telegram-bot/state/*.
- Runtime dependencies — telegram-bot/requirements.txt.
- CI — .github/workflows/telegram-bot-tests.yml.
- Source/legacy corpus — codex-input/* and selected telegram-bot/data files; do not assume every historical artifact is live.

Authority boundaries: DEV authority is deterministic. Guardian owns main-group security. Assistant owns private MUBA interaction. Studio owns media generation, not truth/security. Future Autonomy orchestrates these through explicit interfaces instead of silently absorbing them.

Before modifying a module, search all imports/references and tests. Handler ordering in bot_mention.py is an integration contract.