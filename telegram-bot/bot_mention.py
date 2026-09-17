"""
MUBA Telegram Bot
Webhook-based local-brain version.
No external AI service or API key is required.
"""

import hashlib
import logging
import os

from aiohttp import web
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from muba_brain import (
    build_reply,
    contains_muba,
    detect_language,
    detect_social_intent,
)


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("muba")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

PORT = int(os.getenv("PORT", "10000"))

EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not EXTERNAL_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is not available.")

WEBHOOK_SECRET = os.getenv("MUBA_WEBHOOK_SECRET")

if not WEBHOOK_SECRET:
    WEBHOOK_SECRET = hashlib.sha256(
        TOKEN.encode("utf-8")
    ).hexdigest()

WEBHOOK_PATH = f"/telegram/{WEBHOOK_SECRET}"


def get_user_name(update: Update) -> str:
    user = update.effective_user

    if not user:
        return ""

    if user.username:
        return f"@{user.username}"

    return user.first_name or ""


def should_answer(update: Update) -> bool:
    message = update.effective_message

    if not message or not message.text:
        return False

    text = message.text.strip()

    if not text:
        return False

    # Protected hash commands must reach the brain, where numeric Founder ID
    # and authorized-group checks decide whether they have any effect.
    if text in {"#STOP", "#START"}:
        return True

    if contains_muba(text):
        return True

    chat = update.effective_chat

    if chat and chat.type == ChatType.PRIVATE:
        return True

    # Plain group greetings must reach the local brain even
    # when MUBA is not mentioned.
    social_intent = detect_social_intent(text)

    if social_intent in {"greeting", "gm", "gn"}:
        return True

    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user

        if replied_user and replied_user.is_bot:
            return True

    entities = message.entities or []

    for entity in entities:
        if entity.type == "mention":
            mention = text[
                entity.offset:entity.offset + entity.length
            ].lower()

            if "muba" in mention:
                return True

    return False


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    user_id = update.effective_user.id if update.effective_user else None
    response = build_reply(
        "/start",
        chat_id=chat_id,
        language=detect_language(update.effective_message.text or ""),
        user_id=user_id,
    )
    if response:
        await update.effective_message.reply_text(response)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if not message or not message.text:
        return

    if not should_answer(update):
        return

    text = message.text.strip()

    chat_id = (
        update.effective_chat.id
        if update.effective_chat
        else 0
    )

    user = update.effective_user
    user_id = user.id if user else None

    language = detect_language(text)

    response = build_reply(
        text,
        chat_id=chat_id,
        language=language,
        user_id=user_id,
    )

    if not response:
        return

    user_name = get_user_name(update)

    if (
        user_name
        and update.effective_chat
        and update.effective_chat.type != ChatType.PRIVATE
        and text not in {"#STOP", "#START"}
    ):
        response = f"{user_name} — {response}"

    try:
        await message.reply_text(
            response,
            disable_web_page_preview=True,
        )

    except Exception:
        logger.exception(
            "Failed to send Telegram message."
        )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Telegram update error: %s",
        context.error,
    )


async def health_handler(request: web.Request):
    return web.Response(
        text="MUBA is alive.",
        content_type="text/plain",
    )


async def webhook_handler(
    request: web.Request,
):
    application = request.app["telegram_application"]

    try:
        data = await request.json()

        update = Update.de_json(
            data=data,
            bot=application.bot,
        )

        await application.update_queue.put(update)

        return web.Response(
            text="OK",
            status=200,
        )

    except Exception:
        logger.exception(
            "Failed to process webhook update."
        )

        return web.Response(
            text="Bad Request",
            status=400,
        )


async def start_webhook_server():
    application = (
        Application.builder()
        .token(TOKEN)
        .updater(None)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    application.add_error_handler(
        error_handler
    )

    webhook_url = (
        f"{EXTERNAL_URL}{WEBHOOK_PATH}"
    )

    logger.info(
        "Initializing MUBA webhook application."
    )

    await application.initialize()
    await application.start()

    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    logger.info(
        "MUBA webhook configured successfully."
    )

    logger.info(
        "External AI services are disabled."
    )

    app = web.Application()

    app["telegram_application"] = application

    app.router.add_get(
        "/",
        health_handler,
    )

    app.router.add_get(
        "/health",
        health_handler,
    )

    app.router.add_post(
        WEBHOOK_PATH,
        webhook_handler,
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT,
    )

    await site.start()

    logger.info(
        "MUBA webhook server listening on port %s",
        PORT,
    )

    logger.info(
        "MUBA is live."
    )

    try:
        await asyncio_forever()

    finally:
        logger.info(
            "Stopping MUBA application."
        )

        await runner.cleanup()

        await application.stop()
        await application.shutdown()


async def asyncio_forever():
    import asyncio

    await asyncio.Event().wait()


def main():
    import asyncio

    asyncio.run(
        start_webhook_server()
    )


if __name__ == "__main__":
    main()
