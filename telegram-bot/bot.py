"""Legacy webhook-handler compatibility module backed by the local brain.

Production starts ``bot_mention.py``. This module remains for ``webhook.py``
compatibility and intentionally contains no external generative-AI client.
"""
from __future__ import annotations

import logging
import os

from muba_brain import build_reply, detect_language

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
logger = logging.getLogger("muba.legacy_transport")


async def _reply(update, text: str) -> None:
    message = update.effective_message
    if not message:
        return
    chat_id = update.effective_chat.id if update.effective_chat else 0
    user_id = update.effective_user.id if update.effective_user else None
    response = build_reply(text, chat_id=chat_id, user_id=user_id, language=detect_language(text))
    if response:
        await message.reply_text(response, disable_web_page_preview=True)


async def start(update, context):
    await _reply(update, "/start")


async def status(update, context):
    await _reply(update, "MUBA status?")


async def ca(update, context):
    await _reply(update, "What is the CA?")


async def handle_message(update, context):
    message = update.effective_message
    if message and message.text:
        await _reply(update, message.text.strip())


async def error_handler(update, context):
    logger.error("Telegram update error: %s", context.error)
