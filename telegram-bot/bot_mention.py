"""
MUBA Telegram Bot
Webhook-based local-brain version.
No external AI service or API key is required.
"""

import hashlib
import logging
import json
import os
import time
from collections import OrderedDict
from datetime import datetime
from zoneinfo import ZoneInfo

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    InlineQueryHandler,
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
from natural_chat import match as match_natural_chat
from human_conversation_pack import reply as match_human_conversation
from conversation_continuity import reply as continuity_reply, remember_assistant_turn, clear as clear_conversation
from muba_daily import DAILY_LABELS, daily_text
from assistant_extras import LABELS as EXTRA_LABELS, STORY, LAB, GUIDE, SECURITY_PROMPT, security_check
from system_transparency import TRANSPARENCY_LABELS, TRANSPARENCY_NAV, TRANSPARENCY_PAGES
from system_notes import EXTRA_TRANSPARENCY_PAGES, TRANSLATOR_NOTE_LABELS, TRANSLATOR_NOTE_TEXT

for _lang, _pages in EXTRA_TRANSPARENCY_PAGES.items():
    TRANSPARENCY_PAGES[_lang].extend(_pages)
from muba_studio import REFERENCE_URL, clean_prompt, consume, remaining, render_meme, studio_html, validate_init_data, ai_configured, ai_endpoint, ai_payload, is_dev, studio_token, validate_studio_token
from guardian import DEV_ID, authorized_command, command_arg, inspect_message, is_control_attempt, is_guardian_group, is_dev, lockdown_enabled, set_lockdown, status_text, help_text, security_text


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("muba")

# Short-lived generated Studio outputs. Keys are random and unguessable;
# content is intentionally ephemeral and resets with the service.
_STUDIO_OUTPUTS = {}

# Telegram may redeliver the same webhook update/message. Keep a bounded,
# short-lived set of message identities so one Telegram message is handled once.
_PROCESSED_MESSAGES = OrderedDict()
_PROCESSED_MESSAGE_TTL = 21600
_PROCESSED_MESSAGE_MAX = 4096
_ASSISTANT_DAILY_LIMIT = 7
_ASSISTANT_CALL_INTERVAL = 7200
_ASSISTANT_CALLS = {}
_ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")


def _claim_message(update: Update) -> bool:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return True
    message_id = getattr(message, "message_id", None)
    if message_id is None:
        return True
    now = time.monotonic()
    cutoff = now - _PROCESSED_MESSAGE_TTL
    while _PROCESSED_MESSAGES:
        _, seen_at = next(iter(_PROCESSED_MESSAGES.items()))
        if seen_at >= cutoff:
            break
        _PROCESSED_MESSAGES.popitem(last=False)
    key = (chat.id, message_id)
    if key in _PROCESSED_MESSAGES:
        return False
    _PROCESSED_MESSAGES[key] = now
    _PROCESSED_MESSAGES.move_to_end(key)
    while len(_PROCESSED_MESSAGES) > _PROCESSED_MESSAGE_MAX:
        _PROCESSED_MESSAGES.popitem(last=False)
    return True

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


GUARDIAN_REPORT_LANGS=dict(LANGS)
_GUARDIAN_REPORT_LANGUAGE=None

