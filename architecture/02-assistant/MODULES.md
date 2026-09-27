# 02 — ASSISTANT

Private Telegram assistant and user interaction domain.

## Modules
- telegram-ui — menus, callbacks, private-chat routing
- ask-muba — assistant Q&A mode
- conversation — natural chat and continuity
- camera — MUBA Camera intake/edit workflow
- knowledge-access — assistant-facing knowledge retrieval
- daily — daily assistant content
- news — verified news surface
- price — market-price surface
- human-conversation — catalog/conversation packs

## Current implementation map
- telegram-bot/bot.py
- telegram-bot/bot_mention.py
- telegram-bot/assistant_mode.py
- telegram-bot/assistant_extras.py
- telegram-bot/natural_chat.py
- telegram-bot/muba_camera.py
- telegram-bot/muba_daily.py
- telegram-bot/muba_news.py
- telegram-bot/muba_price.py
- telegram-bot/human_*.py
