"""Isolated private-Assistant feature modes.

No Guardian imports or moderation actions live here.
"""
import re
from urllib.parse import urlparse

LABELS={
"en":{"story":"📖 Story Mode","lab":"🎨 Content Lab","guide":"🧭 Community Guide","security":"🔎 Security Check","back":"⬅️ Back"},
"tr":{"story":"📖 Hikâye Modu","lab":"🎨 İçerik Laboratuvarı","guide":"🧭 Topluluk Rehberi","security":"🔎 Güvenlik Kontrolü","back":"⬅️ Geri"},
"zh":{"story":"📖 故事模式","lab":"🎨 内容实验室","guide":"🧭 社区指南","security":"🔎 安全检查","back":"⬅️ 返回"},
"ar":{"story":"📖 وضع القصة","lab":"🎨 مختبر المحتوى","guide":"🧭 دليل المجتمع","security":"🔎 فحص الأمان","back":"⬅️ رجوع"},
"hi":{"story":"📖 कहानी मोड","lab":"🎨 सामग्री प्रयोगशाला","guide":"🧭 समुदाय मार्गदर्शिका","security":"🔎 सुरक्षा जाँच","back":"⬅️ वापस"},
}

STORY={
"en":["MUBA did not begin with a complicated roadmap. First there was a character, appearing naturally inside meme-world chaos.","People saw MUBA, shared the character and started creating around it. A community formed without a prewritten legend.","That community gave the character a living culture: participation, creativity, humor and consistency became more important than grand promises.","The idea stayed simple: “I'm MUBA.” The story is not treated as finished; it develops through what the community actually does.","Today MUBA has a public home, a private Assistant and a Guardian for the main group. The next chapter remains open: We Live Here Now. "],
"tr":["MUBA karmaşık bir roadmap ile başlamadı. Önce meme dünyasının doğal kaosu içinde ortaya çıkan bir karakter vardı.","İnsanlar MUBA'yı gördü, paylaştı ve karakter etrafında içerik üretmeye başladı. Önceden yazılmış bir efsane olmadan topluluk oluştu.","Bu topluluk karaktere yaşayan bir kültür kazandırdı: katılım, yaratıcılık, mizah ve istikrar büyük vaatlerden daha önemli hale geldi.","Fikir sade kaldı: “Ben MUBA.” Hikâye bitmiş kabul edilmiyor; topluluğun gerçekten yaptıklarıyla gelişiyor.","Bugün MUBA'nın herkese açık bir evi, özel Assistant'ı ve ana grup için Guardian'ı var. Sonraki bölüm hâlâ açık: We Live Here Now. "],
"zh":["MUBA 并不是从复杂路线图开始的。最初只是一个自然出现在 meme 世界混沌中的角色。","人们看见 MUBA、分享它并围绕角色开始创作。没有预写传奇，社区逐渐形成。","社区让角色拥有了活的文化：参与、创造力、幽默和持续建设比宏大承诺更重要。","核心一直很简单：“I'm MUBA.” 故事没有被视为完成，而是随着社区真实的行动继续发展。","今天 MUBA 有公开主页、私聊 Assistant，以及保护主群的 Guardian。下一章仍然开放：We Live Here Now. "],
"ar":["لم يبدأ MUBA بخارطة طريق معقدة. في البداية كانت هناك شخصية ظهرت طبيعياً وسط فوضى عالم الميم.","رأى الناس MUBA وشاركوه وبدأوا بصنع محتوى حوله. تشكّل المجتمع دون أسطورة مكتوبة مسبقاً.","منح المجتمع الشخصية ثقافة حية؛ أصبحت المشاركة والإبداع والفكاهة والاستمرارية أهم من الوعود الكبيرة.","بقيت الفكرة بسيطة: “I'm MUBA.” القصة ليست منتهية؛ بل تتطور بما يفعله المجتمع فعلاً.","اليوم لدى MUBA بيت عام وAssistant خاص وGuardian للمجموعة الرئيسية. الفصل التالي ما زال مفتوحاً: We Live Here Now. "],
"hi":["MUBA किसी जटिल roadmap से शुरू नहीं हुआ। पहले meme-world की प्राकृतिक chaos में उभरा एक character था।","लोगों ने MUBA को देखा, share किया और उसके आसपास content बनाना शुरू किया। बिना prewritten legend के community बनी।","Community ने character को living culture दिया: participation, creativity, humor और consistency बड़े promises से ज्यादा महत्वपूर्ण बने।","Idea simple रहा: “I'm MUBA.” Story को finished नहीं माना जाता; community जो वास्तव में करती है उससे यह आगे बढ़ती है।","आज MUBA का public home, private Assistant और main group के लिए Guardian है। अगला chapter खुला है: We Live Here Now. "],
}