GUARDIAN_REPORT_TEXT={
    "en":{"title":"🛡️ MUBA GUARDIAN — DEV REPORT","event":"Event","action":"Action","user":"User ID","strike":"Strike","detail":"Detail","choose":"🛡️ Guardian Report Language\nChoose the language for private DEV reports.","saved":"Guardian report language: English"},
    "tr":{"title":"🛡️ MUBA GUARDIAN — DEV RAPORU","event":"Olay","action":"İşlem","user":"Kullanıcı ID","strike":"İhlal sayısı","detail":"Detay","choose":"🛡️ Guardian Rapor Dili\nÖzel DEV raporlarının dilini seçin.","saved":"Guardian rapor dili: Türkçe"},
    "zh":{"title":"🛡️ MUBA GUARDIAN — DEV 报告","event":"事件","action":"操作","user":"用户 ID","strike":"违规次数","detail":"详情","choose":"🛡️ Guardian 报告语言\n选择私人 DEV 报告的语言。","saved":"Guardian 报告语言：中文"},
    "ar":{"title":"🛡️ MUBA GUARDIAN — تقرير DEV","event":"الحدث","action":"الإجراء","user":"معرّف المستخدم","strike":"عدد المخالفات","detail":"التفاصيل","choose":"🛡️ لغة تقارير Guardian\nاختر لغة تقارير DEV الخاصة.","saved":"لغة تقارير Guardian: العربية"},
    "hi":{"title":"🛡️ MUBA GUARDIAN — DEV रिपोर्ट","event":"घटना","action":"कार्रवाई","user":"यूज़र ID","strike":"उल्लंघन संख्या","detail":"विवरण","choose":"🛡️ Guardian रिपोर्ट भाषा\nनिजी DEV रिपोर्ट की भाषा चुनें।","saved":"Guardian रिपोर्ट भाषा: हिन्दी"},
}
GUARDIAN_EVENT_LABELS={
    "en":{"security":"Security","suspicious_link":"Suspicious link","flood":"Flood / spam","unauthorized_control":"Unauthorized command","guardian":"Guardian","management":"Guardian management","moderation":"Manual moderation","runtime":"Guardian runtime","fake_ca":"Fake / unverified CA","phishing":"Phishing","blocked_link":"Blocked external link","credential_theft":"Credential theft","warn":"Warning","delete":"Message deleted","mute":"User muted","unmute":"User unmuted","ban":"User banned","unban":"User unbanned","silent":"Silent block","info":"Information","start":"Guardian started","stop":"Guardian stopped","lockdown":"Lockdown enabled","normal":"Normal mode enabled","status":"Status viewed","help":"Help viewed","failed":"Action failed"},
    "tr":{"security":"Güvenlik","suspicious_link":"Şüpheli bağlantı","flood":"Flood / spam","unauthorized_control":"Yetkisiz komut","guardian":"Guardian","management":"Guardian yönetimi","moderation":"Manuel moderasyon","runtime":"Guardian çalışma durumu","fake_ca":"Sahte / doğrulanmamış CA","phishing":"Phishing","blocked_link":"Engellenen dış bağlantı","credential_theft":"Kimlik bilgisi hırsızlığı","warn":"Uyarı","delete":"Mesaj silindi","mute":"Kullanıcı susturuldu","unmute":"Kullanıcının susturması kaldırıldı","ban":"Kullanıcı yasaklandı","unban":"Kullanıcı yasağı kaldırıldı","silent":"Sessiz engelleme","info":"Bilgi","start":"Guardian başlatıldı","stop":"Guardian durduruldu","lockdown":"Lockdown modu açıldı","normal":"Normal moda geçildi","status":"Durum görüntülendi","help":"Yardım görüntülendi","failed":"İşlem başarısız"},
    "zh":{"security":"安全","suspicious_link":"可疑链接","flood":"刷屏 / 垃圾信息","unauthorized_control":"未授权命令","guardian":"Guardian","management":"Guardian 管理","moderation":"手动管理","runtime":"Guardian 运行状态","fake_ca":"虚假 / 未验证 CA","phishing":"网络钓鱼","blocked_link":"已拦截外部链接","credential_theft":"凭证窃取","warn":"警告","delete":"消息已删除","mute":"用户已禁言","unmute":"用户已解除禁言","ban":"用户已封禁","unban":"用户已解除封禁","silent":"静默拦截","info":"信息","start":"Guardian 已启动","stop":"Guardian 已停止","lockdown":"已启用 Lockdown","normal":"已启用正常模式","status":"已查看状态","help":"已查看帮助","failed":"操作失败"},
    "ar":{"security":"الأمان","suspicious_link":"رابط مشبوه","flood":"إغراق / سبام","unauthorized_control":"أمر غير مصرح","guardian":"Guardian","management":"إدارة Guardian","moderation":"إشراف يدوي","runtime":"حالة تشغيل Guardian","fake_ca":"CA مزيف / غير موثّق","phishing":"تصيد احتيالي","blocked_link":"رابط خارجي محظور","credential_theft":"سرقة بيانات الاعتماد","warn":"تحذير","delete":"تم حذف الرسالة","mute":"تم كتم المستخدم","unmute":"تم إلغاء كتم المستخدم","ban":"تم حظر المستخدم","unban":"تم إلغاء حظر المستخدم","silent":"حظر صامت","info":"معلومات","start":"تم تشغيل Guardian","stop":"تم إيقاف Guardian","lockdown":"تم تفعيل Lockdown","normal":"تم تفعيل الوضع العادي","status":"تم عرض الحالة","help":"تم عرض المساعدة","failed":"فشل الإجراء"},
    "hi":{"security":"सुरक्षा","suspicious_link":"संदिग्ध लिंक","flood":"फ्लड / स्पैम","unauthorized_control":"अनधिकृत कमांड","guardian":"Guardian","management":"Guardian प्रबंधन","moderation":"मैनुअल मॉडरेशन","runtime":"Guardian रनटाइम","fake_ca":"नकली / अप्रमाणित CA","phishing":"फ़िशिंग","blocked_link":"ब्लॉक किया गया बाहरी लिंक","credential_theft":"क्रेडेंशियल चोरी","warn":"चेतावनी","delete":"संदेश हटाया गया","mute":"यूज़र म्यूट किया गया","unmute":"यूज़र अनम्यूट किया गया","ban":"यूज़र बैन किया गया","unban":"यूज़र अनबैन किया गया","silent":"साइलेंट ब्लॉक","info":"जानकारी","start":"Guardian शुरू हुआ","stop":"Guardian रोका गया","lockdown":"Lockdown चालू","normal":"सामान्य मोड चालू","status":"स्थिति देखी गई","help":"सहायता देखी गई","failed":"कार्रवाई विफल"},
}

def guardian_report_language_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=f"guardian_lang:{code}")] for code,label in GUARDIAN_REPORT_LANGS.items()])

def language_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=f"lang:{code}")] for code,label in LANGS.items()])

