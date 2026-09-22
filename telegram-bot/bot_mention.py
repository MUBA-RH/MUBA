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
from collections import OrderedDict, defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent, CopyTextButton
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
    get_guardian_report_language,
    set_guardian_report_language,
    append_guardian_violation,
    guardian_violation_history,
    get_assistant_update_seen,
    mark_assistant_update_seen,
    state_storage_status,
)
from assistant_mode import LANGS, TOPIC_LABELS, CATEGORY_LABELS, CATEGORY_TOPICS, TOPIC_CATEGORY, QUESTIONS, TEXT, guided_answer, group_event, assistant_relevant, answer_for_question, match_catalog
from human_catalog import match as match_human_catalog
from natural_chat import match as match_natural_chat
from human_conversation_pack import reply as match_human_conversation
from conversation_continuity import reply as continuity_reply, remember_assistant_turn, clear as clear_conversation
from muba_daily import DAILY_LABELS, daily_text, DEVLOG_LABELS, DEVLOG, devlog_page
from assistant_extras import LABELS as EXTRA_LABELS, STORY, LAB, GUIDE, SECURITY_PROMPT, security_check, TOPIC_PROGRESS, GUIDE_SECTIONS, SHARE_LABELS, SHARE_TWEETS
from system_transparency import TRANSPARENCY_LABELS, TRANSPARENCY_NAV, TRANSPARENCY_PAGES
from system_notes import EXTRA_TRANSPARENCY_PAGES, TRANSLATOR_NOTE_LABELS, TRANSLATOR_NOTE_TEXT

for _lang, _pages in EXTRA_TRANSPARENCY_PAGES.items():
    TRANSPARENCY_PAGES[_lang].extend(_pages)
from muba_studio import REFERENCE_URL, clean_prompt, consume, remaining, render_meme, studio_html, validate_init_data, ai_configured, ai_endpoint, ai_payload, is_dev, studio_token, validate_studio_token
from muba_gallery import archive_creation, list_gallery, read_gallery_image, storage_status, get_gallery_item, set_gallery_visibility
from muba_updates import UPDATE_LABELS, AREA_LABELS, entries as update_entries, latest_id as latest_update_id, has_unseen as has_unseen_update, badge_type as update_badge_type
from muba_story import draft as story_draft, publish as publish_story, public_story
from guardian import DEV_ID, GROUP_ID, authorized_command, command_arg, inspect_message, is_control_attempt, is_guardian_group, is_dev, lockdown_enabled, set_lockdown, status_text, help_text, security_text


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("muba")

# Short-lived generated Studio outputs. Keys are random and unguessable;
# content is intentionally ephemeral and resets with the service.
_STUDIO_OUTPUTS = {}

# Public website Studio access is isolated from Telegram-authenticated Studio.
# The public endpoint is limited per client/day and only allows the official
# GitHub Pages origin. Successful generations consume quota; failures do not.
_WEB_STUDIO_USAGE = defaultdict(lambda: {"day":"","count":0})
_WEB_STUDIO_DAILY_LIMIT = 3
_WEB_STUDIO_ALLOWED_ORIGIN = "https://muba-rh.github.io"

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
_GUARDIAN_REPORT_LANGUAGE_PROMPTED=False

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

GUARDIAN_HISTORY_UI={
    "en":{"title":"📚 Guardian Violation History","history":"📚 Violation History","empty":"No recorded violations.","user_name":"User","user_id":"User ID","violation":"Violation","action":"Action","strike":"Strike","time":"Time","back":"⬅️ Categories"},
    "tr":{"title":"📚 Guardian İhlal Geçmişi","history":"📚 İhlal Geçmişi","empty":"Kayıtlı ihlal yok.","user_name":"Kullanıcı","user_id":"Kullanıcı ID","violation":"İhlal","action":"İşlem","strike":"İhlal sayısı","time":"Zaman","back":"⬅️ Kategoriler"},
    "zh":{"title":"📚 Guardian 违规记录","history":"📚 违规记录","empty":"暂无违规记录。","user_name":"用户","user_id":"用户 ID","violation":"违规","action":"操作","strike":"违规次数","time":"时间","back":"⬅️ 分类"},
    "ar":{"title":"📚 سجل مخالفات Guardian","history":"📚 سجل المخالفات","empty":"لا توجد مخالفات مسجلة.","user_name":"المستخدم","user_id":"معرّف المستخدم","violation":"المخالفة","action":"الإجراء","strike":"عدد المخالفات","time":"الوقت","back":"⬅️ الفئات"},
    "hi":{"title":"📚 Guardian उल्लंघन इतिहास","history":"📚 उल्लंघन इतिहास","empty":"कोई दर्ज उल्लंघन नहीं।","user_name":"यूज़र","user_id":"यूज़र ID","violation":"उल्लंघन","action":"कार्रवाई","strike":"उल्लंघन संख्या","time":"समय","back":"⬅️ श्रेणियाँ"},
}

def guardian_report_language_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=f"guardian_lang:{code}")] for code,label in GUARDIAN_REPORT_LANGS.items()])

def _guardian_violation_category(event):
    subkind=str(event.get("subkind") or "").casefold()
    kind=str(event.get("kind") or "security").casefold()
    return subkind or kind

def _guardian_is_violation(event):
    return str(event.get("kind") or "").casefold() in {"security","suspicious_link","flood","unauthorized_control"}

