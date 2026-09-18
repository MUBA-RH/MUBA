"""
MUBA Telegram Bot
Webhook-based local-brain version.
No external AI service or API key is required.
"""

import hashlib
import logging
import os

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from muba_brain import (
    build_reply,
    contains_muba,
    detect_language,
    detect_social_intent,
    is_authorized_group,
    get_assistant_language,
    set_assistant_language,
    clear_assistant_language,
    group_conversation_paused,
)
from assistant_mode import LANGS, TOPIC_LABELS, QUESTIONS, TEXT, guided_answer, group_event, assistant_relevant, answer_for_question, match_catalog
from human_catalog import match as match_human_catalog
from guardian import authorized_command, command_arg, inspect_message, is_control_attempt, is_guardian_group, is_dev, lockdown_enabled, set_lockdown, status_text, help_text, security_text


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("muba")

# Telegram Bot uses httpx internally. Its INFO request logs include the bot
# token in the request URL, so keep transport logging at WARNING or above.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.request").setLevel(logging.WARNING)

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
    message=update.effective_message
    if not message or not message.text: return False
    chat=update.effective_chat; text=message.text.strip()
    if chat and chat.type==ChatType.PRIVATE: return True
    if not chat or not is_guardian_group(chat.id): return False
    if is_control_attempt(text): return is_dev(update.effective_user.id if update.effective_user else None)
    return bool(group_event(text))


def language_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=f"lang:{code}")] for code,label in LANGS.items()])

def menu_keyboard(lang):
    labels=TOPIC_LABELS[lang]
    rows=[]
    for topic in ("origin","identity","difference","purpose","community","plan"):
        rows.append([InlineKeyboardButton(labels[topic],callback_data=f"topic:{topic}")])
    rows.append([InlineKeyboardButton(TEXT[lang]["language"],callback_data="language")])
    return InlineKeyboardMarkup(rows)