def menu_keyboard(lang,user_id=None):
    labels=TOPIC_LABELS[lang]
    rows=[[InlineKeyboardButton(TRANSPARENCY_LABELS[lang],callback_data="transparency:0")]]
    for topic in ("origin","identity","difference","purpose","community","plan"):
        rows.append([InlineKeyboardButton(labels[topic],callback_data=f"topic:{topic}")])
    rows.append([InlineKeyboardButton(DAILY_LABELS[lang]["daily"],callback_data="daily")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["story"],callback_data="extra:story")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["lab"],callback_data="extra:lab")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["guide"],callback_data="extra:guide")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["security"],callback_data="extra:security")])
    rows.append([InlineKeyboardButton("🎭 MUBA Studio",web_app=WebAppInfo(url=EXTERNAL_URL.rstrip("/")+"/studio?uid="+str(user_id or 0)+"&st="+studio_token(user_id or 0,TOKEN)))])
    rows.append([InlineKeyboardButton(TRANSLATOR_NOTE_LABELS[lang],callback_data="translator_note")])
    rows.append([InlineKeyboardButton(TEXT[lang]["language"],callback_data="language")])
    return InlineKeyboardMarkup(rows)

def transparency_keyboard(lang,page):
    nav=TRANSPARENCY_NAV[lang]
    total=len(TRANSPARENCY_PAGES[lang])
    rows=[]
    pager=[]
    if page>0:
        pager.append(InlineKeyboardButton(nav["prev"],callback_data=f"transparency:{page-1}"))
    if page+1<total:
        pager.append(InlineKeyboardButton(nav["next"],callback_data=f"transparency:{page+1}"))
    if pager:
        rows.append(pager)
    rows.append([InlineKeyboardButton(nav["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def transparency_text(lang,page):
    pages=TRANSPARENCY_PAGES[lang]
    page=max(0,min(page,len(pages)-1))
    return f'{pages[page]}\n\n{TRANSPARENCY_NAV[lang]["page"]} {page+1}/{len(pages)}'

def daily_keyboard(lang):
    labels=DAILY_LABELS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels["x"],callback_data="daily:x")],
        [InlineKeyboardButton(labels["web"],callback_data="daily:web")],
        [InlineKeyboardButton(labels["telegram"],callback_data="daily:telegram")],
        [InlineKeyboardButton(labels["updates"],callback_data="daily:updates")],
        [InlineKeyboardButton(labels["back"],callback_data="menu")],
    ])

def extra_keyboard(lang,mode):
    labels=EXTRA_LABELS[lang]
    if mode=="story":
        rows=[[InlineKeyboardButton(f"📖 {i+1}/5",callback_data=f"story:{i}")] for i in range(5)]
    elif mode=="lab":
        rows=[
            [InlineKeyboardButton("😂 Meme",callback_data="lab:meme")],
            [InlineKeyboardButton("✍️ Tweet",callback_data="lab:tweet")],
            [InlineKeyboardButton("🖼️ Visual 16:9",callback_data="lab:visual")],
        ]
    elif mode=="guide":
        rows=[[InlineKeyboardButton(f"🧭 {i+1}/4",callback_data=f"guide:{i}")] for i in range(4)]
    else:
        rows=[]
    rows.append([InlineKeyboardButton(labels["back"],callback_data="menu")])
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
    clear_conversation(update.effective_user.id)
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
    if data.startswith("guardian_lang:"):
        if not is_dev(user_id): return
        lang=data.split(":",1)[1]
        if lang in GUARDIAN_REPORT_LANGS:
            global _GUARDIAN_REPORT_LANGUAGE
            _GUARDIAN_REPORT_LANGUAGE=lang
            await q.edit_message_text(GUARDIAN_REPORT_TEXT[lang]["saved"])
        return
    if data.startswith("lang:"):
        lang=data.split(":",1)[1]
        if set_assistant_language(user_id,lang):
            clear_conversation(user_id)
            await q.edit_message_text(TEXT[lang]["menu"],reply_markup=menu_keyboard(lang,user_id))
        return
    lang=get_assistant_language(user_id)
    if not lang:
        await q.edit_message_text(TEXT["en"]["choose"],reply_markup=language_keyboard()); return
    if data=="language":
        clear_assistant_language(user_id); clear_conversation(user_id); await q.edit_message_text(TEXT["en"]["choose"],reply_markup=language_keyboard()); return
    if data=="menu":
        await q.edit_message_text(TEXT[lang]["menu"],reply_markup=menu_keyboard(lang,user_id)); return
    if data.startswith("transparency:"):
        raw=data.split(":",1)[1]
        page=int(raw) if raw.isdigit() else 0
        page=max(0,min(page,len(TRANSPARENCY_PAGES[lang])-1))
        await q.edit_message_text(transparency_text(lang,page),reply_markup=transparency_keyboard(lang,page),disable_web_page_preview=True); return
    if data=="translator_note":
        await q.edit_message_text(TRANSLATOR_NOTE_TEXT[lang],reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXT[lang]["back"],callback_data="menu")]]),disable_web_page_preview=True); return
    if data=="daily":
        await q.edit_message_text(DAILY_LABELS[lang]["daily"],reply_markup=daily_keyboard(lang)); return
    if data.startswith("daily:"):
        section=data.split(":",1)[1]
        await q.edit_message_text(daily_text(lang,section),reply_markup=daily_keyboard(lang),disable_web_page_preview=True); return
    if data.startswith("extra:"):
        mode=data.split(":",1)[1]
        if mode=="security":
            context.user_data["muba_security_check"]=True
            await q.edit_message_text(SECURITY_PROMPT[lang],reply_markup=extra_keyboard(lang,"security")); return
        await q.edit_message_text(EXTRA_LABELS[lang][mode],reply_markup=extra_keyboard(lang,mode)); return
    if data.startswith("story:"):
        i=int(data.split(":",1)[1]); await q.edit_message_text(STORY[lang][i],reply_markup=extra_keyboard(lang,"story")); return
    if data.startswith("lab:"):
        kind=data.split(":",1)[1]; await q.edit_message_text(LAB[lang][kind],reply_markup=extra_keyboard(lang,"lab")); return
    if data.startswith("guide:"):
        i=int(data.split(":",1)[1]); await q.edit_message_text(GUIDE[lang][i],reply_markup=extra_keyboard(lang,"guide")); return
    if data.startswith("topic:"):
        topic=data.split(":",1)[1]
        await q.edit_message_text(TOPIC_LABELS[lang][topic],reply_markup=topic_keyboard(lang,topic)); return
    if data.startswith("q:"):
        i=int(data.split(":",1)[1]); answer=answer_for_question(lang,i)
        await q.edit_message_text(answer,reply_markup=topic_keyboard(lang,QUESTIONS[lang][i][0]))