LAB={
"en":{"meme":"Meme idea: MUBA walks into meme-world chaos, looks around and simply says: “We live here now.” Keep the character recognizable and let the situation carry the joke.","tweet":"Tweet seed: No grand legend was waiting for MUBA. The character arrived first. The community gave it a place to live. ","visual":"Visual idea: 16:9. MUBA at the edge of a huge neon meme city, black MUBA cap and $MUBA hoodie, looking toward the next district. Minimal text: WE LIVE HERE NOW."},
"tr":{"meme":"Meme fikri: MUBA meme dünyasının kaosuna girer, etrafına bakar ve sadece “We live here now.” der. Karakter tanınır kalsın; mizahı sahne taşısın.","tweet":"Tweet tohumu: MUBA'yı bekleyen büyük bir efsane yoktu. Önce karakter geldi. Ona yaşayacağı yeri topluluk verdi. ","visual":"Görsel fikri: 16:9. Siyah MUBA şapkası ve $MUBA hoodie'siyle dev neon meme şehrinin kenarında duran MUBA, sonraki bölgeye bakıyor. Minimum yazı: WE LIVE HERE NOW."},
"zh":{"meme":"Meme 点子：MUBA 走进混乱的 meme 世界，看了一圈，只说：“We live here now.” 保持角色辨识度，让场景本身制造幽默。","tweet":"Tweet 灵感：没有宏大传奇在等待 MUBA。角色先出现，社区给了它一个可以生活的地方。","visual":"视觉点子：16:9。MUBA 戴黑色 MUBA 帽、穿 $MUBA hoodie，站在巨大霓虹 meme 城市边缘，看向下一个街区。最少文字：WE LIVE HERE NOW."},
"ar":{"meme":"فكرة ميم: يدخل MUBA إلى فوضى عالم الميم، ينظر حوله ويقول فقط: “We live here now.” حافظ على شكل الشخصية واجعل الموقف يحمل النكتة.","tweet":"بذرة تغريدة: لم تكن هناك أسطورة ضخمة تنتظر MUBA. جاءت الشخصية أولاً، ثم منحها المجتمع مكاناً تعيش فيه. ","visual":"فكرة بصرية: 16:9. MUBA بقبعته السوداء وhoodie $MUBA على حافة مدينة ميم نيون ضخمة وينظر إلى الحي التالي. نص قليل: WE LIVE HERE NOW."},
"hi":{"meme":"Meme idea: MUBA meme-world chaos में आता है, चारों ओर देखता है और बस कहता है: “We live here now.” Character recognizable रहे और joke scene से आए।","tweet":"Tweet seed: MUBA के लिए कोई grand legend इंतजार नहीं कर रही थी। Character पहले आया। Community ने उसे रहने की जगह दी। ","visual":"Visual idea: 16:9. Black MUBA cap और $MUBA hoodie में MUBA एक विशाल neon meme city के किनारे खड़ा अगले district की ओर देख रहा है। Minimal text: WE LIVE HERE NOW."},
}

GUIDE={
"en":["1/4 — Start with the character: MUBA is an original meme character and community identity.","2/4 — Learn the culture: character, creativity, participation, community and consistency come before grand promises.","3/4 — Use official sources: X @MUBA_RH, Telegram @MUBA_RH and muba-rh.github.io/MUBA/.","4/4 — Stay safe: no official CA is published yet. Do not trust unofficial contract addresses. In the main group Guardian handles security; here Assistant explains MUBA."],
"tr":["1/4 — Karakterden başla: MUBA özgün bir meme karakteri ve topluluk kimliğidir.","2/4 — Kültürü tanı: büyük vaatlerden önce karakter, yaratıcılık, katılım, topluluk ve istikrar gelir.","3/4 — Resmi kaynakları kullan: X @MUBA_RH, Telegram @MUBA_RH ve muba-rh.github.io/MUBA/.","4/4 — Güvende kal: henüz resmi CA yayımlanmadı. Resmi olmayan kontrat adreslerine güvenme. Ana grupta güvenliği Guardian yürütür; burada Assistant MUBA'yı açıklar."],
"zh":["1/4 — 从角色开始：MUBA 是原创 meme 角色和社区身份。","2/4 — 了解文化：角色、创造力、参与、社区和持续建设先于宏大承诺。","3/4 — 使用官方来源：X @MUBA_RH、Telegram @MUBA_RH 和 muba-rh.github.io/MUBA/。","4/4 — 注意安全：官方 CA 尚未发布。不要相信非官方合约地址。主群由 Guardian 负责安全，这里由 Assistant 解释 MUBA。"],
"ar":["1/4 — ابدأ بالشخصية: MUBA شخصية ميم أصلية وهوية مجتمع.","2/4 — تعرّف على الثقافة: الشخصية والإبداع والمشاركة والمجتمع والاستمرارية قبل الوعود الكبيرة.","3/4 — استخدم المصادر الرسمية: X @MUBA_RH وTelegram @MUBA_RH و muba-rh.github.io/MUBA/.","4/4 — ابق آمناً: لم يتم نشر CA رسمي بعد. لا تثق بعناوين العقود غير الرسمية. Guardian يحمي المجموعة الرئيسية وAssistant يشرح MUBA هنا."],
"hi":["1/4 — Character से शुरू करें: MUBA एक original meme character और community identity है।","2/4 — Culture समझें: grand promises से पहले character, creativity, participation, community और consistency आते हैं।","3/4 — Official sources इस्तेमाल करें: X @MUBA_RH, Telegram @MUBA_RH और muba-rh.github.io/MUBA/.","4/4 — Safe रहें: official CA अभी publish नहीं हुआ है। Unofficial contract addresses पर भरोसा न करें। Main group में Guardian security संभालता है; यहाँ Assistant MUBA समझाता है।"],
}

SECURITY_PROMPT={
"en":"Send a MUBA link or contract address in your next message. I will compare it only with the currently registered official MUBA sources. I do not moderate users here.",
"tr":"Sonraki mesajında bir MUBA linki veya kontrat adresi gönder. Yalnızca kayıtlı resmi MUBA kaynaklarıyla karşılaştıracağım. Burada kullanıcı moderasyonu yapmıyorum.",
"zh":"下一条消息发送 MUBA 链接或合约地址。我只会与当前登记的官方 MUBA 来源比较。这里不会执行用户管理。",
"ar":"أرسل رابط MUBA أو عنوان عقد في رسالتك التالية. سأقارنه فقط بمصادر MUBA الرسمية المسجلة حالياً. لا أقوم بإدارة المستخدمين هنا.",
"hi":"अगले संदेश में MUBA लिंक या अनुबंध पता भेजें। मैं इसे केवल पंजीकृत आधिकारिक MUBA स्रोतों से मिलाऊँगा। यहाँ उपयोगकर्ता मॉडरेशन नहीं होता।",
}
OFFICIAL_HOST_PATH={("muba-rh.github.io","/MUBA"),("x.com","/MUBA_RH"),("t.me","/MUBA_RH")}
_ADDR=re.compile(r"^(?:0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})$")

