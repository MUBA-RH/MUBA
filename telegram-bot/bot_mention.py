"""
MUBA Telegram Bot
Offline local-brain version.
No external AI service or API key is required.
"""

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from muba_brain import build_reply, contains_muba, detect_language


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("muba")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"MUBA is alive.")

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health server listening on port %s", port)
    server.serve_forever()


def start_health_thread():
    thread = threading.Thread(
        target=start_health_server,
        name="health-server",
        daemon=True,
    )
    thread.start()


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

    # Messages containing MUBA are always considered relevant.
    if contains_muba(text):
        return True

    chat = update.effective_chat

    if chat and chat.type == ChatType.PRIVATE:
        return True

    # Answer messages that directly reply to the bot.
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user

        if replied_user and replied_user.is_bot:
            return True

    # Answer direct mentions containing MUBA.
    entities = message.entities or []

    for entity in entities:
        if entity.type == "mention":
            mention = text[
                entity.offset: entity.offset + entity.length
            ].lower()

            if "muba" in mention:
                return True

    return False


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        "MUBA is here.\n\nWe Live Here Now. 🪶"
    )


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

    language = detect_language(text)

    response = build_reply(
        text,
        chat_id=chat_id,
        language=language,
    )

    if not response:
        return

    user_name = get_user_name(update)

    # Mention the person who started the MUBA topic.
    if (
        user_name
        and update.effective_chat
        and update.effective_chat.type != ChatType.PRIVATE
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


def main():
    start_health_thread()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    application.add_error_handler(error_handler)

    logger.info(
        "MUBA local-brain bot is starting."
    )

    logger.info(
        "External AI services are disabled."
    )

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