async def _translate_tr_to_en(text):
    """Translate Turkish to English through the already configured Cloudflare Workers AI account."""
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID")
    token=os.getenv("CLOUDFLARE_API_TOKEN")
    if not account or not token:
        return None
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/meta/m2m100-1.2b"
    payload={"text":text,"source_lang":"tr","target_lang":"en"}
    headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url,json=payload,headers=headers,timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status!=200:
                    return None
                data=await response.json()
        result=data.get("result")
        if isinstance(result,dict):
            translated=result.get("translated_text") or result.get("translation")
            if translated:
                return str(translated).strip()
        if isinstance(result,list) and result:
            item=result[0]
            if isinstance(item,dict):
                translated=item.get("translated_text") or item.get("translation")
                if translated:
                    return str(translated).strip()
    except Exception:
        logger.exception("DEV inline translation failed")
    return None


async def dev_inline_translator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DEV-only Turkish→English inline translator; sends the selected result as the invoking user."""
    query=update.inline_query
    if not query or not is_dev(query.from_user.id):
        if query:
            await query.answer([],cache_time=1,is_personal=True)
        return
    # DEV UX: typing @MUBA_RH_AI_Bot <Turkish text> in any chat is
    # already Telegram inline mode. Translate the query directly so DEV only
    # needs to tap the returned English result. No "tr " prefix is required.
    # Non-DEV users are rejected above and retain the existing Studio path.
    source=" ".join((query.query or "").strip().split())[:2000]
    if not source:
        return
    translated=await _translate_tr_to_en(source)
    if not translated:
        await query.answer([],cache_time=1,is_personal=True)
        return
    result=InlineQueryResultArticle(
        id=hashlib.sha256((source+"\0"+translated).encode()).hexdigest()[:32],
        title="🇬🇧 "+translated[:120],
        description="MUBA DEV Translator — Turkish → English",
        input_message_content=InputTextMessageContent(message_text=translated),
    )
    await query.answer([result],cache_time=1,is_personal=True)


async def guardian_slash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Translate Telegram-native /guardian commands to the existing locked # command path."""
    message=update.effective_message
    chat=update.effective_chat
    user=update.effective_user
    if not message or not chat or not user or not is_guardian_group(chat.id):
        return
    raw=(message.text or "").strip()
    first,*rest=raw.split(maxsplit=1)
    name=first.split("@",1)[0].lstrip("/").upper()
    mapped="#"+name
    message.text=mapped+((" "+rest[0]) if rest else "")
    await handle_message(update,context)