def security_check(lang, value):
    lang=lang if lang in LABELS else "en"
    v=(value or "").strip()
    low=v.casefold()
    if low in ("@muba_rh","muba-rh.github.io/muba/","muba-rh.github.io/muba"):
        ok=True
    else:
        raw=v if "://" in v else ("https://"+v if "." in v else "")
        ok=False
        if raw:
            try:
                p=urlparse(raw); host=(p.hostname or "").casefold(); path=p.path.rstrip("/") or "/"
                ok=(host,path) in {(h.casefold(),pa) for h,pa in OFFICIAL_HOST_PATH} and not p.username and not p.password
            except ValueError: ok=False
    if ok:
        return {"en":"✅ Official MUBA source.","tr":"✅ Resmi MUBA kaynağı.","zh":"✅ MUBA 官方来源。","ar":"✅ مصدر MUBA رسمي.","hi":"✅ आधिकारिक MUBA स्रोत।"}[lang]
    if _ADDR.fullmatch(v):
        return {"en":"⚠️ No official MUBA CA is published yet. This address cannot be verified as official.","tr":"⚠️ Henüz resmi MUBA CA yayımlanmadı. Bu adres resmi olarak doğrulanamaz.","zh":"⚠️ MUBA 官方 CA 尚未发布。此地址无法验证为官方地址。","ar":"⚠️ لم يتم نشر CA رسمي لـ MUBA بعد. لا يمكن التحقق من هذا العنوان كعنوان رسمي.","hi":"⚠️ आधिकारिक MUBA CA अभी प्रकाशित नहीं हुआ है। इस पते को आधिकारिक रूप से सत्यापित नहीं किया जा सकता।"}[lang]
    return {"en":"❌ This is not a registered official MUBA source.","tr":"❌ Bu, kayıtlı resmi bir MUBA kaynağı değil.","zh":"❌ 这不是已登记的 MUBA 官方来源。","ar":"❌ هذا ليس مصدراً رسمياً مسجلاً لـ MUBA.","hi":"❌ यह पंजीकृत आधिकारिक MUBA स्रोत नहीं है।"}[lang]


# --- MUBA content evolution layer (2026-09-21) ---
# Keeps the original Assistant catalogue intact while extending each mode with
# distinct, non-duplicated responsibilities.

