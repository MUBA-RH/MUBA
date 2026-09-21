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
"x":"आधिकारिक X: @MUBA_RH. MUBA की कहानी, सामुदायिक अपडेट और पुष्टि किए गए विकास यहाँ साझा होते हैं।",
"web":"आधिकारिक वेबसाइट: muba-rh.github.io/MUBA/ — MUBA का सार्वजनिक परियोजना घर और कहानी का स्थान।",
"telegram":"आधिकारिक Telegram: @MUBA_RH. वर्तमान सामुदायिक घोषणाओं के लिए पिन किए गए आधिकारिक संदेश देखें।",
"updates":"नवीनतम सत्यापित निर्माण सारांश: MUBA Assistant निजी चैट में 5 भाषाओं में निर्देशित और स्वाभाविक बातचीत का समर्थन करता है। MUBA Guardian मुख्य समूह को अनधिकृत लिंक, नकली CA, फ़िशिंग और धोखाधड़ी नियंत्रण से सुरक्षित रखता है। आंतरिक GitHub विवरण यहाँ प्रदर्शित नहीं किए जाते।"}
}

def daily_text(lang, section):
    lang=lang if lang in DAILY else "en"
    return DAILY[lang].get(section, DAILY[lang]["updates"])


# Persistent user-facing development log. Keep old entries; append new verified
# changes instead of replacing history.
DEVLOG_LABELS={
"en":{"log":"📜 Development Log","new":"✨ New","updates":"🛠 Updated","fixed":"🧩 Refined","back":"⬅️ Back"},
"tr":{"log":"📜 Geliştirme Günlüğü","new":"✨ Yenilikler","updates":"🛠 Güncellemeler","fixed":"🧩 Düzenlenenler","back":"⬅️ Geri"},
"zh":{"log":"📜 开发日志","new":"✨ 新增","updates":"🛠 更新","fixed":"🧩 调整","back":"⬅️ 返回"},
"ar":{"log":"📜 سجل التطوير","new":"✨ جديد","updates":"🛠 تحديثات","fixed":"🧩 تحسينات","back":"⬅️ رجوع"},
"hi":{"log":"📜 Development Log","new":"✨ नया","updates":"🛠 अपडेट","fixed":"🧩 सुधार","back":"⬅️ वापस"}
}