async def assistant_group_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message=update.effective_message; chat=update.effective_chat; user=update.effective_user
    if not message or not message.text or not chat or chat.type==ChatType.PRIVATE or not user: return
    if not is_guardian_group(chat.id): return
    normalized=" ".join(message.text.strip().upper().split())
    if normalized!="#MUBA ASSISTANT": return
    if not _claim_message(update): return

    user_id=user.id
    if not is_dev(user_id):
        now=datetime.now(_ISTANBUL_TZ)
        today=now.date().isoformat()
        state=_ASSISTANT_CALLS.get(user_id)
        if not state or state["date"]!=today:
            state={"date":today,"count":0,"last":0.0}
            _ASSISTANT_CALLS[user_id]=state

        lang=get_assistant_language(user_id)
        if lang not in LANGS:
            code=(getattr(user,"language_code",None) or "en").lower()
            if code.startswith("tr"): lang="tr"
            elif code.startswith("zh"): lang="zh"
            elif code.startswith("ar"): lang="ar"
            elif code.startswith("hi"): lang="hi"
            else: lang="en"

        limit_text={
            "en":"You've reached your 7 MUBA Assistant calls for today. Your limit resets tomorrow.",
            "tr":"Bugünkü 7 MUBA Assistant çağrı hakkınızı kullandınız. Limitiniz yarın yenilenecek.",
            "zh":"您今天的 7 次 MUBA Assistant 呼叫次数已用完。额度将在明天重置。",
            "ar":"لقد استخدمت 7 مرات لاستدعاء MUBA Assistant اليوم. سيتم تجديد الحد غدًا.",
            "hi":"आप आज के 7 MUBA Assistant कॉल पूरे कर चुके हैं। आपकी सीमा कल रीसेट होगी।",
        }
        wait_text={
            "en":"Your next MUBA Assistant call will be available in {time}.",
            "tr":"Bir sonraki MUBA Assistant çağrınız {time} sonra kullanılabilir.",
            "zh":"您可以在 {time} 后再次呼叫 MUBA Assistant。",
            "ar":"يمكنك استدعاء MUBA Assistant مرة أخرى بعد {time}.",
            "hi":"आप अगली बार MUBA Assistant को {time} बाद बुला सकते हैं।",
        }
        if state["count"]>=_ASSISTANT_DAILY_LIMIT:
            await message.reply_text(limit_text[lang]); return
        elapsed=time.time()-state["last"] if state["last"] else _ASSISTANT_CALL_INTERVAL
        if elapsed<_ASSISTANT_CALL_INTERVAL:
            remaining_seconds=max(1,int(_ASSISTANT_CALL_INTERVAL-elapsed))
            hours,rem=divmod(remaining_seconds,3600); minutes=(rem+59)//60
            if minutes==60: hours+=1; minutes=0
            if lang=="tr": duration=(f"{hours} sa {minutes} dk" if minutes else f"{hours} sa")
            elif lang=="zh": duration=(f"{hours}小时{minutes}分钟" if minutes else f"{hours}小时")
            elif lang=="ar": duration=(f"{hours} س {minutes} د" if minutes else f"{hours} س")
            elif lang=="hi": duration=(f"{hours}घं {minutes}मि" if minutes else f"{hours}घं")
            else: duration=(f"{hours}h {minutes}m" if minutes else f"{hours}h")
            await message.reply_text(wait_text[lang].format(time=duration)); return
        state["count"]+=1
        state["last"]=time.time()

    username=context.bot.username
    button=InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Open MUBA Assistant",url=f"https://t.me/{username}?start=assistant")]])
    await message.reply_text("MUBA Assistant 🪶\nI'm here whenever you need me. Open MUBA Assistant below.",reply_markup=button)