STORY={
"en":[
"1/8 — Before the system\nMUBA began as a character, not as a finished project story. There was no prewritten legend waiting for people to follow.",
"2/8 — The first movement\nPeople saw the character, shared it, reacted to it and started creating around it. The story began through real participation, not through a script.",
"3/8 — A culture appeared\nRepeated participation created recognizable habits: original MUBA content, meme-native humor, consistency and the idea that MUBA should stay unmistakably MUBA.",
"4/8 — Community became structure\nWhat started as interaction became an organized community space. The need shifted from simply seeing MUBA to understanding it, discussing it and creating with it.",
"5/8 — Knowledge became accessible\nMUBA Assistant was built so members could explore the character, culture and verified project information in five languages without depending on one person to explain everything.",
"6/8 — Safety became part of the story\nGuardian added a dedicated security layer for the main group. Assistant and Guardian were kept separate: one explains and interacts; the other protects the group.",
"7/8 — Creation became a tool\nMUBA Studio and the content tools turned participation into something practical: members can move from learning about MUBA to producing and sharing MUBA-native ideas.",
"8/8 — Where the story is now\nThe story is still not prewritten. The difference is that MUBA now has a stronger structure for knowledge, conversation, security and creation. What happens next is built from what the community actually does. We Live Here Now. "],
"tr":[
"1/8 — Sistemden önce\nMUBA bitmiş bir proje hikâyesi olarak değil, bir karakter olarak başladı. İnsanların takip etmesi için önceden yazılmış bir efsane yoktu.",
"2/8 — İlk hareket\nİnsanlar karakteri gördü, paylaştı, tepki verdi ve etrafında içerik üretmeye başladı. Hikâye bir senaryodan değil, gerçek katılımdan doğdu.",
"3/8 — Kültür oluştu\nTekrarlanan katılım; özgün MUBA içerikleri, meme-native mizah, istikrar ve MUBA'nın her zaman MUBA olarak kalması fikrini görünür hale getirdi.",
"4/8 — Topluluk yapıya dönüştü\nBaşta yalnızca etkileşim olan şey düzenli bir topluluk alanına dönüştü. İhtiyaç artık sadece MUBA'yı görmek değil; anlamak, konuşmak ve onunla üretmekti.",
"5/8 — Bilgi erişilebilir hale geldi\nMUBA Assistant, üyelerin karakteri, kültürü ve doğrulanmış proje bilgisini beş dilde öğrenebilmesi için kuruldu; herkesin tek bir kişiden açıklama beklemesi gerekmiyor.",
"6/8 — Güvenlik hikâyenin parçası oldu\nGuardian ana grup için ayrı bir güvenlik katmanı ekledi. Assistant ile Guardian ayrıldı: biri anlatır ve etkileşir, diğeri grubu korur.",
"7/8 — Üretim araca dönüştü\nMUBA Studio ve içerik araçları katılımı pratik hale getirdi: topluluk artık MUBA'yı öğrenmekten MUBA'ya uygun içerik üretip paylaşmaya geçebiliyor.",
"8/8 — Hikâyenin bugünkü noktası\nHikâye hâlâ önceden yazılmış değil. Fark şu: MUBA artık bilgi, sohbet, güvenlik ve üretim için daha güçlü bir düzene sahip. Sonraki bölüm, topluluğun gerçekten yaptıklarıyla oluşacak. We Live Here Now. "],
"zh":[
"1/8 — 系统之前\nMUBA 最初是一个角色，而不是一套完成的项目故事。没有预先写好的传奇要求大家照着走。",
"2/8 — 最初的推动\n人们看到角色、分享、回应并围绕它创作。故事来自真实参与，而不是脚本。",
"3/8 — 文化形成\n持续参与逐渐形成清晰习惯：原创 MUBA 内容、meme-native 幽默、持续建设，以及让 MUBA 始终保持自身身份。",
"4/8 — 社区变成结构\n最初的互动逐渐成为有组织的社区空间。需求从“看到 MUBA”变成“理解、讨论并与 MUBA 一起创作”。",
"5/8 — 知识变得可访问\nMUBA Assistant 让成员能用五种语言了解角色、文化和已验证项目信息，而不必依赖某一个人解释一切。",
"6/8 — 安全成为故事的一部分\nGuardian 为主群加入独立安全层。Assistant 与 Guardian 分工：一个负责解释与互动，另一个负责保护群组。",
"7/8 — 创作变成工具\nMUBA Studio 和内容工具让参与更实际：成员可以从了解 MUBA 进一步到制作并分享符合 MUBA 气质的内容。",
"8/8 — 故事现在的位置\n故事依然不是预先写好的。不同的是，MUBA 现在拥有更完整的知识、对话、安全和创作结构。下一章来自社区真实做出的事情。We Live Here Now. "],
"ar":[
"1/8 — قبل النظام\nبدأ MUBA كشخصية، لا كقصة مشروع مكتملة. لم تكن هناك أسطورة مكتوبة مسبقاً ليتبعها الناس.",
"2/8 — الحركة الأولى\nرأى الناس الشخصية وشاركوها وتفاعلوا معها وبدأوا بصنع محتوى حولها. بدأت القصة من المشاركة الحقيقية لا من نص جاهز.",
"3/8 — ظهور الثقافة\nصنعت المشاركة المستمرة عادات واضحة: محتوى MUBA أصلي، فكاهة meme-native، استمرارية، والحفاظ على MUBA كهوية مستقلة.",
"4/8 — المجتمع أصبح بنية\nتحول التفاعل إلى مساحة مجتمع منظمة. لم يعد المطلوب مجرد رؤية MUBA، بل فهمه والحديث عنه والإبداع معه.",
"5/8 — أصبحت المعرفة متاحة\nتم بناء MUBA Assistant ليتمكن الأعضاء من استكشاف الشخصية والثقافة والمعلومات الموثقة بخمس لغات دون الاعتماد على شخص واحد لشرح كل شيء.",
"6/8 — أصبح الأمان جزءاً من القصة\nأضاف Guardian طبقة أمان مستقلة للمجموعة الرئيسية. تم فصل Assistant عن Guardian: الأول يشرح ويتفاعل، والثاني يحمي المجموعة.",
"7/8 — أصبح الإبداع أداة\nحوّل MUBA Studio وأدوات المحتوى المشاركة إلى شيء عملي: يمكن للأعضاء الانتقال من معرفة MUBA إلى إنتاج ومشاركة أفكار بروح MUBA.",
"8/8 — أين وصلت القصة\nالقصة ما زالت غير مكتوبة مسبقاً. الجديد أن MUBA يملك الآن بنية أقوى للمعرفة والمحادثة والأمان والإبداع. الفصل القادم يتشكل مما يفعله المجتمع فعلاً. We Live Here Now. "],
"hi":[
"1/8 — सिस्टम से पहले\nMUBA एक character के रूप में शुरू हुआ, किसी finished project story के रूप में नहीं। लोगों के follow करने के लिए कोई prewritten legend नहीं थी।",
"2/8 — पहली movement\nलोगों ने character देखा, share किया, react किया और उसके आसपास content बनाना शुरू किया। Story script से नहीं, real participation से बनी।",
"3/8 — Culture बना\nलगातार participation से original MUBA content, meme-native humor, consistency और MUBA को हमेशा अपनी identity में रखने की आदत बनी।",
"4/8 — Community structure बनी\nInteraction धीरे-धीरे organized community space में बदला। अब जरूरत सिर्फ MUBA को देखने की नहीं, उसे समझने, discuss करने और उसके साथ create करने की थी।",
"5/8 — Knowledge accessible हुआ\nMUBA Assistant इसलिए बनाया गया कि members पाँच भाषाओं में character, culture और verified project information समझ सकें, बिना हर बात के लिए एक व्यक्ति पर निर्भर हुए।",
"6/8 — Security story का हिस्सा बनी\nGuardian main group के लिए अलग security layer बना। Assistant और Guardian अलग रहे: एक explain और interact करता है, दूसरा group protect करता है।",
"7/8 — Creation tool बनी\nMUBA Studio और content tools participation को practical बनाते हैं: members MUBA को सीखने से आगे बढ़कर MUBA-native ideas बना और share कर सकते हैं।",
"8/8 — Story आज कहाँ है\nStory अभी भी prewritten नहीं है। फर्क यह है कि अब MUBA के पास knowledge, conversation, security और creation की मजबूत structure है। अगला chapter community के असली actions से बनेगा। We Live Here Now. "]
}