DEVLOG={
"en":{
"new":[
"2026-09-21 — MUBA Gallery added as a shared archive for Web Studio and Telegram Studio creations.",
"2026-09-21 — Assistant gained a central MUBA Updates flow with per-area NEW/UPDATED/IMPROVED badges.",
"2026-09-21 — Story Mode expanded into a chronological, transparent journey with previous/next navigation.",
"2026-09-21 — CREATE → SHARE added under MUBA Studio with share-ready MUBA-native post examples and copy actions."],
"updates":[
"2026-09-21 — MUBA Studio formats were separated more clearly: Meme, Image, Sticker and Reaction now use distinct visual guidance.",
"2026-09-21 — Origin, Identity, Difference, Purpose, Community and Future received distinct present-day context without collapsing their responsibilities into one another.",
"2026-09-21 — Community Guide expanded into clear destinations so members can choose where to go based on what they want to learn or do."],
"fixed":[
"2026-09-21 — Studio defaults were refined so visible text appears only when explicitly requested.",
"2026-09-21 — Repetitive explanations were separated by topic: roots, identity evolution, practical difference, system purpose, community utility and future value now have different scopes.",
"2026-09-21 — Development history is now preserved as an append-only user-facing log instead of a single replaceable summary."]
},
"tr":{
"new":[
"2026-09-21 — Web Studio ve Telegram Studio üretimleri için ortak arşiv olarak MUBA Galeri eklendi.",
"2026-09-21 — Assistant içine merkezi MUBA Yenilikleri akışı ve bölüm bazlı YENİ/GÜNCELLENDİ/İYİLEŞTİRİLDİ işaretleri eklendi.",
"2026-09-21 — Hikâye Modu kronolojik ve şeffaf bir yolculuk olarak genişletildi; önceki/sonraki gezinme eklendi.",
"2026-09-21 — MUBA Studio altına ÜRET → PAYLAŞ eklendi; MUBA diline uygun paylaşmaya hazır TWT örnekleri ve kopyalama işlemleri eklendi."],
"updates":[
"2026-09-21 — MUBA Studio formatları daha net ayrıldı: Meme, Image, Sticker ve Reaction artık farklı görsel yönlendirmeler kullanıyor.",
"2026-09-21 — Köken, Kimlik, Farkı, Amaç, Topluluk ve Gelecek bölümlerine birbirinin görevini tekrar etmeyen bugünkü durum katmanları eklendi.",
"2026-09-21 — Topluluk Rehberi, üyenin merak ettiği konuya göre doğru bölüme yönlendiren daha açık bir yapıya genişletildi."],
"fixed":[
"2026-09-21 — Studio varsayılanı, yalnız açıkça istendiğinde görünür yazı üretecek şekilde iyileştirildi.",
"2026-09-21 — Tekrarlayan anlatımlar konu bazında ayrıldı: kökler, kimlik gelişimi, pratik fark, sistem amacı, topluluk faydası ve gelecek değeri artık ayrı kapsamda.",
"2026-09-21 — Geliştirme geçmişi tek bir değiştirilebilir özet yerine geçmişi koruyan kalıcı günlük yapısına dönüştürüldü."]
},
"zh":{
"new":["2026-09-21 — 新增 MUBA Gallery，统一归档 Web Studio 与 Telegram Studio 的作品。","2026-09-21 — Assistant 新增中央 MUBA 更新流，并在相关区域显示新增/更新/改进标记。","2026-09-21 — 故事模式扩展为透明的时间线旅程，并加入上一页/下一页导航。","2026-09-21 — MUBA Studio 下新增“创作 → 分享”，提供符合 MUBA 风格的可分享帖子与复制操作。"],
"updates":["2026-09-21 — MUBA Studio 的 Meme、Image、Sticker 与 Reaction 现在使用更明确区分的视觉生成指导。","2026-09-21 — 起源、身份、独特之处、目标、社区与未来加入各自独立的当前状态内容，避免职责重复。","2026-09-21 — 社区指南扩展为按成员想了解或想做的事情进行明确引导。"],
"fixed":["2026-09-21 — Studio 默认生成无可见文字，只有明确要求文字时才允许加入。","2026-09-21 — 重复说明按主题拆分：根基、身份演变、实际差异、系统目标、社区价值与未来价值各自独立。","2026-09-21 — 开发历史改为保留旧记录的持续日志，不再只是可被替换的单一摘要。"]},
"ar":{
"new":["2026-09-21 — تمت إضافة MUBA Gallery كأرشيف مشترك لإبداعات Web Studio وTelegram Studio.","2026-09-21 — تمت إضافة مركز تحديثات MUBA مع علامات جديد/محدّث/محسّن للأقسام ذات الصلة.","2026-09-21 — تم توسيع وضع القصة إلى رحلة زمنية شفافة مع أزرار السابق/التالي.","2026-09-21 — تمت إضافة «أنشئ → شارك» أسفل MUBA Studio مع منشورات جاهزة بروح MUBA وخيارات نسخ."],
"updates":["2026-09-21 — أصبحت أنماط Meme وImage وSticker وReaction في MUBA Studio أكثر تميزاً من خلال توجيه بصري خاص بكل نوع.","2026-09-21 — تمت إضافة سياق حالي منفصل للنشأة والهوية والاختلاف والهدف والمجتمع والمستقبل دون تكرار نفس الدور.","2026-09-21 — تم توسيع دليل المجتمع ليوجه العضو إلى القسم الصحيح حسب ما يريد معرفته أو فعله."],
"fixed":["2026-09-21 — تم تحسين Studio ليكون بلا نص مرئي افتراضياً، ولا يسمح بالكتابة إلا بطلب صريح.","2026-09-21 — تم فصل الشروحات المتكررة حسب الموضوع: الجذور وتطور الهوية والاختلاف العملي وهدف النظام وفائدة المجتمع وقيمة المستقبل.","2026-09-21 — أصبح تاريخ التطوير سجلاً مستمراً يحتفظ بالماضي بدلاً من ملخص واحد قابل للاستبدال."]},
"hi":{
"new":["2026-09-21 — Web Studio और Telegram Studio creations के shared archive के रूप में MUBA Gallery जोड़ी गई।","2026-09-21 — Assistant में central MUBA Updates flow और संबंधित sections पर NEW/UPDATED/IMPROVED badges जोड़े गए।","2026-09-21 — Story Mode को transparent chronological journey बनाया गया और previous/next navigation जोड़ी गई।","2026-09-21 — MUBA Studio के नीचे CREATE → SHARE जोड़ा गया, MUBA-native share-ready posts और copy actions के साथ।"],
"updates":["2026-09-21 — MUBA Studio के Meme, Image, Sticker और Reaction formats को अलग visual guidance के साथ अधिक स्पष्ट किया गया।","2026-09-21 — Origin, Identity, Difference, Purpose, Community और Future में अलग-अलग present-day context जोड़ा गया ताकि roles repeat न हों।","2026-09-21 — Community Guide को user की जरूरत के अनुसार सही section तक पहुँचाने के लिए expand किया गया।"],
"fixed":["2026-09-21 — Studio default को text-free बनाया गया; visible writing केवल explicit request पर आती है।","2026-09-21 — Repetitive explanations को topic scope में अलग किया गया: roots, identity evolution, practical difference, system purpose, community utility और future value।","2026-09-21 — Development history अब replaceable summary नहीं, past preserve करने वाला append-only log है।"]}
}

def devlog_page(lang, category, index):
    lang=lang if lang in DEVLOG else "en"
    category=category if category in DEVLOG[lang] else "updates"
    rows=DEVLOG[lang][category]
    index=max(0,min(index,len(rows)-1))
    return rows[index], index, len(rows)