def guardian_history_keyboard(lang,category=None,index=0):
    ui=GUARDIAN_HISTORY_UI[lang]
    labels=GUARDIAN_EVENT_LABELS[lang]
    if category is None:
        history=guardian_violation_history()
        counts={}
        for item in history:
            key=item.get("category") or "security"
            counts[key]=counts.get(key,0)+1
        rows=[[InlineKeyboardButton(f"{labels.get(key,key)} ({count})",callback_data=f"guardian_history:{key}:0")] for key,count in sorted(counts.items())]
        if not rows:
            rows=[[InlineKeyboardButton(ui["empty"],callback_data="guardian_history:noop")]]
        return InlineKeyboardMarkup(rows)
    items=guardian_violation_history(category)
    if not items:
        return InlineKeyboardMarkup([[InlineKeyboardButton(ui["back"],callback_data="guardian_history")]])
    index=max(0,min(index,len(items)-1))
    pager=[]
    if index>0:
        pager.append(InlineKeyboardButton("⬅️",callback_data=f"guardian_history:{category}:{index-1}"))
    if index+1<len(items):
        pager.append(InlineKeyboardButton("➡️",callback_data=f"guardian_history:{category}:{index+1}"))
    rows=[pager] if pager else []
    rows.append([InlineKeyboardButton(ui["back"],callback_data="guardian_history")])
    return InlineKeyboardMarkup(rows)

def guardian_history_text(lang,category,index):
    ui=GUARDIAN_HISTORY_UI[lang]
    labels=GUARDIAN_EVENT_LABELS[lang]
    items=guardian_violation_history(category)
    if not items:
        return ui["empty"],0,0
    index=max(0,min(index,len(items)-1))
    item=items[index]
    lines=[
        ui["title"],
        f'{ui["violation"]}: {labels.get(item.get("category"),item.get("category"))}',
        f'{ui["action"]}: {labels.get(item.get("action"),item.get("action"))}',
        f'{ui["user_name"]}: {item.get("user_name") or "-"}',
        f'{ui["user_id"]}: {item.get("user_id") or "-"}',
    ]
    if item.get("strike") is not None:
        lines.append(f'{ui["strike"]}: {item.get("strike")}')
    lines.append(f'{ui["time"]}: {item.get("time") or "-"}')
    return "\n".join(lines)+f"\n\n{index+1}/{len(items)}",index,len(items)

def language_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=f"lang:{code}")] for code,label in LANGS.items()])

def _update_badge(lang,user_id,area):
    seen=get_assistant_update_seen(user_id,area)
    kind=update_badge_type(area,seen)
    if not kind: return ""
    return " · "+UPDATE_LABELS[lang].get(kind,kind.upper())

_UPDATE_AREAS=("gallery","studio","web","telegram","daily","assistant","guardian")

def _any_unseen_updates(user_id):
    return any(has_unseen_update(area,get_assistant_update_seen(user_id,area)) for area in _UPDATE_AREAS)

def _global_update_badge(lang,user_id):
    for item in update_entries("en"):
        if any(
            area in item.get("areas",()) and
            has_unseen_update(area,get_assistant_update_seen(user_id,area))
            for area in _UPDATE_AREAS
        ):
            kind=item.get("type","new")
            return " · "+UPDATE_LABELS[lang].get(kind,kind.upper())
    return ""

def _combined_update_badge(lang,user_id,areas):
    for area in areas:
        badge=_update_badge(lang,user_id,area)
        if badge: return badge
    return ""

def _mark_central_update_seen(user_id,item):
    # Only advance an area's seen marker when this item is that area's latest
    # canonical change. Browsing older history must never re-open a badge.
    for area in item.get("areas",()):
        latest=latest_update_id(area)
        if latest and latest==item.get("id"):
            mark_assistant_update_seen(user_id,area,latest)

def _global_update_index(lang,item_id):
    rows=update_entries(lang)
    for index,item in enumerate(rows):
        if item.get("id")==item_id:
            return index
    return 0

def _latest_area_global_index(lang,area):
    item_id=latest_update_id(area)
    return _global_update_index(lang,item_id) if item_id else 0

def _legacy_area_global_index(lang,area,area_index):
    area_rows=update_entries(lang,area)
    if not area_rows:
        return 0
    area_index=max(0,min(area_index,len(area_rows)-1))
    return _global_update_index(lang,area_rows[area_index].get("id"))

def menu_keyboard(lang,user_id=None):
    user_id=int(user_id or 0)
    labels=CATEGORY_LABELS[lang]
    updates_label=UPDATE_LABELS[lang]["center"]+_global_update_badge(lang,user_id)
    rows=[[InlineKeyboardButton(updates_label,callback_data="updates_center")]]
    rows.append([InlineKeyboardButton(TRANSPARENCY_LABELS[lang],callback_data="transparency:0")])
    for category in ("discover","understand","world"):
        rows.append([InlineKeyboardButton(labels[category],callback_data=f"category:{category}")])
    rows.append([InlineKeyboardButton(DAILY_LABELS[lang]["daily"]+_combined_update_badge(lang,user_id,("daily","web","telegram")),callback_data="daily")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["story"],callback_data="extra:story")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["guide"],callback_data="extra:guide")])
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["security"]+_update_badge(lang,user_id,"guardian"),callback_data="extra:security")])
    rows.append([InlineKeyboardButton("🎭 MUBA Studio"+_update_badge(lang,user_id,"studio"),web_app=WebAppInfo(url=EXTERNAL_URL.rstrip("/")+"/studio?uid="+str(user_id or 0)+"&st="+studio_token(user_id or 0,TOKEN)))])
    rows.append([InlineKeyboardButton(AREA_LABELS[lang]["gallery"]+_update_badge(lang,user_id,"gallery"),callback_data="updates_area:gallery:0")])
    if is_dev(user_id):
        rows.append([InlineKeyboardButton("🎬 MUBA Daily Story",callback_data="story_director")])
        rows.append([InlineKeyboardButton(GALLERY_ADMIN_LABELS[lang]["menu"],callback_data="gallery_admin")])
    rows.append([InlineKeyboardButton(SHARE_LABELS[lang]["menu"],callback_data="share")])
    rows.append([InlineKeyboardButton(TRANSLATOR_NOTE_LABELS[lang],callback_data="translator_note")])
    rows.append([InlineKeyboardButton(TEXT[lang]["language"],callback_data="language")])
    return InlineKeyboardMarkup(rows)