TOPIC_PROGRESS={
"en":{
"origin":[("🌱 Roots today","MUBA's roots are not a hidden mythology. They are visible in the order that actually happened: character first, participation second, community third, structure later. The written story follows those events; it does not manufacture a past that never existed."),("🧱 What stayed unchanged","The core has stayed simple through every new layer: MUBA remains an original character, the culture grows through participation, and confirmed facts stay separate from invented lore.")],
"identity":[("👤 How identity formed","MUBA's identity formed through repetition: the same recognizable character, the same refusal to become a copy of another meme mascot, and a community that kept creating around that identity."),("📍 Identity today","Today MUBA is both the original character and the culture around it. Assistant, Guardian and Studio support that identity, but none of those tools replace MUBA itself.")],
"difference":[("🛠 From idea to reality","The difference is now visible in the system itself: MUBA did not stop at saying 'community'. Knowledge access, five-language interaction, security and creative tools were built around actual community use."),("🔗 One ecosystem, separate roles","Assistant explains, Guardian protects, Studio helps creation and the public channels carry the story. Keeping these roles separate makes the ecosystem clearer instead of turning everything into one generic bot."),(" Lived, not scripted","The project history is documented after developments happen. The story grows from real changes and community behavior instead of forcing events to match a prewritten legend.")],
"purpose":[("🎯 Why this system exists","The current system was built so people can talk about MUBA, learn about it and participate without every question or routine interaction depending on a human moderator."),("⚙️ Self-sufficient direction","The direction is a more self-sufficient ecosystem: Assistant handles knowledge and conversation, Guardian handles defined security work, and community tools help members create. Human control still exists where authority is required, but routine dependency is reduced.")],
"community":[("👥 What members gain","Members get a clearer way to learn MUBA, find the right official area, ask questions in their own supported language, stay safer in the main group and move directly into creation."),(" What members can do","They can explore the story, ask MUBA questions, create memes or visual ideas, use share-ready post examples, contribute original content and help the culture grow through participation rather than passive watching.")],
"plan":[("🧭 Why today's system matters tomorrow","Every stable layer reduces future rebuilding. A documented knowledge base, five-language access, separated security and creative tools give future MUBA developments a structure they can extend instead of restarting from zero."),("🏗 Build forward without rewriting the past","Future growth can add new verified information, tools and community functions while keeping the original identity intact. The system is designed to evolve by addition and validation, not by constantly replacing its foundation.")],
},
"tr":{
"origin":[("🌱 Bugünkü kökler","MUBA'nın kökeni gizli bir mitoloji değil. Gerçekte gerçekleşen sıra açık: önce karakter, sonra katılım, ardından topluluk ve daha sonra sistemleşme. Yazılan hikâye bu olayları takip eder; hiç yaşanmamış bir geçmiş üretmez."),("🧱 Değişmeyen temel","Yeni katmanlar eklense de öz aynı kaldı: MUBA özgün karakterdir, kültür katılımla büyür ve doğrulanmış bilgiler uydurma hikâyelerden ayrı tutulur.")],
"identity":[("👤 Kimlik nasıl oluştu","MUBA'nın kimliği tekrar ve tutarlılıkla oluştu: aynı tanınabilir karakter, başka meme maskotlarının kopyası olmama çizgisi ve bu kimliğin etrafında üretmeye devam eden topluluk."),("📍 Kimlik bugün","Bugün MUBA hem özgün karakterin kendisi hem de onun çevresinde oluşan kültürdür. Assistant, Guardian ve Studio bu kimliği destekler; hiçbiri MUBA'nın yerine geçmez.")],
"difference":[("🛠 Fikirden gerçeğe","Fark artık sistemin içinde görünür durumda: MUBA yalnızca 'topluluk' demekle kalmadı; bilgi erişimi, beş dilde etkileşim, güvenlik ve üretim araçları gerçek topluluk kullanımının etrafında kuruldu."),("🔗 Tek ekosistem, ayrı görevler","Assistant anlatır, Guardian korur, Studio üretime yardım eder, resmi kanallar hikâyeyi taşır. Görevlerin ayrılması, her şeyi tek ve sıradan bir bota çevirmek yerine sistemi daha anlaşılır yapar."),(" Yazılmadı, yaşandı","Proje geçmişi gelişmeler gerçekleştikten sonra kayda geçer. Hikâye önceden yazılmış bir efsaneye olay uydurmak yerine gerçek değişikliklerden ve topluluk davranışından büyür.")],
"purpose":[("🎯 Bu sistem neden var","Mevcut sistem; insanların MUBA hakkında konuşabilmesi, onu öğrenebilmesi ve katılım gösterebilmesi için kuruldu. Her soru veya rutin etkileşim için sürekli bir insan moderatöre bağlı kalınması amaçlanmıyor."),("⚙️ Kendi kendine yeten yön","Hedef daha fazla kendi kendine yetebilen bir ekosistem: Assistant bilgi ve sohbeti, Guardian tanımlı güvenlik işlerini, topluluk araçları ise üretimi taşır. Yetki gereken yerlerde insan kontrolü korunur; rutin bağımlılık azaltılır.")],
"community":[("👥 Topluluğa faydası","Üyeler MUBA'yı daha net öğrenebilir, doğru resmi bölüme yönlenebilir, desteklenen kendi dilinde soru sorabilir, ana grupta daha güvenli kalabilir ve doğrudan üretime geçebilir."),(" Neler yapabilirler","Hikâyeyi keşfedebilir, MUBA hakkında soru sorabilir, meme veya görsel fikir üretebilir, paylaşmaya hazır gönderi örneklerini kullanabilir, özgün içerikle katkı verebilir ve kültürü yalnızca izlemek yerine katılımla büyütebilirler.")],
"plan":[("🧭 Bugünkü sistem geleceğe neden yarar","Her stabil katman gelecekte aynı şeyi yeniden kurma ihtiyacını azaltır. Belgelenmiş bilgi tabanı, beş dil erişimi, ayrılmış güvenlik ve üretim araçları yeni gelişmelerin sıfırdan başlamak yerine mevcut yapının üzerine kurulmasını sağlar."),("🏗 Geçmişi silmeden ileri inşa","Gelecekte yeni doğrulanmış bilgiler, araçlar ve topluluk fonksiyonları eklenebilir; özgün kimlik korunur. Sistem temeli sürekli değiştirmek için değil, doğrulayarak ve ekleyerek gelişmek için tasarlandı.")],
},
"zh":{
"origin":[("🌱 今天的根基","MUBA 的根基不是隐藏神话，而是实际发生过的顺序：先有角色，再有参与，然后形成社区，最后才有结构。文字故事记录这些事实，不制造不存在的过去。"),("🧱 不变的基础","即使加入新层，核心仍然简单：MUBA 是原创角色，文化通过参与成长，已确认事实与虚构 lore 保持分离。")],
"identity":[("👤 身份如何形成","MUBA 的身份来自持续一致：同一个可识别角色、不成为其他 meme 吉祥物复制品，以及围绕这一身份持续创作的社区。"),("📍 今天的身份","今天 MUBA 既是原创角色，也是围绕它形成的文化。Assistant、Guardian 和 Studio 支持这一身份，但都不会取代 MUBA 本身。")],
"difference":[("🛠 从想法到现实","差异已经体现在系统本身：MUBA 不只是说“社区”，而是围绕真实社区使用建立了知识访问、五语言互动、安全与创作工具。"),("🔗 一个生态，不同职责","Assistant 解释，Guardian 保护，Studio 帮助创作，官方渠道承载故事。职责分离让生态更清晰，而不是把一切塞进一个普通机器人。"),(" 被经历，而非预写","项目历史是在发展发生后记录的。故事来自真实变化和社区行为，而不是让现实去配合预先写好的传奇。")],
"purpose":[("🎯 为什么建立这个系统","当前系统让大家能讨论 MUBA、了解 MUBA 并参与其中，而不需要每个问题或日常互动都依赖人工管理员。"),("⚙️ 更自给的方向","方向是更自给的生态：Assistant 负责知识与交流，Guardian 负责定义好的安全工作，社区工具帮助创作。需要权限的地方仍保留人工控制，但减少日常依赖。")],
"community":[("👥 成员能获得什么","成员能更清楚地了解 MUBA、找到正确官方入口、用支持的语言提问、在主群中更安全，并直接进入创作。"),(" 成员能做什么","可以探索故事、提问、制作 meme 或视觉点子、使用可直接分享的帖子示例、贡献原创内容，并通过参与而不是旁观来推动文化。")],
"plan":[("🧭 今天的系统为何对未来重要","每一个稳定层都减少未来重复建设。文档化知识、五语言访问、独立安全与创作工具，让未来发展可以在现有结构上扩展，而不是从零开始。"),("🏗 不改写过去地继续建设","未来可以加入新的已验证信息、工具和社区功能，同时保持原始身份。系统通过添加与验证演进，而不是不断替换基础。")],
},
"ar":{
"origin":[("🌱 الجذور اليوم","جذور MUBA ليست أسطورة مخفية. الترتيب الحقيقي واضح: الشخصية أولاً، ثم المشاركة، ثم المجتمع، ثم البنية. القصة المكتوبة تتبع ما حدث فعلاً ولا تصنع ماضياً غير موجود."),("🧱 ما بقي ثابتاً","مع إضافة طبقات جديدة بقي الأساس بسيطاً: MUBA شخصية أصلية، والثقافة تنمو بالمشاركة، والمعلومات المؤكدة تبقى منفصلة عن القصص المختلقة.")],
"identity":[("👤 كيف تشكلت الهوية","تكونت هوية MUBA عبر الاستمرارية: نفس الشخصية المميزة، وعدم التحول إلى نسخة من تميمة ميم أخرى، ومجتمع استمر في الإبداع حول هذه الهوية."),("📍 الهوية اليوم","اليوم MUBA هو الشخصية الأصلية والثقافة المحيطة بها. Assistant وGuardian وStudio يدعمون هذه الهوية لكنهم لا يستبدلون MUBA نفسه.")],
"difference":[("🛠 من الفكرة إلى الواقع","الاختلاف ظاهر الآن داخل النظام: لم يكتفِ MUBA بالحديث عن المجتمع؛ بل بُنيت المعرفة والتفاعل بخمس لغات والأمان وأدوات الإبداع حول استخدام المجتمع الحقيقي."),("🔗 منظومة واحدة بأدوار منفصلة","Assistant يشرح، Guardian يحمي، Studio يساعد على الإبداع، والقنوات الرسمية تحمل القصة. فصل الأدوار يجعل المنظومة أوضح بدلاً من وضع كل شيء داخل بوت عام واحد."),(" قصة عاشت ولم تُكتب مسبقاً","يتم توثيق تاريخ المشروع بعد وقوع التطورات. تنمو القصة من التغييرات الحقيقية وسلوك المجتمع لا من إجبار الأحداث على مطابقة أسطورة مكتوبة مسبقاً.")],
"purpose":[("🎯 لماذا يوجد هذا النظام","بُني النظام الحالي لكي يتحدث الناس عن MUBA ويتعلموا عنه ويشاركوا دون أن يعتمد كل سؤال أو تفاعل روتيني على مشرف بشري."),("⚙️ اتجاه أكثر اكتفاءً","الاتجاه هو منظومة أكثر اكتفاءً: Assistant للمعرفة والمحادثة، Guardian لأعمال الأمان المحددة، وأدوات المجتمع للإبداع. يبقى التحكم البشري حيث تتطلب الصلاحية ذلك، بينما تقل التبعية اليومية.")],
"community":[("👥 فائدة المجتمع","يحصل الأعضاء على طريقة أوضح لتعلم MUBA والوصول إلى المكان الرسمي الصحيح وطرح الأسئلة بلغتهم المدعومة والبقاء أكثر أماناً في المجموعة والانتقال مباشرة إلى الإبداع."),(" ماذا يمكنهم أن يفعلوا","يمكنهم استكشاف القصة وطرح الأسئلة وصنع أفكار ميم أو صور واستخدام نماذج منشورات جاهزة للمشاركة والمساهمة بمحتوى أصلي وتنمية الثقافة بالمشاركة بدلاً من المشاهدة فقط.")],
"plan":[("🧭 لماذا يفيد نظام اليوم المستقبل","كل طبقة مستقرة تقلل الحاجة إلى إعادة البناء لاحقاً. المعرفة الموثقة والوصول بخمس لغات وفصل الأمان وأدوات الإبداع تمنح التطورات القادمة بنية يمكن توسيعها بدلاً من البدء من الصفر."),("🏗 البناء للأمام دون إعادة كتابة الماضي","يمكن للمستقبل إضافة معلومات وأدوات ووظائف مجتمع موثقة جديدة مع الحفاظ على الهوية الأصلية. النظام مصمم للتطور بالإضافة والتحقق لا باستبدال أساسه باستمرار.")],
},
"hi":{
"origin":[("🌱 आज की roots","MUBA की roots कोई hidden mythology नहीं हैं। असली क्रम साफ है: character पहले, participation बाद में, फिर community और उसके बाद structure। लिखी गई story उन्हीं events को follow करती है; वह नकली past नहीं बनाती।"),("🧱 जो नहीं बदला","नई layers के बावजूद core simple रहा: MUBA original character है, culture participation से बढ़ता है और verified facts invented lore से अलग रहते हैं।")],
"identity":[("👤 Identity कैसे बनी","MUBA की identity consistency से बनी: वही recognizable character, दूसरे meme mascots की copy न बनने की line और उस identity के आसपास लगातार create करती community।"),("📍 Identity आज","आज MUBA original character भी है और उसके आसपास बनी culture भी। Assistant, Guardian और Studio identity को support करते हैं, लेकिन वे MUBA को replace नहीं करते।")],
"difference":[("🛠 Idea से reality","अब difference system में दिखता है: MUBA ने सिर्फ 'community' नहीं कहा; knowledge access, five-language interaction, security और creation tools real community use के around बनाए गए।"),("🔗 One ecosystem, separate roles","Assistant explain करता है, Guardian protect करता है, Studio creation में मदद करता है और official channels story carry करते हैं। Separate roles ecosystem को clear रखते हैं।"),(" Lived, not scripted","Project history developments होने के बाद document होती है। Story real changes और community behavior से बढ़ती है, prewritten legend को fit करने के लिए events नहीं बनाए जाते।")],
"purpose":[("🎯 यह system क्यों है","Current system इसलिए बनाया गया कि लोग MUBA के बारे में बात कर सकें, सीख सकें और participate कर सकें, बिना हर routine question के लिए human moderator पर depend हुए।"),("⚙️ Self-sufficient direction","Direction ज्यादा self-sufficient ecosystem की है: Assistant knowledge/conversation, Guardian defined security work और community tools creation संभालते हैं। Authority वाली जगह human control रहता है, routine dependency कम होती है।")],
"community":[("👥 Members को क्या मिलता है","Members MUBA को clearer way में समझ सकते हैं, सही official area तक जा सकते हैं, supported language में पूछ सकते हैं, main group में safer रह सकते हैं और creation तक direct पहुँच सकते हैं।"),(" Members क्या कर सकते हैं","Story explore करें, सवाल पूछें, meme/visual ideas बनाएँ, share-ready post examples इस्तेमाल करें, original content contribute करें और passive watching के बजाय participation से culture grow करें।")],
"plan":[("🧭 आज का system future के लिए क्यों जरूरी है","हर stable layer future rebuilding कम करती है। Documented knowledge, five-language access, separated security और creative tools future developments को zero से शुरू करने के बजाय existing structure extend करने देते हैं।"),("🏗 Past मिटाए बिना आगे build","Future में नई verified information, tools और community functions add हो सकती हैं जबकि original identity intact रहे। System addition और validation से evolve करने के लिए बना है, foundation बार-बार replace करने के लिए नहीं।")],
}
}

