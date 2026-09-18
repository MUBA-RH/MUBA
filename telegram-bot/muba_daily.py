"""MUBA Daily: verified, user-facing project updates for private Assistant.

This module intentionally exposes summaries, not GitHub internals.
Live-source adapters can replace these snapshots later without changing Guardian.
"""

DAILY_LABELS={
"en":{"daily":"📰 MUBA Daily","x":"🐦 X","web":"🌐 Website","telegram":"📌 Telegram","updates":"🛠 Updates","back":"⬅️ Back"},
"tr":{"daily":"📰 MUBA Daily","x":"🐦 X","web":"🌐 Web Sitesi","telegram":"📌 Telegram","updates":"🛠 Güncellemeler","back":"⬅️ Geri"},
"zh":{"daily":"📰 MUBA Daily","x":"🐦 X","web":"🌐 网站","telegram":"📌 Telegram","updates":"🛠 更新","back":"⬅️ 返回"},
"ar":{"daily":"📰 MUBA Daily","x":"🐦 X","web":"🌐 الموقع","telegram":"📌 Telegram","updates":"🛠 التحديثات","back":"⬅️ رجوع"},
"hi":{"daily":"📰 MUBA Daily","x":"🐦 X","web":"🌐 वेबसाइट","telegram":"📌 Telegram","updates":"🛠 अपडेट्स","back":"⬅️ वापस"},
}

DAILY={
"en":{
"x":"Official X: @MUBA_RH. MUBA shares its story, community updates and confirmed developments there.",
"web":"Official website: muba-rh.github.io/MUBA/ — MUBA's public project home and story.",
"telegram":"Official Telegram: @MUBA_RH. Check the pinned official messages there for current community announcements.",
"updates":"Latest verified build summary: MUBA Assistant supports private guided and natural conversation in 5 languages. MUBA Guardian protects the main group with link, fake-CA, phishing and scam controls. Internal GitHub details are intentionally not exposed here."},
"tr":{
"x":"Resmi X: @MUBA_RH. MUBA'nın hikâyesi, topluluk gelişmeleri ve doğrulanmış yenilikler burada paylaşılır.",
"web":"Resmi web sitesi: muba-rh.github.io/MUBA/ — MUBA'nın herkese açık proje evi ve hikâye alanı.",
"telegram":"Resmi Telegram: @MUBA_RH. Güncel topluluk duyuruları için sabitlenmiş resmi mesajları kontrol edebilirsin.",
"updates":"Son doğrulanmış geliştirme özeti: MUBA Assistant özel sohbette 5 dilde butonlu ve doğal konuşmayı destekliyor. MUBA Guardian ana grubu link, sahte CA, phishing ve scam kontrolleriyle koruyor. Dahili GitHub ayrıntıları burada gösterilmez."},
"zh":{
"x":"官方 X：@MUBA_RH。MUBA 的故事、社区动态和已确认进展会在这里发布。",
"web":"官方网站：muba-rh.github.io/MUBA/ — MUBA 的公开项目主页与故事空间。",
"telegram":"官方 Telegram：@MUBA_RH。当前社区公告请查看其中置顶的官方消息。",
"updates":"最新已确认构建摘要：MUBA Assistant 在私聊中支持 5 种语言的引导式与自然对话。MUBA Guardian 通过链接、假 CA、钓鱼和诈骗控制保护主群。这里不会公开内部 GitHub 细节。"},
"ar":{
"x":"حساب X الرسمي: @MUBA_RH. تُنشر هناك قصة MUBA وتحديثات المجتمع والتطورات المؤكدة.",
"web":"الموقع الرسمي: muba-rh.github.io/MUBA/ — الصفحة العامة للمشروع وقصة MUBA.",
"telegram":"Telegram الرسمي: @MUBA_RH. راجع الرسائل الرسمية المثبتة للحصول على إعلانات المجتمع الحالية.",
"updates":"آخر ملخص مؤكد: يدعم MUBA Assistant المحادثة الخاصة الموجهة والطبيعية بخمس لغات. ويحمي MUBA Guardian المجموعة الرئيسية من الروابط غير المصرح بها وCA المزيف والتصيد والاحتيال. لا تُعرض تفاصيل GitHub الداخلية هنا."},
"hi":{
"x":"Official X: @MUBA_RH. MUBA की story, community updates और confirmed developments यहाँ share होते हैं।",
"web":"Official website: muba-rh.github.io/MUBA/ — MUBA का public project home और story space.",
"telegram":"Official Telegram: @MUBA_RH. Current community announcements के लिए pinned official messages देखें।",
"updates":"Latest verified build summary: MUBA Assistant private chat में 5 languages में guided और natural conversation support करता है। MUBA Guardian main group को links, fake CA, phishing और scam controls से protect करता है। Internal GitHub details यहाँ expose नहीं किए जाते।"}
}

def daily_text(lang, section):
    lang=lang if lang in DAILY else "en"
    return DAILY[lang].get(section, DAILY[lang]["updates"])