async def _guardian_dev_report(context: ContextTypes.DEFAULT_TYPE, event: dict, user_id=None):
    """Best-effort localized private Guardian report to DEV; never block moderation."""
    try:
        global _GUARDIAN_REPORT_LANGUAGE
        if _GUARDIAN_REPORT_LANGUAGE not in GUARDIAN_REPORT_LANGS:
            await context.bot.send_message(chat_id=DEV_ID,text=GUARDIAN_REPORT_TEXT["en"]["choose"],reply_markup=guardian_report_language_keyboard())
            return
        lang=_GUARDIAN_REPORT_LANGUAGE
        ui=GUARDIAN_REPORT_TEXT[lang]
        labels=GUARDIAN_EVENT_LABELS[lang]
        kind=str(event.get("kind") or "guardian").casefold()
        subkind=str(event.get("subkind") or "").casefold()
        action=str(event.get("action") or "info").casefold()
        event_text=labels.get(kind,kind)
        if subkind:
            event_text += " / "+labels.get(subkind,subkind)
        lines=[ui["title"],f'{ui["event"]}: {event_text}',f'{ui["action"]}: {labels.get(action,action)}']
        if user_id is not None: lines.append(f'{ui["user"]}: {user_id}')
        strike=event.get("strike")
        if strike is not None: lines.append(f'{ui["strike"]}: {strike}')
        detail=event.get("detail")
        if detail: lines.append(f'{ui["detail"]}: {detail}')
        await context.bot.send_message(chat_id=DEV_ID,text="\\n".join(lines))
    except Exception:
        logger.exception("Guardian DEV private report failed")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _claim_message(update):
        logger.info("Ignoring duplicate Telegram message delivery")
        return
    message=update.effective_message; chat=update.effective_chat
    if not message or not message.text or not chat: return
    text=message.text.strip(); user=update.effective_user; user_id=user.id if user else None
    if chat.type==ChatType.PRIVATE:
        lang=get_assistant_language(user_id)
        if not lang:
            await show_language(update); return
        if context.user_data.pop("muba_security_check",False):
            await message.reply_text(security_check(lang,text),disable_web_page_preview=True,reply_markup=menu_keyboard(lang,user_id)); return
        catalog_index=match_catalog(lang,text)
        if catalog_index is not None:
            response=answer_for_question(lang,catalog_index)
            remember_assistant_turn(user_id,lang,response)
            await message.reply_text(response,disable_web_page_preview=True); return
        continuity=continuity_reply(user_id,lang,text)
        if continuity:
            remember_assistant_turn(user_id,lang,continuity)
            await message.reply_text(continuity,disable_web_page_preview=True); return
        expanded_human=match_human_conversation(lang,text)
        if expanded_human:
            remember_assistant_turn(user_id,lang,expanded_human)
            await message.reply_text(expanded_human,disable_web_page_preview=True)
            return
        human_answer=match_human_catalog(lang,text)
        if human_answer:
            remember_assistant_turn(user_id,lang,human_answer)
            await message.reply_text(human_answer,disable_web_page_preview=True); return
        natural_answer=match_natural_chat(lang,text)
        if natural_answer:
            remember_assistant_turn(user_id,lang,natural_answer)
            await message.reply_text(natural_answer,disable_web_page_preview=True); return
        if not assistant_relevant(text):
            response=TEXT[lang]["outside"]
            remember_assistant_turn(user_id,lang,response)
            await message.reply_text(response); return
        response=build_reply(text,chat_id=chat.id,language=lang,user_id=user_id)
        if response:
            remember_assistant_turn(user_id,lang,response)
            await message.reply_text(response,disable_web_page_preview=True)
        return
    if not is_guardian_group(chat.id): return
    cmd=authorized_command(chat.id,user_id,text)
    if cmd:
        if cmd in ("#START","#STOP"):
            build_reply(cmd,chat_id=chat.id,language=detect_language(text),user_id=user_id)
            from telegram import ChatPermissions
            try:
                if cmd=="#STOP":
                    await context.bot.set_chat_permissions(chat.id,ChatPermissions.no_permissions())
                    response="MUBA DEV IS HERE 🎙️"
                else:
                    await context.bot.set_chat_permissions(chat.id,ChatPermissions(can_send_messages=True, can_send_other_messages=False, can_send_photos=False, can_send_videos=False, can_send_video_notes=False, can_send_voice_notes=False, can_send_audios=False, can_send_documents=False, can_send_polls=False, can_add_web_page_previews=False, can_invite_users=True, can_pin_messages=False, can_change_info=False, can_manage_topics=False), use_independent_chat_permissions=True)
                    response="MUBA COMMUNITY 🔥"
                await message.reply_text(response,disable_web_page_preview=True)
                await _guardian_dev_report(context,{"kind":"management","subkind":cmd.lstrip("#").casefold(),"action":cmd.lstrip("#").casefold()},user_id)
            except Exception:
                logger.exception("Guardian could not change group posting permissions")
                await message.reply_text("🛡️ Guardian could not change group permissions. Check bot admin permissions.")
                await _guardian_dev_report(context,{"kind":"runtime","subkind":cmd.lstrip("#").casefold(),"action":"failed","detail":"Grup izinleri değiştirilemedi."},user_id)
            return
        if cmd in ("#GUARDIAN","#STATUS"):
            await message.reply_text(status_text(group_conversation_paused(chat.id)))
            await _guardian_dev_report(context,{"kind":"management","subkind":cmd.lstrip("#").casefold(),"action":"status"},user_id)
            return
        if cmd=="#HELP":
            await message.reply_text(help_text())
            await _guardian_dev_report(context,{"kind":"management","subkind":"help","action":"help"},user_id)
            return
        if cmd=="#SECURITY":
            await message.reply_text(security_text())
            await _guardian_dev_report(context,{"kind":"management","subkind":"security","action":"security"},user_id)
            return
        if cmd=="#LOCKDOWN":
            set_lockdown(True)
            await message.reply_text("🛡️ GUARDIAN — LOCKDOWN")
            await _guardian_dev_report(context,{"kind":"management","subkind":"lockdown","action":"lockdown"},user_id)
            return
        if cmd=="#NORMAL":
            set_lockdown(False)
            await message.reply_text("🛡️ GUARDIAN — NORMAL")
            await _guardian_dev_report(context,{"kind":"management","subkind":"normal","action":"normal"},user_id)
            return
        target=message.reply_to_message
        try:
            if cmd=="#DELETE":
                if target:
                    await target.delete()
                    await message.reply_text("🛡️ Deleted.")
                    await _guardian_dev_report(context,{"kind":"moderation","subkind":"manual","action":"delete"},target.from_user.id if target.from_user else None)
                return
            if cmd=="#WARN":
                if target and target.from_user:
                    await message.reply_text("⚠️ GUARDIAN warning for "+target.from_user.mention_html(),parse_mode="HTML")
                    await _guardian_dev_report(context,{"kind":"moderation","subkind":"manual","action":"warn"},target.from_user.id)
                return
            if cmd in ("#MUTE","#UNMUTE","#BAN"):
                if not target or not target.from_user:
                    await message.reply_text("Reply to a user's message with "+cmd+".")
                    return
                tid=target.from_user.id
                if is_dev(tid):
                    await message.reply_text("🛡️ DEV is protected.")
                    return
                if cmd=="#BAN":
                    await context.bot.ban_chat_member(chat.id,tid)
                    await message.reply_text("🛡️ User banned.")
                    await _guardian_dev_report(context,{"kind":"moderation","subkind":"manual","action":"ban"},tid)
                    return
                from telegram import ChatPermissions
                perms=ChatPermissions.no_permissions() if cmd=="#MUTE" else ChatPermissions.all_permissions()
                await context.bot.restrict_chat_member(chat.id,tid,permissions=perms)
                await message.reply_text("🛡️ User "+("muted." if cmd=="#MUTE" else "unmuted."))
                await _guardian_dev_report(context,{"kind":"moderation","subkind":"manual","action":"mute" if cmd=="#MUTE" else "unmute"},tid)
                return
            if cmd=="#UNBAN":
                arg=command_arg(text)
                if arg.lstrip("-").isdigit():
                    tid=int(arg)
                    await context.bot.unban_chat_member(chat.id,tid)
                    await message.reply_text("🛡️ User unbanned.")
                    await _guardian_dev_report(context,{"kind":"moderation","subkind":"manual","action":"unban"},tid)
                else:
                    await message.reply_text("Use: #UNBAN <user_id>")
                return
        except Exception:
            logger.exception("Guardian moderation action failed")
            await message.reply_text("🛡️ Guardian action could not be completed. Check bot admin permissions.")
            await _guardian_dev_report(context,{"kind":"runtime","subkind":"moderation","action":"failed","detail":"Manuel Guardian işlemi tamamlanamadı."},user_id)
            return
    if is_control_attempt(text):
        try:
            await message.delete()
            await _guardian_dev_report(context,{"kind":"unauthorized_control","subkind":"command","action":"delete","detail":"Yetkisiz Guardian komut girişimi silindi."},user_id)
        except Exception:
            logger.exception("Guardian could not delete unauthorized control message")
            await _guardian_dev_report(context,{"kind":"runtime","subkind":"unauthorized_control","action":"failed","detail":"Yetkisiz komut mesajı silinemedi."},user_id)
        return
    guardian_event=inspect_message(chat.id,user_id,text)
    if guardian_event:
        action=guardian_event.get("action")
        if action=="warn":
            await message.reply_text(guardian_event["text"])
            await _guardian_dev_report(context,guardian_event,user_id)
        elif action=="delete":
            try:
                await message.delete()
                await context.bot.send_message(chat.id,guardian_event["text"])
                await _guardian_dev_report(context,guardian_event,user_id)
            except Exception:
                logger.exception("Guardian link deletion failed")
                await _guardian_dev_report(context,{"kind":"runtime","subkind":"link_deletion","action":"failed","detail":"Guardian bağlantı silme işlemi tamamlanamadı."},user_id)
        elif action in ("mute","ban"):
            try:
                # Always moderate the numeric Telegram ID attached to this exact message.
                # Never resolve a username/display name to choose a target.
                member=await context.bot.get_chat_member(chat.id,user_id)
                if getattr(member,"status",None) in ("administrator","creator","owner") or is_dev(user_id):
                    logger.warning("Guardian skipped automatic moderation for protected/admin user %s",user_id)
                    await _guardian_dev_report(context,{"kind":"security","subkind":"protected_user","action":"info","detail":"Otomatik moderasyon korunan/admin kullanıcı için uygulanmadı."},user_id)
                    return
                await message.delete()
                if action=="mute":
                    import time
                    from telegram import ChatPermissions
                    await context.bot.restrict_chat_member(
                        chat.id,user_id,
                        permissions=ChatPermissions.no_permissions(),
                        until_date=int(time.time())+int(guardian_event.get("mute_seconds",1800)),
                    )
                else:
                    await context.bot.ban_chat_member(chat.id,user_id,revoke_messages=True)
                await context.bot.send_message(chat.id,guardian_event["text"])
                await _guardian_dev_report(context,guardian_event,user_id)
            except Exception:
                logger.exception("Guardian automatic moderation failed")
                await _guardian_dev_report(context,{"kind":"runtime","subkind":"automatic_moderation","action":"failed","detail":"Otomatik Guardian moderasyonu tamamlanamadı."},user_id)
        return
    event=group_event(text)
    if not event: return
    if event=="assistant_redirect":
        return
    if event=="fake_ca":
        await message.reply_text("🚨 Fake CA warning. Do not trust unofficial contract addresses.")
        await _guardian_dev_report(context,{"kind":"security","subkind":"fake_ca","action":"warn"},user_id)
        return
    if event=="ca":
        await message.reply_text("Soon."); return
    response=build_reply(text,chat_id=chat.id,language=detect_language(text),user_id=user_id)
    if response: await message.reply_text(response,disable_web_page_preview=True)