GUIDE_SECTIONS={
"en":[("🧩 What is MUBA?","Start with Identity if you want the shortest answer to what MUBA is. Use Origin for how it began and Story Mode for the full chronological journey."),("📖 I want the story","Use Story Mode when you want the journey from the first character appearance to today's Assistant, Guardian and Studio structure."),("✨ What makes it different?","Open Difference to see how the non-prewritten, original-character approach became a real working ecosystem rather than only a slogan."),("👥 I want to participate","Open Community to see what members can do, then use MUBA Studio and ÜRET → PAYLAŞ for practical creation and share-ready ideas."),("🔎 I want official/safe information","Use MUBA Daily for official public areas and recent project changes. Use Security Check when you need to verify a MUBA link or contract-like address."),("🧭 I want to know what comes next","Open Future for how today's stable layers support future growth. Confirmed developments are added when they actually exist.")],
"tr":[("🧩 MUBA nedir?","En kısa tanım için Kimlik'e gir. Nasıl başladığını öğrenmek için Köken'i, baştan bugüne kronolojik yolculuk için Hikâye Modu'nu kullan."),("📖 Hikâyeyi öğrenmek istiyorum","İlk karakterden bugünkü Assistant, Guardian ve Studio düzenine kadar olan yolculuk için Hikâye Modu'nu aç."),("✨ Farkı ne?","Önceden yazılmamış ve özgün karakter yaklaşımının yalnızca söz olarak kalmayıp nasıl çalışan bir ekosisteme dönüştüğünü görmek için Farkı bölümünü aç."),("👥 Katılmak istiyorum","Topluluk bölümünde üyelerin neler yapabileceğini gör; ardından pratik üretim ve paylaşmaya hazır fikirler için MUBA Studio ile ÜRET → PAYLAŞ'ı kullan."),("🔎 Resmi/güvenli bilgi arıyorum","Resmi alanlar ve yakın dönem proje değişiklikleri için MUBA Daily'yi kullan. Bir MUBA linkini veya kontrat benzeri adresi kontrol etmek için Güvenlik Kontrolü'nü aç."),("🧭 Bundan sonra ne olacak?","Bugünkü stabil katmanların gelecekteki büyümeyi nasıl desteklediğini görmek için Gelecek bölümünü aç. Yalnızca gerçekten oluşmuş doğrulanmış gelişmeler eklenir.")],
"zh":[("🧩 MUBA 是什么？","想要最简短定义请看“身份”。想知道如何开始请看“起源”，想看完整时间线请进入故事模式。"),("📖 我想看完整故事","故事模式会从最初角色出现一直讲到今天的 Assistant、Guardian 和 Studio 结构。"),("✨ 有什么不同？","进入“独特之处”，查看原创角色和非预写故事的方法如何变成真正运行的生态，而不是只停留在口号。"),("👥 我想参与","先看“社区”了解成员能做什么，再使用 MUBA Studio 与“创作 → 分享”获取实际创作与可分享内容。"),("🔎 我需要官方/安全信息","MUBA Daily 用于官方公开区域与近期项目变更。需要检查 MUBA 链接或类似合约地址时使用安全检查。"),("🧭 我想知道未来","进入“未来”查看今天的稳定结构如何支持后续增长。只有真正发生并确认的发展才会加入。")],
"ar":[("🧩 ما هو MUBA؟","لأقصر تعريف افتح الهوية. لمعرفة البداية افتح النشأة، وللقصة الزمنية الكاملة استخدم وضع القصة."),("📖 أريد القصة كاملة","وضع القصة يعرض الرحلة من ظهور الشخصية الأولى إلى بنية Assistant وGuardian وStudio الحالية."),("✨ ما المختلف؟","افتح الاختلاف لترى كيف تحولت الشخصية الأصلية والقصة غير المكتوبة مسبقاً إلى منظومة تعمل فعلاً لا مجرد شعار."),("👥 أريد المشاركة","افتح المجتمع لمعرفة ما يمكن للأعضاء فعله، ثم استخدم MUBA Studio و«أنشئ ← شارك» للإبداع العملي وأفكار جاهزة للمشاركة."),("🔎 أريد معلومات رسمية/آمنة","استخدم MUBA Daily للمناطق الرسمية والتغييرات الحديثة، واستخدم فحص الأمان للتحقق من رابط MUBA أو عنوان يشبه العقد."),("🧭 أريد معرفة المستقبل","افتح المستقبل لترى كيف تدعم الطبقات المستقرة الحالية النمو القادم. لا تضاف إلا التطورات التي تحدث فعلاً ويتم تأكيدها.")],
"hi":[("🧩 MUBA क्या है?","सबसे short answer के लिए Identity खोलें। शुरुआत के लिए Origin और पूरी chronological journey के लिए Story Mode इस्तेमाल करें।"),("📖 पूरी story चाहिए","Story Mode first character appearance से आज के Assistant, Guardian और Studio structure तक journey दिखाता है।"),("✨ Difference क्या है?","Difference खोलें और देखें कि original-character, non-prewritten approach सिर्फ slogan न रहकर working ecosystem कैसे बनी।"),("👥 Participate करना है","Community में देखें members क्या कर सकते हैं; फिर practical creation और share-ready ideas के लिए MUBA Studio और CREATE → SHARE इस्तेमाल करें।"),("🔎 Official/safe information चाहिए","Official areas और recent project changes के लिए MUBA Daily इस्तेमाल करें। MUBA link या contract-like address verify करने के लिए Security Check खोलें।"),("🧭 आगे क्या?","Future खोलें और देखें कि आज की stable layers future growth को कैसे support करती हैं। केवल confirmed developments ही add होते हैं।")]
}

