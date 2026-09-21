"""Central append-only public change feed for MUBA Assistant.

Add verified product changes here instead of replacing older entries.
UI badges use per-user seen IDs from muba_brain, while this history stays
source-controlled and durable.
"""
from __future__ import annotations

UPDATE_LABELS={
"en":{"center":"🔔 MUBA Updates","new":"NEW","updated":"UPDATED","improved":"IMPROVED","fixed":"FIXED","back":"⬅️ Back","open_gallery":"🖼 Open MUBA Gallery"},
"tr":{"center":"🔔 MUBA Yenilikleri","new":"YENİ","updated":"GÜNCELLENDİ","improved":"İYİLEŞTİRİLDİ","fixed":"DÜZELTİLDİ","back":"⬅️ Geri","open_gallery":"🖼 MUBA Galeri'yi Aç"},
"zh":{"center":"🔔 MUBA 更新","new":"新增","updated":"已更新","improved":"已改进","fixed":"已修复","back":"⬅️ 返回","open_gallery":"🖼 打开 MUBA Gallery"},
"ar":{"center":"🔔 تحديثات MUBA","new":"جديد","updated":"محدّث","improved":"محسّن","fixed":"تم الإصلاح","back":"⬅️ رجوع","open_gallery":"🖼 فتح MUBA Gallery"},
"hi":{"center":"🔔 MUBA Updates","new":"NEW","updated":"UPDATED","improved":"IMPROVED","fixed":"FIXED","back":"⬅️ वापस","open_gallery":"🖼 MUBA Gallery खोलें"},
}

AREA_LABELS={
"en":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 Website","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"tr":{"gallery":"🖼 MUBA Galeri","studio":"🎭 MUBA Studio","web":"🌐 Web Sitesi","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"zh":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 网站","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"ar":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 الموقع","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"hi":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 वेबसाइट","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
}

UPDATES=[
{"id":"20260921-gallery","date":"2026-09-21","type":"new","areas":["gallery","studio","web","telegram"],
 "en":"MUBA Gallery added as a shared archive for creations from Web Studio and Telegram Studio.",
 "tr":"MUBA Galeri, Web Studio ve Telegram Studio üretimlerinin ortak arşivi olarak eklendi.",
 "zh":"新增 MUBA Gallery，用于统一归档 Web Studio 与 Telegram Studio 的作品。",
 "ar":"تمت إضافة MUBA Gallery كأرشيف مشترك لإبداعات Web Studio وTelegram Studio.",
 "hi":"MUBA Gallery को Web Studio और Telegram Studio creations के shared archive के रूप में जोड़ा गया।"},
{"id":"20260921-studio-quality","date":"2026-09-21","type":"improved","areas":["studio"],
 "en":"Meme, Image, Sticker and Reaction generation were separated more clearly, with stronger realistic emotion guidance for MUBA reactions.",
 "tr":"Meme, Image, Sticker ve Reaction üretimleri daha net ayrıldı; MUBA reaksiyonları için daha güçlü ve gerçekçi duygu yönlendirmesi eklendi.",
 "zh":"Meme、Image、Sticker 与 Reaction 的生成风格进一步区分，并强化了 MUBA 表情的真实情绪表现。",
 "ar":"تم توضيح الفروق بين Meme وImage وSticker وReaction مع تحسين واقعية تعبيرات MUBA.",
 "hi":"Meme, Image, Sticker और Reaction generation को अधिक स्पष्ट रूप से अलग किया गया और MUBA reactions की realistic emotion guidance बेहतर की गई।"},
{"id":"20260921-textless","date":"2026-09-21","type":"improved","areas":["studio"],
 "en":"Studio now creates text-free visuals by default and allows visible writing only when explicitly requested.",
 "tr":"Studio artık varsayılan olarak yazısız görsel üretiyor; görünür yazıya yalnız açıkça istendiğinde izin veriliyor.",
 "zh":"Studio 默认生成无文字视觉，仅在用户明确要求时加入可见文字。",
 "ar":"ينشئ Studio صوراً بلا نص افتراضياً، ولا يضيف كتابة مرئية إلا بطلب صريح.",
 "hi":"Studio अब default रूप से text-free visuals बनाता है; visible text केवल explicit request पर आता है।"},
{"id":"20260921-web-studio","date":"2026-09-21","type":"new","areas":["studio","web"],
 "en":"Direct Web Studio generation, preview, download and MUBA TWT handoff became available on the website.",
 "tr":"Web sitesinde doğrudan Studio üretimi, önizleme, indirme ve MUBA TWT'ye geçiş kullanıma açıldı.",
 "zh":"网站现已支持直接 Studio 生成、预览、下载并进入 MUBA TWT。",
 "ar":"أصبح إنشاء Studio المباشر والمعاينة والتنزيل والانتقال إلى MUBA TWT متاحاً على الموقع.",
 "hi":"Website पर direct Studio generation, preview, download और MUBA TWT handoff उपलब्ध हुआ।"},
{"id":"20260921-guardian-history","date":"2026-09-21","type":"updated","areas":["guardian","telegram"],
 "en":"Guardian violation history and quieter DEV reporting were added.",
 "tr":"Guardian ihlal geçmişi ve daha sessiz DEV raporlama sistemi eklendi.",
 "zh":"新增 Guardian 违规历史与更安静的 DEV 报告方式。",
 "ar":"تمت إضافة سجل مخالفات Guardian وتقارير DEV أكثر هدوءاً.",
 "hi":"Guardian violation history और quieter DEV reporting जोड़े गए।"},
{"id":"20260921-daily-log","date":"2026-09-21","type":"updated","areas":["daily","assistant"],
 "en":"MUBA Daily gained a preserved Development Log with categorized history.",
 "tr":"MUBA Daily'ye kategorili geçmişi koruyan Geliştirme Günlüğü eklendi.",
 "zh":"MUBA Daily 新增保留历史的分类开发日志。",
 "ar":"تمت إضافة سجل تطوير مصنف ومحفوظ إلى MUBA Daily.",
 "hi":"MUBA Daily में categorized preserved Development Log जोड़ा गया।"},
]

def entries(lang="en",area=None):
    lang=lang if lang in UPDATE_LABELS else "en"
    rows=[item for item in UPDATES if not area or area in item["areas"]]
    return [dict(item,text=item.get(lang,item["en"])) for item in rows]

def latest_id(area=None):
    rows=entries("en",area)
    return rows[0]["id"] if rows else None

def has_unseen(area,seen_id):
    latest=latest_id(area)
    return bool(latest and seen_id!=latest)

def badge_type(area,seen_id):
    if not has_unseen(area,seen_id):
        return ""
    for item in UPDATES:
        if area in item["areas"]:
            return item["type"]
    return "new"
