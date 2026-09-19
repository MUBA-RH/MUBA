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
"en":["MUBA did not begin with a complicated roadmap. First there was a character, appearing naturally inside meme-world chaos.","People saw MUBA, shared the character and started creating around it. A community formed without a prewritten legend.","That community gave the character a living culture: participation, creativity, humor and consistency became more important than grand promises.","The idea stayed simple: “I'm MUBA.” The story is not treated as finished; it develops through what the community actually does.","Today MUBA has a public home, a private Assistant and a Guardian for the main group. The next chapter remains open: We Live Here Now. 🪶"],
"tr":["MUBA karmaşık bir roadmap ile başlamadı. Önce meme dünyasının doğal kaosu içinde ortaya çıkan bir karakter vardı.","İnsanlar MUBA'yı gördü, paylaştı ve karakter etrafında içerik üretmeye başladı. Önceden yazılmış bir efsane olmadan topluluk oluştu.","Bu topluluk karaktere yaşayan bir kültür kazandırdı: katılım, yaratıcılık, mizah ve istikrar büyük vaatlerden daha önemli hale geldi.","Fikir sade kaldı: “Ben MUBA.” Hikâye bitmiş kabul edilmiyor; topluluğun gerçekten yaptıklarıyla gelişiyor.","Bugün MUBA'nın herkese açık bir evi, özel Assistant'ı ve ana grup için Guardian'ı var. Sonraki bölüm hâlâ açık: We Live Here Now. 🪶"],
"zh":["MUBA 并不是从复杂路线图开始的。最初只是一个自然出现在 meme 世界混沌中的角色。","人们看见 MUBA、分享它并围绕角色开始创作。没有预写传奇，社区逐渐形成。","社区让角色拥有了活的文化：参与、创造力、幽默和持续建设比宏大承诺更重要。","核心一直很简单：“I'm MUBA.” 故事没有被视为完成，而是随着社区真实的行动继续发展。","今天 MUBA 有公开主页、私聊 Assistant，以及保护主群的 Guardian。下一章仍然开放：We Live Here Now. 🪶"],
"ar":["لم يبدأ MUBA بخارطة طريق معقدة. في البداية كانت هناك شخصية ظهرت طبيعياً وسط فوضى عالم الميم.","رأى الناس MUBA وشاركوه وبدأوا بصنع محتوى حوله. تشكّل المجتمع دون أسطورة مكتوبة مسبقاً.","منح المجتمع الشخصية ثقافة حية؛ أصبحت المشاركة والإبداع والفكاهة والاستمرارية أهم من الوعود الكبيرة.","بقيت الفكرة بسيطة: “I'm MUBA.” القصة ليست منتهية؛ بل تتطور بما يفعله المجتمع فعلاً.","اليوم لدى MUBA بيت عام وAssistant خاص وGuardian للمجموعة الرئيسية. الفصل التالي ما زال مفتوحاً: We Live Here Now. 🪶"],
"hi":["MUBA किसी जटिल roadmap से शुरू नहीं हुआ। पहले meme-world की प्राकृतिक chaos में उभरा एक character था।","लोगों ने MUBA को देखा, share किया और उसके आसपास content बनाना शुरू किया। बिना prewritten legend के community बनी।","Community ने character को living culture दिया: participation, creativity, humor और consistency बड़े promises से ज्यादा महत्वपूर्ण बने।","Idea simple रहा: “I'm MUBA.” Story को finished नहीं माना जाता; community जो वास्तव में करती है उससे यह आगे बढ़ती है।","आज MUBA का public home, private Assistant और main group के लिए Guardian है। अगला chapter खुला है: We Live Here Now. 🪶"],
}

LAB={
"en":{"meme":"Meme idea: MUBA walks into meme-world chaos, looks around and simply says: “We live here now.” Keep the character recognizable and let the situation carry the joke.","tweet":"Tweet seed: No grand legend was waiting for MUBA. The character arrived first. The community gave it a place to live. 🪶","visual":"Visual idea: 16:9. MUBA at the edge of a huge neon meme city, black MUBA cap and $MUBA hoodie, looking toward the next district. Minimal text: WE LIVE HERE NOW."},
"tr":{"meme":"Meme fikri: MUBA meme dünyasının kaosuna girer, etrafına bakar ve sadece “We live here now.” der. Karakter tanınır kalsın; mizahı sahne taşısın.","tweet":"Tweet tohumu: MUBA'yı bekleyen büyük bir efsane yoktu. Önce karakter geldi. Ona yaşayacağı yeri topluluk verdi. 🪶","visual":"Görsel fikri: 16:9. Siyah MUBA şapkası ve $MUBA hoodie'siyle dev neon meme şehrinin kenarında duran MUBA, sonraki bölgeye bakıyor. Minimum yazı: WE LIVE HERE NOW."},
"zh":{"meme":"Meme 点子：MUBA 走进混乱的 meme 世界，看了一圈，只说：“We live here now.” 保持角色辨识度，让场景本身制造幽默。","tweet":"Tweet 灵感：没有宏大传奇在等待 MUBA。角色先出现，社区给了它一个可以生活的地方。🪶","visual":"视觉点子：16:9。MUBA 戴黑色 MUBA 帽、穿 $MUBA hoodie，站在巨大霓虹 meme 城市边缘，看向下一个街区。最少文字：WE LIVE HERE NOW."},
"ar":{"meme":"فكرة ميم: يدخل MUBA إلى فوضى عالم الميم، ينظر حوله ويقول فقط: “We live here now.” حافظ على شكل الشخصية واجعل الموقف يحمل النكتة.","tweet":"بذرة تغريدة: لم تكن هناك أسطورة ضخمة تنتظر MUBA. جاءت الشخصية أولاً، ثم منحها المجتمع مكاناً تعيش فيه. 🪶","visual":"فكرة بصرية: 16:9. MUBA بقبعته السوداء وhoodie $MUBA على حافة مدينة ميم نيون ضخمة وينظر إلى الحي التالي. نص قليل: WE LIVE HERE NOW."},
"hi":{"meme":"Meme idea: MUBA meme-world chaos में आता है, चारों ओर देखता है और बस कहता है: “We live here now.” Character recognizable रहे और joke scene से आए।","tweet":"Tweet seed: MUBA के लिए कोई grand legend इंतजार नहीं कर रही थी। Character पहले आया। Community ने उसे रहने की जगह दी। 🪶","visual":"Visual idea: 16:9. Black MUBA cap और $MUBA hoodie में MUBA एक विशाल neon meme city के किनारे खड़ा अगले district की ओर देख रहा है। Minimal text: WE LIVE HERE NOW."},
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