def updates_center_text(lang,user_id,index=0):
    rows=update_entries(lang)
    if not rows:
        return UPDATE_LABELS[lang]["center"],0,0
    index=max(0,min(index,len(rows)-1))
    item=rows[index]
    _mark_central_update_seen(user_id,item)
    kind_label=UPDATE_LABELS[lang].get(item["type"],item["type"].upper())
    related=" · ".join(AREA_LABELS[lang].get(area,area) for area in item.get("areas",()))
    body=(
        f'{UPDATE_LABELS[lang]["center"]}\n\n'
        f'{kind_label} · {item["date"]}\n'
        f'{item["title_text"]}\n\n'
        f'{item["text"]}'
    )
    if related:
        body+=f'\n\n{UPDATE_LABELS[lang]["related"]}: {related}'
    body+=f'\n\n{index+1}/{len(rows)}'
    return body,index,len(rows)

def updates_center_keyboard(lang,user_id,index=0):
    rows_data=update_entries(lang)
    total=len(rows_data)
    if not total:
        return InlineKeyboardMarkup([[InlineKeyboardButton(UPDATE_LABELS[lang]["back"],callback_data="menu")]])
    index=max(0,min(index,total-1))
    pager=[]
    if index>0:
        pager.append(InlineKeyboardButton("⬅️",callback_data=f"updates_global:{index-1}"))
    if index+1<total:
        pager.append(InlineKeyboardButton("➡️",callback_data=f"updates_global:{index+1}"))
    rows=[pager] if pager else []
    item=rows_data[index]
    if "gallery" in item.get("areas",()):
        rows.append([InlineKeyboardButton(UPDATE_LABELS[lang]["open_gallery"],url="https://muba-rh.github.io/MUBA/#gallery")])
    rows.append([InlineKeyboardButton(UPDATE_LABELS[lang]["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def updates_area_text(lang,user_id,area,index):
    # Unit views stay local. The central MUBA Updates feed remains the only
    # combined timeline for every canonical project update.
    rows=update_entries(lang,area)
    if not rows:
        return AREA_LABELS[lang].get(area,area),0,0
    index=max(0,min(index,len(rows)-1))
    item=rows[index]
    # Opening a unit's newest update means that unit has been read. This clears
    # only that unit's badge; older-history browsing cannot move seen state back.
    latest=latest_update_id(area)
    if latest and item.get("id")==latest:
        mark_assistant_update_seen(user_id,area,latest)
    kind_label=UPDATE_LABELS[lang].get(item["type"],item["type"].upper())
    body=(
        f'{AREA_LABELS[lang].get(area,area)}\n\n'
        f'{kind_label} · {item["date"]}\n'
        f'{item["title_text"]}\n\n'
        f'{item["text"]}\n\n'
        f'{index+1}/{len(rows)}'
    )
    return body,index,len(rows)

def updates_area_keyboard(lang,user_id,area,index):
    rows_data=update_entries(lang,area)
    total=len(rows_data)
    if not total:
        return InlineKeyboardMarkup([[InlineKeyboardButton(UPDATE_LABELS[lang]["back"],callback_data="menu")]])
    index=max(0,min(index,total-1))
    pager=[]
    if index>0:
        pager.append(InlineKeyboardButton("⬅️",callback_data=f"updates_area:{area}:{index-1}"))
    if index+1<total:
        pager.append(InlineKeyboardButton("➡️",callback_data=f"updates_area:{area}:{index+1}"))
    rows=[pager] if pager else []
    if area=="gallery":
        rows.append([InlineKeyboardButton(UPDATE_LABELS[lang]["open_gallery"],url="https://muba-rh.github.io/MUBA/#gallery")])
    rows.append([InlineKeyboardButton(UPDATE_LABELS[lang]["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

GALLERY_ADMIN_LABELS={
"en":{"menu":"🛠 Gallery Moderation","title":"🛠 MUBA Gallery Moderation","empty":"No Gallery items.","public":"PUBLIC","hidden":"HIDDEN","rejected":"REJECTED","back":"⬅️ Back","saved":"Gallery status updated."},
"tr":{"menu":"🛠 Galeri Moderasyonu","title":"🛠 MUBA Galeri Moderasyonu","empty":"Galeri kaydı yok.","public":"YAYINDA","hidden":"GİZLİ","rejected":"REDDEDİLDİ","back":"⬅️ Geri","saved":"Galeri durumu güncellendi."},
"zh":{"menu":"🛠 Gallery 管理","title":"🛠 MUBA Gallery 管理","empty":"暂无 Gallery 项目。","public":"公开","hidden":"隐藏","rejected":"拒绝","back":"⬅️ 返回","saved":"Gallery 状态已更新。"},
"ar":{"menu":"🛠 إدارة Gallery","title":"🛠 إدارة MUBA Gallery","empty":"لا توجد عناصر في Gallery.","public":"عام","hidden":"مخفي","rejected":"مرفوض","back":"⬅️ رجوع","saved":"تم تحديث حالة Gallery."},
"hi":{"menu":"🛠 Gallery Moderation","title":"🛠 MUBA Gallery Moderation","empty":"Gallery items नहीं हैं।","public":"PUBLIC","hidden":"HIDDEN","rejected":"REJECTED","back":"⬅️ वापस","saved":"Gallery status updated."},
}

def gallery_admin_keyboard(lang):
    labels=GALLERY_ADMIN_LABELS[lang]
    items=list_gallery(limit=10,visibility=None)
    rows=[]
    for item in items:
        state=item.get("visibility","public")
        marker={"public":"●","hidden":"◐","rejected":"×"}.get(state,"?")
        label=(item.get("label") or "MUBA")[:32]
        rows.append([InlineKeyboardButton(f"{marker} {label}",callback_data=f'gallery_admin_item:{item["id"]}')])
    if not rows:
        rows.append([InlineKeyboardButton(labels["empty"],callback_data="gallery_admin_noop")])
    rows.append([InlineKeyboardButton(labels["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def gallery_admin_item_text(lang,item):
    labels=GALLERY_ADMIN_LABELS[lang]
    status=item.get("visibility","public")
    return (
        f'{labels["title"]}\n\n'
        f'{item.get("label") or "MUBA"}\n'
        f'{str(item.get("kind") or "image").upper()} · {str(item.get("source") or "web").upper()}\n'
        f'Status: {labels.get(status,status.upper())}\n'
        f'{item.get("created_at") or ""}'
    )

def gallery_admin_item_keyboard(lang,item_id):
    labels=GALLERY_ADMIN_LABELS[lang]
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(labels["public"],callback_data=f"gallery_set:{item_id}:public"),
            InlineKeyboardButton(labels["hidden"],callback_data=f"gallery_set:{item_id}:hidden"),
        ],
        [InlineKeyboardButton(labels["rejected"],callback_data=f"gallery_set:{item_id}:rejected")],
        [InlineKeyboardButton(labels["back"],callback_data="gallery_admin")],
    ])

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

def daily_keyboard(lang,user_id=None):
    user_id=int(user_id or 0)
    labels=DAILY_LABELS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels["x"],callback_data="daily:x")],
        [InlineKeyboardButton(labels["web"]+_update_badge(lang,user_id,"web"),callback_data="daily:web")],
        [InlineKeyboardButton(labels["telegram"]+_update_badge(lang,user_id,"telegram"),callback_data="daily:telegram")],
        [InlineKeyboardButton(labels["updates"]+_global_update_badge(lang,user_id),callback_data="updates_center")],
        [InlineKeyboardButton(DEVLOG_LABELS[lang]["log"]+_update_badge(lang,user_id,"assistant"),callback_data="devlog")],
        [InlineKeyboardButton(labels["back"],callback_data="menu")],
    ])

def devlog_keyboard(lang,category=None,index=0):
    labels=DEVLOG_LABELS[lang]
    if category not in ("new","updates","fixed"):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(labels["new"],callback_data="devlog:new:0")],
            [InlineKeyboardButton(labels["updates"],callback_data="devlog:updates:0")],
            [InlineKeyboardButton(labels["fixed"],callback_data="devlog:fixed:0")],
            [InlineKeyboardButton(labels["back"],callback_data="daily")],
        ])
    total=len(DEVLOG[lang][category])
    pager=[]
    if index>0:
        pager.append(InlineKeyboardButton("⬅️",callback_data=f"devlog:{category}:{index-1}"))
    if index+1<total:
        pager.append(InlineKeyboardButton("➡️",callback_data=f"devlog:{category}:{index+1}"))
    rows=[pager] if pager else []
    rows.append([InlineKeyboardButton(labels["back"],callback_data="devlog")])
    return InlineKeyboardMarkup(rows)

def story_keyboard(lang,page):
    total=len(STORY[lang])
    pager=[]
    if page>0:
        pager.append(InlineKeyboardButton("⬅️",callback_data=f"story:{page-1}"))
    if page+1<total:
        pager.append(InlineKeyboardButton("➡️",callback_data=f"story:{page+1}"))
    rows=[pager] if pager else []
    rows.append([InlineKeyboardButton(EXTRA_LABELS[lang]["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def extra_keyboard(lang,mode):
    labels=EXTRA_LABELS[lang]
    if mode=="story":
        return story_keyboard(lang,0)
    if mode=="lab":
        rows=[
            [InlineKeyboardButton("😂 Meme",callback_data="lab:meme")],
            [InlineKeyboardButton("✍️ Tweet",callback_data="lab:tweet")],
            [InlineKeyboardButton("🖼️ Visual 16:9",callback_data="lab:visual")],
        ]
    elif mode=="guide":
        rows=[[InlineKeyboardButton(label,callback_data=f"guide:{i}")] for i,(label,_) in enumerate(GUIDE_SECTIONS[lang])]
    else:
        rows=[]
    rows.append([InlineKeyboardButton(labels["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def share_keyboard(lang,index=None):
    labels=SHARE_LABELS[lang]
    if index is None:
        rows=[[InlineKeyboardButton(labels["tweets"],callback_data="share:tweet:0")]]
    else:
        total=len(SHARE_TWEETS[lang])
        pager=[]
        if index>0:
            pager.append(InlineKeyboardButton("⬅️",callback_data=f"share:tweet:{index-1}"))
        if index+1<total:
            pager.append(InlineKeyboardButton("➡️",callback_data=f"share:tweet:{index+1}"))
        rows=[pager] if pager else []
        rows.append([InlineKeyboardButton("📋 COPY",copy_text=CopyTextButton(text=SHARE_TWEETS[lang][index]))])
    rows.append([InlineKeyboardButton(labels["back"],callback_data="menu" if index is None else "share")])
    return InlineKeyboardMarkup(rows)

def category_keyboard(lang,category):
    topics=CATEGORY_TOPICS[category]
    rows=[]
    for topic in topics:
        for i,(label,_) in enumerate(TOPIC_PROGRESS.get(lang,{}).get(topic,[])):
            rows.append([InlineKeyboardButton(label,callback_data=f"topicx:{topic}:{i}")])
    for i,(topic,question) in enumerate(QUESTIONS[lang]):
        if topic in topics:
            rows.append([InlineKeyboardButton(question,callback_data=f"q:{i}")])
    rows.append([InlineKeyboardButton(TEXT[lang]["back"],callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def topic_keyboard(lang,topic):
    return category_keyboard(lang,TOPIC_CATEGORY[topic])

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
        if lang in GUARDIAN_REPORT_LANGS and set_guardian_report_language(lang):
            global _GUARDIAN_REPORT_LANGUAGE_PROMPTED
            _GUARDIAN_REPORT_LANGUAGE_PROMPTED=False
            await q.edit_message_text(
                GUARDIAN_REPORT_TEXT[lang]["saved"],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(GUARDIAN_HISTORY_UI[lang]["history"],callback_data="guardian_history")]])
            )
        return
    if data=="guardian_history":
        if not is_dev(user_id): return
        lang=get_guardian_report_language() or "en"
        await q.edit_message_text(GUARDIAN_HISTORY_UI[lang]["title"],reply_markup=guardian_history_keyboard(lang)); return
    if data.startswith("guardian_history:"):
        if not is_dev(user_id): return
        parts=data.split(":")
        if len(parts)!=3 or parts[1]=="noop": return
        category=parts[1]; raw=parts[2]
        index=int(raw) if raw.isdigit() else 0
        lang=get_guardian_report_language() or "en"
        body,index,total=guardian_history_text(lang,category,index)
        await q.edit_message_text(body,reply_markup=guardian_history_keyboard(lang,category,index)); return
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
    if data=="updates_center":
        body,index,total=updates_center_text(lang,user_id,0)
        await q.edit_message_text(body,reply_markup=updates_center_keyboard(lang,user_id,index),disable_web_page_preview=True); return
    if data.startswith("updates_global:"):
        raw=data.split(":",1)[1]
        index=int(raw) if raw.isdigit() else 0
        body,index,total=updates_center_text(lang,user_id,index)
        await q.edit_message_text(body,reply_markup=updates_center_keyboard(lang,user_id,index),disable_web_page_preview=True); return
    if data.startswith("updates_jump:"):
        area=data.split(":",1)[1]
        index=_latest_area_global_index(lang,area)
        body,index,total=updates_center_text(lang,user_id,index)
        await q.edit_message_text(body,reply_markup=updates_center_keyboard(lang,user_id,index),disable_web_page_preview=True); return
    if data=="story_director":
        if not is_dev(user_id): return
        item=story_draft()
        body="🎬 MUBA DAILY STORY — "+item["day"]+"\\n\\n"+item["theme"]+"\\n\\n"+"\\n".join(f"{i+1}. {s}" for i,s in enumerate(item["scenes"]))+"\\n\\nTWT: "+item["twt"]+"\\n\\nStatus: "+item["status"].upper() 
        rows=[]
        if item["status"]!="published": rows.append([InlineKeyboardButton("✅ WEB YAYINLA",callback_data="story_publish")])
        rows.append([InlineKeyboardButton("⬅️ Back",callback_data="menu")]) 
        await q.edit_message_text(body,reply_markup=InlineKeyboardMarkup(rows)); return
    if data=="story_publish":
        if not is_dev(user_id): return
        item=publish_story(story_draft()["day"])
        await q.edit_message_text("🎬 MUBA Daily Story\\n\\nWeb yayını onaylandı: "+item["day"],reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Story",url="https://muba-rh.github.io/MUBA/#daily-story")],[InlineKeyboardButton("⬅️ Back",callback_data="menu")]])); return
    if data=="gallery_admin":
        if not is_dev(user_id): return
        await q.edit_message_text(GALLERY_ADMIN_LABELS[lang]["title"],reply_markup=gallery_admin_keyboard(lang)); return
    if data.startswith("gallery_admin_item:"):
        if not is_dev(user_id): return
        item_id=data.split(":",1)[1]
        item=get_gallery_item(item_id)
        if not item:
            await q.edit_message_text(GALLERY_ADMIN_LABELS[lang]["empty"],reply_markup=gallery_admin_keyboard(lang)); return
        await q.edit_message_text(gallery_admin_item_text(lang,item),reply_markup=gallery_admin_item_keyboard(lang,item_id)); return
    if data.startswith("gallery_set:"):
        if not is_dev(user_id): return
        _,item_id,visibility=data.split(":",2)
        try:
            item=set_gallery_visibility(item_id,visibility)
        except ValueError:
            item=None
        if not item:
            await q.edit_message_text(GALLERY_ADMIN_LABELS[lang]["empty"],reply_markup=gallery_admin_keyboard(lang)); return
        await q.edit_message_text(GALLERY_ADMIN_LABELS[lang]["saved"]+"\n\n"+gallery_admin_item_text(lang,item),reply_markup=gallery_admin_item_keyboard(lang,item_id)); return
    if data.startswith("updates_area:"):
        _,area,raw=data.split(":",2)
        index=int(raw) if raw.isdigit() else 0
        body,index,total=updates_area_text(lang,user_id,area,index)
        await q.edit_message_text(body,reply_markup=updates_area_keyboard(lang,user_id,area,index),disable_web_page_preview=True); return
    if data.startswith("transparency:"):
        raw=data.split(":",1)[1]
        page=int(raw) if raw.isdigit() else 0
        page=max(0,min(page,len(TRANSPARENCY_PAGES[lang])-1))
        await q.edit_message_text(transparency_text(lang,page),reply_markup=transparency_keyboard(lang,page),disable_web_page_preview=True); return
    if data=="translator_note":
        await q.edit_message_text(TRANSLATOR_NOTE_TEXT[lang],reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXT[lang]["back"],callback_data="menu")]]),disable_web_page_preview=True); return
    if data=="daily":
        await q.edit_message_text(DAILY_LABELS[lang]["daily"],reply_markup=daily_keyboard(lang,user_id)); return
    if data.startswith("daily:"):
        section=data.split(":",1)[1]
        if section=="updates":
            body,index,total=updates_center_text(lang,user_id,0)
            await q.edit_message_text(body,reply_markup=updates_center_keyboard(lang,user_id,index),disable_web_page_preview=True); return
        await q.edit_message_text(daily_text(lang,section),reply_markup=daily_keyboard(lang,user_id),disable_web_page_preview=True); return
    if data=="devlog":
        await q.edit_message_text(DEVLOG_LABELS[lang]["log"],reply_markup=devlog_keyboard(lang)); return
    if data.startswith("devlog:"):
        _,category,raw=data.split(":",2)
        index=int(raw) if raw.isdigit() else 0
        body,index,total=devlog_page(lang,category,index)
        await q.edit_message_text(f"{body}\n\n{index+1}/{total}",reply_markup=devlog_keyboard(lang,category,index)); return
    if data.startswith("extra:"):
        mode=data.split(":",1)[1]
        if mode=="security":
            context.user_data["muba_security_check"]=True
            await q.edit_message_text(SECURITY_PROMPT[lang],reply_markup=extra_keyboard(lang,"security")); return
        if mode=="story":
            await q.edit_message_text(STORY[lang][0],reply_markup=story_keyboard(lang,0)); return
        await q.edit_message_text(EXTRA_LABELS[lang][mode],reply_markup=extra_keyboard(lang,mode)); return
    if data.startswith("story:"):
        i=int(data.split(":",1)[1]); i=max(0,min(i,len(STORY[lang])-1))
        await q.edit_message_text(STORY[lang][i],reply_markup=story_keyboard(lang,i)); return
    if data.startswith("lab:"):
        kind=data.split(":",1)[1]; await q.edit_message_text(LAB[lang][kind],reply_markup=extra_keyboard(lang,"lab")); return
    if data.startswith("guide:"):
        i=int(data.split(":",1)[1]); items=GUIDE_SECTIONS[lang]; i=max(0,min(i,len(items)-1))
        await q.edit_message_text(items[i][1],reply_markup=extra_keyboard(lang,"guide")); return
    if data=="share":
        await q.edit_message_text(SHARE_LABELS[lang]["menu"],reply_markup=share_keyboard(lang)); return
    if data.startswith("share:tweet:"):
        raw=data.rsplit(":",1)[1]; i=int(raw) if raw.isdigit() else 0
        i=max(0,min(i,len(SHARE_TWEETS[lang])-1))
        await q.edit_message_text(SHARE_TWEETS[lang][i],reply_markup=share_keyboard(lang,i)); return
    if data.startswith("topicx:"):
        _,topic,raw=data.split(":",2)
        i=int(raw) if raw.isdigit() else 0
        items=TOPIC_PROGRESS.get(lang,{}).get(topic,[])
        if items:
            i=max(0,min(i,len(items)-1))
            await q.edit_message_text(items[i][1],reply_markup=topic_keyboard(lang,topic)); return
    if data.startswith("category:"):
        category=data.split(":",1)[1]
        if category in CATEGORY_TOPICS:
            await q.edit_message_text(CATEGORY_LABELS[lang][category],reply_markup=category_keyboard(lang,category)); return
    if data.startswith("topic:"):
        topic=data.split(":",1)[1]
        await q.edit_message_text(CATEGORY_LABELS[lang][TOPIC_CATEGORY[topic]],reply_markup=topic_keyboard(lang,topic)); return
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
        global _GUARDIAN_REPORT_LANGUAGE_PROMPTED
        kind=str(event.get("kind") or "guardian").casefold()
        subkind=str(event.get("subkind") or "").casefold()
        action=str(event.get("action") or "info").casefold()

        # Successful DEV management/manual actions are intentionally not private-report events.
        if kind in {"management","moderation"}:
            return

        user_name="-"
        if user_id is not None:
            try:
                member=await context.bot.get_chat_member(GROUP_ID,user_id)
                tg_user=member.user
                user_name=("@"+tg_user.username) if tg_user.username else (tg_user.full_name or "-")
            except Exception:
                logger.info("Guardian could not resolve user display name for %s",user_id)

        if _guardian_is_violation(event):
            category=_guardian_violation_category(event)
            append_guardian_violation({
                "category":category,
                "kind":kind,
                "subkind":subkind,
                "action":action,
                "user_id":user_id,
                "user_name":user_name,
                "strike":event.get("strike"),
                "detail":event.get("detail"),
                "time":datetime.now(_ISTANBUL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            })

        lang=get_guardian_report_language()
        if lang not in GUARDIAN_REPORT_LANGS:
            if not _GUARDIAN_REPORT_LANGUAGE_PROMPTED:
                _GUARDIAN_REPORT_LANGUAGE_PROMPTED=True
                await context.bot.send_message(
                    chat_id=DEV_ID,
                    text=GUARDIAN_REPORT_TEXT["en"]["choose"],
                    reply_markup=guardian_report_language_keyboard(),
                )
            return

        ui=GUARDIAN_REPORT_TEXT[lang]
        labels=GUARDIAN_EVENT_LABELS[lang]
        history_ui=GUARDIAN_HISTORY_UI[lang]
        event_text=labels.get(kind,kind)
        if subkind:
            event_text += " / "+labels.get(subkind,subkind)
        lines=[ui["title"],f'{ui["event"]}: {event_text}',f'{ui["action"]}: {labels.get(action,action)}']
        if user_id is not None:
            lines.append(f'{history_ui["user_name"]}: {user_name}')
            lines.append(f'{ui["user"]}: {user_id}')
        strike=event.get("strike")
        if strike is not None: lines.append(f'{ui["strike"]}: {strike}')
        detail=event.get("detail")
        if detail: lines.append(f'{ui["detail"]}: {detail}')
        markup=None
        if _guardian_is_violation(event):
            markup=InlineKeyboardMarkup([[InlineKeyboardButton(history_ui["history"],callback_data="guardian_history")]])
        await context.bot.send_message(chat_id=DEV_ID,text="\n".join(lines),reply_markup=markup)
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
            except Exception:
                logger.exception("Guardian could not change group posting permissions")
                await message.reply_text("🛡️ Guardian could not change group permissions. Check bot admin permissions.")
                await _guardian_dev_report(context,{"kind":"runtime","subkind":cmd.lstrip("#").casefold(),"action":"failed","detail":"Grup izinleri değiştirilemedi."},user_id)
            return
        if cmd in ("#GUARDIAN","#STATUS"):
            await message.reply_text(status_text(group_conversation_paused(chat.id)))
            return
        if cmd=="#HELP":
            await message.reply_text(help_text())
            return
        if cmd=="#SECURITY":
            await message.reply_text(security_text(group_conversation_paused(chat.id)))
            return
        if cmd=="#LOCKDOWN":
            set_lockdown(True)
            await message.reply_text("🛡️ GUARDIAN — LOCKDOWN")
            return
        if cmd=="#NORMAL":
            set_lockdown(False)
            await message.reply_text("🛡️ GUARDIAN — NORMAL")
            return
        target=message.reply_to_message
        try:
            if cmd=="#DELETE":
                if target:
                    await target.delete()
                    await message.reply_text("🛡️ Deleted.")
                return
            if cmd=="#WARN":
                if target and target.from_user:
                    await message.reply_text("⚠️ GUARDIAN warning for "+target.from_user.mention_html(),parse_mode="HTML")
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
                    return
                from telegram import ChatPermissions
                perms=ChatPermissions.no_permissions() if cmd=="#MUTE" else ChatPermissions.all_permissions()
                await context.bot.restrict_chat_member(chat.id,tid,permissions=perms)
                await message.reply_text("🛡️ User "+("muted." if cmd=="#MUTE" else "unmuted."))
                return
            if cmd=="#UNBAN":
                arg=command_arg(text)
                if arg.lstrip("-").isdigit():
                    tid=int(arg)
                    await context.bot.unban_chat_member(chat.id,tid)
                    await message.reply_text("🛡️ User unbanned.")
                else:
                    await message.reply_text("Use: #UNBAN <user_id>")
                return
        except Exception:
            logger.exception("Guardian moderation action failed")
            await message.reply_text("🛡️ Guardian action could not be completed. Check bot admin permissions.")
            await _guardian_dev_report(context,{"kind":"runtime","subkind":"moderation","action":"failed","detail":"Manuel Guardian işlemi tamamlanamadı."},user_id)
            return
    # #STOP pauses the full Guardian runtime after DEV command handling.
    # #START remains available because authorized DEV commands are processed above.
    if group_conversation_paused(chat.id):
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
    gallery_item=_archive_studio_output(body,out_type,prompt,kind,"telegram")
    import secrets, time
    key=secrets.token_urlsafe(24)
    _STUDIO_OUTPUTS[key]={"body":body,"content_type":out_type,"created":time.time()}
    output_url=EXTERNAL_URL.rstrip("/")+"/studio/output/"+key
    return web.Response(body=body,content_type=out_type,headers={
        "X-MUBA-Remaining":"DEV" if is_dev(uid) else str(remaining(uid)),
        "X-MUBA-Output-URL":output_url,
        "X-MUBA-Gallery-ID":gallery_item["id"] if gallery_item else "",
        "Content-Disposition":'inline; filename="muba-studio.png"',
    })

def _web_studio_client_key(request: web.Request) -> str:
    forwarded=(request.headers.get("X-Forwarded-For") or "").split(",",1)[0].strip()
    return forwarded or request.headers.get("CF-Connecting-IP") or request.remote or "unknown"

def _web_studio_remaining(client_key: str) -> int:
    row=_WEB_STUDIO_USAGE[client_key]; day=time.strftime("%Y-%m-%d",time.gmtime())
    if row["day"]!=day: row.update(day=day,count=0)
    return max(0,_WEB_STUDIO_DAILY_LIMIT-row["count"])

def _web_studio_consume(client_key: str) -> None:
    row=_WEB_STUDIO_USAGE[client_key]; day=time.strftime("%Y-%m-%d",time.gmtime())
    if row["day"]!=day: row.update(day=day,count=0)
    row["count"]+=1

def _web_studio_cors_headers(origin: str) -> dict:
    if origin!=_WEB_STUDIO_ALLOWED_ORIGIN: return {}
    return {
        "Access-Control-Allow-Origin":origin,
        "Access-Control-Allow-Methods":"POST, OPTIONS",
        "Access-Control-Allow-Headers":"Content-Type",
        "Access-Control-Expose-Headers":"X-MUBA-Remaining, X-MUBA-Output-URL, X-MUBA-Gallery-ID",
        "Vary":"Origin",
    }

def _web_studio_json(origin: str, payload: dict, status: int):
    return web.json_response(payload,status=status,headers=_web_studio_cors_headers(origin))

async def studio_web_options_handler(request: web.Request):
    origin=request.headers.get("Origin","")
    if origin!=_WEB_STUDIO_ALLOWED_ORIGIN:
        return web.Response(status=403)
    return web.Response(status=204,headers=_web_studio_cors_headers(origin))

async def studio_web_generate_handler(request: web.Request):
    """Public GitHub Pages Studio endpoint with isolated rate limiting."""
    origin=request.headers.get("Origin","")
    if origin!=_WEB_STUDIO_ALLOWED_ORIGIN:
        return web.json_response({"error":"Website origin not allowed."},status=403)
    try:
        data=await request.json()
    except Exception:
        return _web_studio_json(origin,{"error":"Invalid request."},400)

    prompt=clean_prompt(str(data.get("prompt","")))
    kind=str(data.get("kind","image")).strip().casefold()
    if kind=="reaction": kind="emoji"
    if kind not in {"meme","image","sticker","emoji"}:
        return _web_studio_json(origin,{"error":"Invalid Studio type."},400)
    if not prompt:
        return _web_studio_json(origin,{"error":"Write something for MUBA."},400)

    client_key=_web_studio_client_key(request)
    if _web_studio_remaining(client_key)<=0:
        return _web_studio_json(origin,{"error":"Daily web limit reached — 3/3."},429)
    if not ai_configured():
        return _web_studio_json(origin,{"error":"MUBA AI engine is not configured yet. No quota was used."},503)

    try:
        import base64, aiohttp
        ref=await _studio_reference(request)
        form=aiohttp.FormData()
        payload=ai_payload(prompt,kind,"")
        form.add_field("prompt",payload["prompt"])
        form.add_field("width",str(payload["width"]))
        form.add_field("height",str(payload["height"]))
        form.add_field("input_image_0",ref,filename="muba-reference.jpg",content_type="image/jpeg")
        headers={"Authorization":"Bearer "+os.environ["CLOUDFLARE_API_TOKEN"]}
        async with request.app["http_session"].post(ai_endpoint(),data=form,headers=headers,timeout=90) as response:
            raw=await response.read()
            if response.status!=200:
                logger.error("Public Studio AI request failed status=%s body=%s",response.status,raw[:1000].decode("utf-8","replace"))
                raise RuntimeError("AI request failed")
            if response.headers.get("Content-Type","").startswith("image/"):
                body=raw; out_type=response.headers.get("Content-Type")
            else:
                response_payload=json.loads(raw.decode("utf-8"))
                result=response_payload.get("result",response_payload)
                encoded=result.get("image") if isinstance(result,dict) else None
                if not encoded: raise RuntimeError("AI response contained no image")
                body=base64.b64decode(encoded); out_type="image/png"
    except Exception:
        logger.exception("Public MUBA Studio generation failed")
        return _web_studio_json(origin,{"error":"MUBA Studio could not create this image. Failed attempts do not count."},503)

    _web_studio_consume(client_key)
    gallery_item=_archive_studio_output(body,out_type,prompt,kind,"web")
    import secrets
    key=secrets.token_urlsafe(24)
    _STUDIO_OUTPUTS[key]={"body":body,"content_type":out_type,"created":time.time()}
    output_url=EXTERNAL_URL.rstrip("/")+"/studio/output/"+key
    headers=_web_studio_cors_headers(origin)
    headers.update({
        "X-MUBA-Remaining":str(_web_studio_remaining(client_key)),
        "X-MUBA-Output-URL":output_url,
        "X-MUBA-Gallery-ID":gallery_item["id"] if gallery_item else "",
        "Content-Disposition":'inline; filename="muba-studio.png"',
        "Cache-Control":"no-store",
    })
    return web.Response(body=body,content_type=out_type,headers=headers)

def _archive_studio_output(body,out_type,prompt,kind,source):
    try:
        content_type=(out_type or "image/png").split(";",1)[0].strip()
        return archive_creation(body,content_type,prompt,kind,source)
    except Exception:
        logger.exception("MUBA Gallery archive write failed")
        return None

def _gallery_cors_headers():
    return {"Access-Control-Allow-Origin":_WEB_STUDIO_ALLOWED_ORIGIN,"Vary":"Origin"}

async def story_public_handler(request: web.Request):
    item=public_story(request.query.get("day") or None)
    if not item: return web.json_response({"story":None},headers=_gallery_cors_headers())
    item=dict(item)
    item["image_urls"]=[EXTERNAL_URL.rstrip("/")+"/gallery/image/"+x for x in item.get("images",[])]
    item.pop("prompts",None)
    return web.json_response({"story":item},headers=_gallery_cors_headers())

async def gallery_list_handler(request: web.Request):
    raw_limit=request.query.get("limit","60")
    limit=int(raw_limit) if str(raw_limit).isdigit() else 60
    kind=request.query.get("kind") or None
    items=[]
    for item in list_gallery(limit=limit,kind=kind):
        items.append({
            "id":item["id"],
            "label":item["label"],
            "kind":item["kind"],
            "source":item["source"],
            "created_at":item["created_at"],
            "image_url":EXTERNAL_URL.rstrip("/")+"/gallery/image/"+item["id"],
        })
    state=storage_status()
    return web.json_response({"items":items,"persistent":state["persistent"],"writable":state["writable"],"backend":state.get("backend","unknown")},headers=_gallery_cors_headers())

async def gallery_image_handler(request: web.Request):
    result=read_gallery_image(request.match_info.get("item_id",""))
    if not result: return web.Response(status=404,text="Gallery item not found.")
    body,content_type=result
    return web.Response(body=body,content_type=content_type,headers={"Cache-Control":"public, max-age=31536000, immutable"})

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

async def state_health_handler(request: web.Request):
    state=state_storage_status()
    gallery=storage_status()
    return web.json_response({
        "state":{"persistent":state["persistent"],"backend":state["backend"]},
        "gallery":{"persistent":gallery["persistent"],"writable":gallery["writable"],"backend":gallery.get("backend","unknown")},
    })


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
    app.router.add_get(
        "/health/state",
        state_health_handler,
    )

    app.router.add_post(
        WEBHOOK_PATH,
        webhook_handler,
    )
    app.router.add_get("/studio", studio_page_handler)
    app.router.add_post("/studio/generate", studio_generate_handler)
    app.router.add_options("/studio/web-generate", studio_web_options_handler)
    app.router.add_post("/studio/web-generate", studio_web_generate_handler)
    app.router.add_get("/studio/output/{key}", studio_output_handler)
    app.router.add_get("/studio/render", studio_render_handler)
    app.router.add_get("/story", story_public_handler)
    app.router.add_get("/gallery", gallery_list_handler)
    app.router.add_get("/gallery/image/{item_id}", gallery_image_handler)

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