async def inline_studio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.inline_query
    if not q or not q.from_user: return
    if is_dev(q.from_user.id): return
    prompt=clean_prompt(q.query)
    if not prompt: return
    from urllib.parse import urlencode
    url=EXTERNAL_URL.rstrip("/")+"/studio/render?"+urlencode({"p":prompt,"k":"meme"})
    rid=hashlib.sha256((str(q.from_user.id)+prompt).encode()).hexdigest()[:32]
    await q.answer([InlineQueryResultPhoto(id=rid,photo_url=url,thumbnail_url=REFERENCE_URL,caption=prompt)],cache_time=1,is_personal=True)

async def studio_page_handler(request: web.Request):
    return web.Response(text=studio_html(EXTERNAL_URL),content_type="text/html")

async def _studio_reference(request: web.Request):
    async with request.app["http_session"].get(REFERENCE_URL,timeout=15) as response:
        if response.status != 200: raise RuntimeError("MUBA reference unavailable")
        return await response.read()

async def studio_generate_handler(request: web.Request):
    try: data=await request.json()
    except Exception: return web.json_response({"error":"Invalid request."},status=400)
    user=validate_init_data(str(data.get("initData","")),TOKEN) or validate_studio_token(data.get("uid"),data.get("studioToken"),TOKEN)
    if not user or not user.get("id"): return web.json_response({"error":"Open Studio from Telegram."},status=401)
    uid=int(user["id"]); prompt=clean_prompt(str(data.get("prompt",""))); kind=str(data.get("kind","meme"))
    if not prompt: return web.json_response({"error":"Write something for MUBA."},status=400)
    if not is_dev(uid) and remaining(uid)<=0: return web.json_response({"error":"Daily limit reached — 3/3."},status=429)
    if not ai_configured(): return web.json_response({"error":"MUBA AI engine is not configured yet. No quota was used."},status=503)
    try:
        import base64, aiohttp
        ref=await _studio_reference(request)
        # FLUX.2 Klein image-to-image expects multipart/form-data and the
        # reference image under input_image_0 (not a JSON data URI).
        form=aiohttp.FormData()
        payload=ai_payload(prompt,kind,"")
        form.add_field("prompt",payload["prompt"])
        form.add_field("width",str(payload["width"]))
        form.add_field("height",str(payload["height"]))
        form.add_field("input_image_0",ref,filename="muba-reference.jpg",content_type="image/jpeg")
        headers={"Authorization":"Bearer "+os.environ["CLOUDFLARE_API_TOKEN"]}
        async with request.app["http_session"].post(ai_endpoint(),data=form,headers=headers,timeout=90) as response:
            raw=await response.read()
            if response.status != 200:
                logger.error("Workers AI request failed status=%s body=%s",response.status,raw[:1000].decode("utf-8","replace"))
                raise RuntimeError("AI request failed")
            if response.headers.get("Content-Type","").startswith("image/"): body=raw; out_type=response.headers.get("Content-Type")
            else:
                payload=json.loads(raw.decode("utf-8")); result=payload.get("result",payload)
                encoded=result.get("image") if isinstance(result,dict) else None
                if not encoded: raise RuntimeError("AI response contained no image")
                body=base64.b64decode(encoded); out_type="image/png"
    except Exception:
        logger.exception("MUBA AI generation failed")
        return web.json_response({"error":"MUBA AI could not create this image. Failed attempts do not count."},status=503)
    consume(uid)
    import secrets, time
    key=secrets.token_urlsafe(24)
    _STUDIO_OUTPUTS[key]={"body":body,"content_type":out_type,"created":time.time()}
    output_url=EXTERNAL_URL.rstrip("/")+"/studio/output/"+key
    return web.Response(body=body,content_type=out_type,headers={
        "X-MUBA-Remaining":"DEV" if is_dev(uid) else str(remaining(uid)),
        "X-MUBA-Output-URL":output_url,
        "Content-Disposition":'inline; filename="muba-studio.png"',
    })