def topic_keyboard(lang,topic):
    rows=[]
    for i,(t,q) in enumerate(QUESTIONS[lang]):
        if t==topic: rows.append([InlineKeyboardButton(q,callback_data=f"q:{i}")])
    rows.append([InlineKeyboardButton(TEXT[lang]["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

async def show_language(update):
    msg=update.effective_message
    if msg: await msg.reply_text(TEXT["en"]["choose"],reply_markup=language_keyboard())


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message: return
    chat=update.effective_chat
    if not chat or chat.type!=ChatType.PRIVATE: return
    clear_assistant_language(update.effective_user.id)
    await show_language(update)

async def ca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message: return
    chat=update.effective_chat
    if chat and chat.type!=ChatType.PRIVATE and is_authorized_group(chat.id):
        await update.effective_message.reply_text("Soon.")
    elif chat and chat.type==ChatType.PRIVATE:
        lang=get_assistant_language(update.effective_user.id)
        if not lang: await show_language(update); return
        response=build_reply("What is the CA?",chat_id=chat.id,user_id=update.effective_user.id,language=lang)
        if response: await update.effective_message.reply_text(response)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q: return
    await q.answer()
    user_id=q.from_user.id; data=q.data or ""
    if data.startswith("lang:"):
        lang=data.split(":",1)[1]
        if set_assistant_language(user_id,lang):
            await q.edit_message_text(TEXT[lang]["menu"],reply_markup=menu_keyboard(lang))
        return
    lang=get_assistant_language(user_id)
    if not lang:
        await q.edit_message_text(TEXT["en"]["choose"],reply_markup=language_keyboard()); return
    if data=="language":
        clear_assistant_language(user_id); await q.edit_message_text(TEXT["en"]["choose"],reply_markup=language_keyboard()); return
    if data=="menu":
        await q.edit_message_text(TEXT[lang]["menu"],reply_markup=menu_keyboard(lang)); return
    if data.startswith("topic:"):
        topic=data.split(":",1)[1]
        await q.edit_message_text(TOPIC_LABELS[lang][topic],reply_markup=topic_keyboard(lang,topic)); return
    if data.startswith("q:"):
        i=int(data.split(":",1)[1]); answer=answer_for_question(lang,i)
        await q.edit_message_text(answer,reply_markup=topic_keyboard(lang,QUESTIONS[lang][i][0]))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message=update.effective_message; chat=update.effective_chat
    if not message or not message.text or not chat: return
    text=message.text.strip(); user=update.effective_user; user_id=user.id if user else None
    if chat.type==ChatType.PRIVATE:
        lang=get_assistant_language(user_id)
        if not lang:
            await show_language(update); return
        catalog_index=match_catalog(lang,text)
        if catalog_index is not None:
            await message.reply_text(answer_for_question(lang,catalog_index),disable_web_page_preview=True,reply_markup=menu_keyboard(lang)); return
        human_answer=match_human_catalog(lang,text)
        if human_answer:
            await message.reply_text(human_answer,disable_web_page_preview=True,reply_markup=menu_keyboard(lang)); return
        if not assistant_relevant(text):
            await message.reply_text(TEXT[lang]["outside"],reply_markup=menu_keyboard(lang)); return
        response=build_reply(text,chat_id=chat.id,language=lang,user_id=user_id)
        if response: await message.reply_text(response,disable_web_page_preview=True,reply_markup=menu_keyboard(lang))
        return
    if not is_guardian_group(chat.id): return
    cmd=authorized_command(chat.id,user_id,text)
    if cmd:
        if cmd in ("#START","#STOP"):
            build_reply(cmd,chat_id=chat.id,language=detect_language(text),user_id=user_id)
            response="MUBA DEV IS HERE 🎙️" if cmd=="#STOP" else "MUBA COMMUNITY 🔥"
            await message.reply_text(response,disable_web_page_preview=True)
            return
        if cmd in ("#GUARDIAN","#STATUS"):
            await message.reply_text(status_text(group_conversation_paused(chat.id))); return
        if cmd=="#HELP":
            await message.reply_text(help_text()); return
        if cmd=="#SECURITY":
            await message.reply_text(security_text()); return
        if cmd=="#LOCKDOWN":
            set_lockdown(True); await message.reply_text("🛡️ GUARDIAN — LOCKDOWN"); return
        if cmd=="#NORMAL":
            set_lockdown(False); await message.reply_text("🛡️ GUARDIAN — NORMAL"); return
        target=message.reply_to_message
        try:
            if cmd=="#DELETE":
                if target: await target.delete(); await message.reply_text("🛡️ Deleted.")
                return
            if cmd=="#WARN":
                if target and target.from_user: await message.reply_text("⚠️ GUARDIAN warning for "+(target.from_user.mention_html()),parse_mode="HTML")
                return
            if cmd in ("#MUTE","#UNMUTE","#BAN"):
                if not target or not target.from_user: await message.reply_text("Reply to a user's message with "+cmd+"."); return
                tid=target.from_user.id
                if is_dev(tid): await message.reply_text("🛡️ DEV is protected."); return
                if cmd=="#BAN": await context.bot.ban_chat_member(chat.id,tid); await message.reply_text("🛡️ User banned."); return
                from telegram import ChatPermissions
                perms=ChatPermissions.no_permissions() if cmd=="#MUTE" else ChatPermissions.all_permissions()
                await context.bot.restrict_chat_member(chat.id,tid,permissions=perms)
                await message.reply_text("🛡️ User "+("muted." if cmd=="#MUTE" else "unmuted.")); return
            if cmd=="#UNBAN":
                arg=command_arg(text)
                if arg.lstrip("-").isdigit(): await context.bot.unban_chat_member(chat.id,int(arg)); await message.reply_text("🛡️ User unbanned.")
                else: await message.reply_text("Use: #UNBAN <user_id>")
                return
        except Exception:
            logger.exception("Guardian moderation action failed")
            await message.reply_text("🛡️ Guardian action could not be completed. Check bot admin permissions.")
            return
    if is_control_attempt(text):
        try:
            await message.delete()
        except Exception:
            logger.exception("Guardian could not delete unauthorized control message")
        return
    guardian_event=inspect_message(chat.id,user_id,text)
    if guardian_event:
        if guardian_event.get("action")=="warn": await message.reply_text(guardian_event["text"])
        return
    event=group_event(text)
    if not event: return
    if event=="assistant_redirect":
        username=context.bot.username
        button=InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Open MUBA Assistant",url=f"https://t.me/{username}?start=assistant")]])
        await message.reply_text("MUBA Assistant can answer that. Open the bot to explore MUBA.",reply_markup=button)
        return
    if event=="fake_ca":
        await message.reply_text("🚨 Fake CA warning. Do not trust unofficial contract addresses.")
        return
    if event=="ca":
        await message.reply_text("Soon."); return
    response=build_reply(text,chat_id=chat.id,language=detect_language(text),user_id=user_id)
    if response: await message.reply_text(response,disable_web_page_preview=True)


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

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ca", ca_command))
    application.add_handler(CallbackQueryHandler(callback_handler))

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
