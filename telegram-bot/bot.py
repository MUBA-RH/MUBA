import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from muba_brain import build_reply

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
log = logging.getLogger("muba.bot")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    reply = build_reply(
        "muba nedir",
        chat_id=update.effective_chat.id if update.effective_chat else 0,
        user_id=update.effective_user.id if update.effective_user else None,
    )
    await update.message.reply_text(reply or "MUBA.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("MUBA online.")


async def ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    reply = build_reply(
        "CA",
        chat_id=update.effective_chat.id if update.effective_chat else 0,
        user_id=update.effective_user.id if update.effective_user else None,
    )
    await update.message.reply_text(reply or "CA coming soon.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text.strip()
    if not user_text:
        return
    chat = update.effective_chat
    user = update.effective_user
    reply = build_reply(
        user_text,
        chat_id=chat.id if chat else 0,
        user_id=user.id if user else None,
    )
    if reply:
        await update.message.reply_text(reply)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("bot error: %s", context.error)


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("ca", ca))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