async def studio_output_handler(request: web.Request):
    import time
    key=request.match_info.get("key","")
    item=_STUDIO_OUTPUTS.get(key)
    if not item: return web.Response(status=404,text="Studio output expired.")
    # Keep generated links temporary instead of creating a permanent public archive.
    if time.time()-item["created"]>86400:
        _STUDIO_OUTPUTS.pop(key,None)
        return web.Response(status=410,text="Studio output expired.")
    download=request.query.get("download")=="1"
    headers={"Cache-Control":"private, max-age=3600"}
    if download: headers["Content-Disposition"]='attachment; filename="muba-studio.png"'
    return web.Response(body=item["body"],content_type=item["content_type"],headers=headers)

async def studio_render_handler(request: web.Request):
    prompt=clean_prompt(request.query.get("p","")); kind=request.query.get("k","meme")
    if not prompt: return web.Response(status=400)
    try: return web.Response(body=render_meme(await _studio_reference(request),prompt,kind),content_type="image/jpeg")
    except Exception:
        logger.exception("Inline render failed")
        return web.Response(status=503)


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
    for guardian_name in ("start","stop","status","guardian","security","lockdown","normal","warn","mute","unmute","ban","unban","delete","help"):
        application.add_handler(CommandHandler(guardian_name, guardian_slash_command), group=-2)
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(InlineQueryHandler(dev_inline_translator), group=-3)
    application.add_handler(InlineQueryHandler(inline_studio))
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^#MUBA\s+ASSISTANT\s*$"),
            assistant_group_call,
        ),
        group=-1,
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT,
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

    import aiohttp
    app["http_session"] = aiohttp.ClientSession()

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
    app.router.add_get("/studio", studio_page_handler)
    app.router.add_post("/studio/generate", studio_generate_handler)
    app.router.add_get("/studio/output/{key}", studio_output_handler)
    app.router.add_get("/studio/render", studio_render_handler)

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

        await app["http_session"].close()
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
