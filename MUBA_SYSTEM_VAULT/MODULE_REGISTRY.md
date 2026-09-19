# Module Registry
Website: index.html — public site.
Integration: telegram-bot/bot_mention.py — webhook/router and module wiring.
Guardian: telegram-bot/guardian.py — group security and DEV authority.
Assistant: assistant_mode.py, human_catalog.py, natural_chat.py, muba_daily.py, assistant_extras.py.
Studio: muba_studio.py — media generation.
Brain adapter: muba_brain.py.
Core registry: muba_core/registry.py — specialist layer loading.
Layers: telegram-bot/layers/ — authority, identity, knowledge, security and semantic/policy functions.
State: telegram-bot/state/ — current state abstractions where imported.
Dependencies: telegram-bot/requirements.txt.
CI: .github/workflows/telegram-bot-tests.yml.
Legacy/source material: codex-input/ and selected data artifacts; do not assume every historical artifact is live.

Authority boundaries: Guardian owns group security; Assistant owns private MUBA interaction; Studio owns media generation, not truth/security; future Autonomy orchestrates through explicit interfaces and must not silently absorb these responsibilities.