SHARE_LABELS={
"en":{"menu":" CREATE → SHARE","tweets":"✍️ Share-ready posts","back":"⬅️ Back"},
"tr":{"menu":" ÜRET → PAYLAŞ","tweets":"✍️ Paylaşmaya hazır TWT'ler","back":"⬅️ Geri"},
"zh":{"menu":" 创作 → 分享","tweets":"✍️ 可直接分享的帖子","back":"⬅️ 返回"},
"ar":{"menu":" أنشئ → شارك","tweets":"✍️ منشورات جاهزة للمشاركة","back":"⬅️ رجوع"},
"hi":{"menu":" CREATE → SHARE","tweets":"✍️ Share-ready posts","back":"⬅️ वापस"}
}

SHARE_TWEETS={
"en":[
"We Live Here Now. \nNo borrowed mascot. No borrowed story. Just MUBA becoming more MUBA every day.\n$MUBA #MUBA",
"The story was never waiting in a document.\nIt showed up in the timeline, the memes and the people who kept building around MUBA. \n$MUBA #MUBA",
"MUBA did not need a bigger legend.\nIt needed a character people remembered — and a community that kept showing up. \n$MUBA #MUBA",
"Learn it. Meme it. Remix the moment.\nKeep the face MUBA, keep the energy yours. \n$MUBA #MUBA"],
"tr":[
"Artık burada yaşıyoruz. \nÖdünç maskot yok. Ödünç hikâye yok. MUBA her gün biraz daha MUBA oluyor.\n$MUBA #MUBA",
"Hikâye bir dosyanın içinde bizi beklemiyordu.\nTimeline'da, memelerde ve MUBA'nın etrafında üretmeye devam eden insanlarda oluştu. \n$MUBA #MUBA",
"MUBA'nın daha büyük bir efsaneye ihtiyacı yoktu.\nHatırlanan bir karaktere ve gelmeye devam eden bir topluluğa ihtiyacı vardı. \n$MUBA #MUBA",
"Öğren. Meme yap. Anı kendi dilinle yeniden kur.\nYüz MUBA kalsın, enerji senin olsun. \n$MUBA #MUBA"],
"zh":[
"We Live Here Now. \n没有借来的吉祥物，没有借来的故事。MUBA 每天都更像 MUBA。\n$MUBA #MUBA",
"故事从来不是在某份文件里等着我们。\n它出现在时间线、meme 和那些持续围绕 MUBA 创作的人中。\n$MUBA #MUBA",
"MUBA 不需要更大的传奇。\n它需要一个让人记住的角色，以及不断回来的社区。\n$MUBA #MUBA",
"了解它。做成 meme。重新创造这一刻。\n让角色保持 MUBA，让表达属于你。\n$MUBA #MUBA"],
"ar":[
"We Live Here Now. \nلا تميمة مستعارة. لا قصة مستعارة. فقط MUBA يصبح أكثر MUBA كل يوم.\n$MUBA #MUBA",
"لم تكن القصة تنتظرنا داخل ملف.\nظهرت في الـ timeline والميمات والناس الذين استمروا في البناء حول MUBA. \n$MUBA #MUBA",
"لم يحتج MUBA إلى أسطورة أكبر.\nاحتاج إلى شخصية يتذكرها الناس ومجتمع يستمر في الحضور. \n$MUBA #MUBA",
"تعلّمه. حوّله إلى meme. أعد صنع اللحظة بطريقتك.\nليظل الوجه MUBA ولتكن الطاقة طاقتك. \n$MUBA #MUBA"],
"hi":[
"We Live Here Now. \nNo borrowed mascot. No borrowed story. हर दिन MUBA थोड़ा और MUBA बनता है।\n$MUBA #MUBA",
"Story किसी file में हमारा इंतजार नहीं कर रही थी।\nवह timeline, memes और MUBA के around लगातार create करने वाले लोगों में बनी। \n$MUBA #MUBA",
"MUBA को बड़ी legend की जरूरत नहीं थी।\nउसे याद रहने वाला character और वापस आती community चाहिए थी। \n$MUBA #MUBA",
"सीखो। Meme बनाओ। Moment को अपने तरीके से remix करो।\nFace MUBA रहे, energy तुम्हारी हो। \n$MUBA #MUBA"]
}
