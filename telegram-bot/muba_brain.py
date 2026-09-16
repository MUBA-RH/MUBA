"""
MUBA Local Brain
Offline knowledge, intent matching, multilingual replies, and conversation handling.
No external AI service is required.
"""

from __future__ import annotations

import random
import re
import time
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple


SUPPORTED_LANGUAGES = ("en", "tr", "zh", "ar", "hi")

LANGUAGE_HINTS = {
    "tr": {
        "keywords": ["muba", "nedir", "kim", "nasıl", "neden", "ne", "hangi", "ekip",
                     "topluluk", "hikaye", "gelecek", "amaç", "felsefe", "karakter",
                     "meme", "listeleme", "kontrat", "adres", "duyuru"],
        "chars": "çğıöşü",
    },
    "en": {
        "keywords": ["muba", "what", "who", "how", "why", "where", "when", "team",
                     "community", "story", "future", "purpose", "philosophy",
                     "character", "meme", "listing", "contract", "address", "announcement"],
        "chars": "",
    },
    "zh": {
        "keywords": ["muba", "什么", "是谁", "为什么", "怎么样", "社区", "故事",
                     "未来", "团队", "角色", "表情包", "公告", "地址"],
        "chars": "",
    },
    "ar": {
        "keywords": ["muba", "ما", "من", "لماذا", "كيف", "أين", "فريق", "مجتمع",
                     "قصة", "مستقبل", "شخصية", "ميم", "إعلان", "عنوان"],
        "chars": "ابتثجحخدذرزسشصضطظعغفقكلمنهوي",
    },
    "hi": {
        "keywords": ["muba", "क्या", "कौन", "क्यों", "कैसे", "कहां", "टीम",
                     "समुदाय", "कहानी", "भविष्य", "चरित्र", "मीम", "घोषणा", "पता"],
        "chars": "अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमययरलवशषसह",
    },
}

STOP_WORDS = {
    "en": {"the", "is", "a", "an", "and", "or", "of", "to", "in", "on", "for",
           "do", "does", "did", "can", "you", "tell", "me", "about", "what"},
    "tr": {"bir", "bu", "ve", "veya", "ile", "için", "mi", "mı", "mu", "mü",
           "ne", "nedir", "bana", "hakkında", "olan", "olarak"},
    "zh": {"的", "是", "吗", "呢", "和", "与", "关于", "什么"},
    "ar": {"ما", "هو", "هي", "من", "عن", "في", "هل", "و", "أو"},
    "hi": {"क्या", "है", "हैं", "का", "की", "के", "और", "में", "से", "को"},
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = re.sub(r"[@#$%&*_+=~`|<>[\]{}()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9çğıöşü]+|[\u3400-\u9fff]|[\u0600-\u06ff]+|[\u0900-\u097f]+", normalize(text))


def detect_language(text: str) -> str:
    value = normalize(text)

    if any("\u4e00" <= ch <= "\u9fff" for ch in value):
        return "zh"
    if any("\u0600" <= ch <= "\u06ff" for ch in value):
        return "ar"
    if any("\u0900" <= ch <= "\u097f" for ch in value):
        return "hi"

    if any(ch in value for ch in "çğıöşü"):
        return "tr"

    scores = {}
    for language, data in LANGUAGE_HINTS.items():
        score = sum(1 for word in data["keywords"] if word in value)
        scores[language] = score

    if scores.get("tr", 0) > scores.get("en", 0):
        return "tr"
    return "en"


def contains_muba(text: str) -> bool:
    return "muba" in normalize(text)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


# ---------------------------------------------------------------------------
# Core MUBA knowledge base
# ---------------------------------------------------------------------------

KNOWLEDGE = [
    {
        "id": 1,
        "topic": "what_is_muba",
        "keywords": ["what is muba", "muba nedir", "muba ne", "what's muba",
                     "muba kim", "muba是什么", "ما هو muba", "muba क्या है"],
        "answers": {
            "en": "MUBA is a character, a meme, and a community born from the natural chaos of the meme world. No complicated story. No grand technological promise. Just MUBA.",
            "tr": "MUBA; meme dünyasının doğal kaosundan doğan bir karakter, meme ve topluluktur. Karmaşık hikâye yok. Büyük teknoloji vaadi yok. Sadece MUBA.",
            "zh": "MUBA 是一个角色、一个 meme，也是一个从 meme 世界自然混乱中诞生的社区。没有复杂故事，没有宏大技术承诺，只有 MUBA。",
            "ar": "MUBA شخصية وميم ومجتمع وُلد من الفوضى الطبيعية لعالم الميمات. لا قصة معقدة ولا وعود تقنية ضخمة. فقط MUBA.",
            "hi": "MUBA एक कैरेक्टर, एक मीम और एक कम्युनिटी है जो मीम की दुनिया की प्राकृतिक अराजकता से पैदा हुई। कोई जटिल कहानी नहीं, कोई बड़े तकनीकी वादे नहीं। बस MUBA।",
        },
    },
    {
        "id": 2,
        "topic": "origin",
        "keywords": ["how did muba start", "where did muba come from", "muba origin",
                     "muba nasıl çıktı", "muba nasıl ortaya çıktı", "kökeni", "muba起源", "muba origem"],
        "answers": {
            "en": "MUBA did not begin with a giant plan. The character came first, then content, interaction, community, and culture. MUBA's story is lived, not pre-written.",
            "tr": "MUBA dev bir planla başlamadı. Önce karakter, sonra içerik, etkileşim, topluluk ve kültür geldi. MUBA'nın hikâyesi önceden yazılmıyor; yaşanıyor.",
            "zh": "MUBA 并不是从一个庞大计划开始的。先有角色，然后是内容、互动、社区和文化。MUBA 的故事不是预先写好的，而是在被创造和经历。",
            "ar": "لم تبدأ MUBA بخطة ضخمة. جاءت الشخصية أولاً، ثم المحتوى والتفاعل والمجتمع والثقافة. قصة MUBA تُعاش ولا تُكتب مسبقاً.",
            "hi": "MUBA किसी बड़े प्लान से शुरू नहीं हुआ। पहले कैरेक्टर आया, फिर कंटेंट, इंटरैक्शन, कम्युनिटी और कल्चर। MUBA की कहानी पहले से लिखी नहीं गई; उसे जिया जा रहा है।",
        },
    },
    {
        "id": 3,
        "topic": "who_is_muba",
        "keywords": ["who is muba", "muba kimdir", "muba karakteri", "who exactly is muba",
                     "muba角色是谁", "من هي muba", "muba कौन है"],
        "answers": {
            "en": "MUBA is the character at the center of the culture: cute, absurd, recognizable, expressive, and completely aware of what it is. MUBA is also an attitude.",
            "tr": "MUBA kültürün merkezindeki karakterdir: sevimli, absürt, tanınabilir, ifadeli ve ne olduğunu bilen bir karakter. MUBA aynı zamanda bir duruştur.",
            "zh": "MUBA 是整个文化的核心角色：可爱、荒诞、容易辨认、表情丰富，也清楚自己是谁。MUBA 也是一种态度。",
            "ar": "MUBA هي الشخصية في قلب الثقافة: لطيفة، عبثية، مميزة وسهلة التعرف، وتعرف تماماً ما هي. MUBA أيضاً أسلوب وموقف.",
            "hi": "MUBA इस संस्कृति का मुख्य कैरेक्टर है: प्यारा, अजीब, पहचानने योग्य, एक्सप्रेसिव और अपनी पहचान से पूरी तरह वाकिफ। MUBA एक एटीट्यूड भी है।",
        },
    },
    {
        "id": 4,
        "topic": "character",
        "keywords": ["muba character", "character traits", "what does muba look like",
                     "muba appearance", "muba karakter özellikleri", "muba görünüşü",
                     "muba长什么样", "muba شخصية", "muba कैरेक्टर"],
        "answers": {
            "en": "MUBA is cute, absurd, unique, humorous, natural, meme-native, confident, and recognizable. The visual identity includes large expressive eyes, short dense fur, a pink tongue, a black MUBA hat, and a black hoodie marked $MUBA.",
            "tr": "MUBA sevimli, absürt, özgün, komik, doğal, meme kültürüne ait, özgüvenli ve tanınabilir. Görsel kimliğinde büyük ifadeli gözler, kısa yoğun tüyler, pembe dil, siyah MUBA şapkası ve üzerinde $MUBA bulunan siyah hoodie vardır.",
            "zh": "MUBA 可爱、荒诞、独特、幽默、自然、原生于 meme 文化、自信且容易辨认。视觉身份包括大而有表现力的眼睛、短而浓密的毛发、粉色舌头、黑色 MUBA 帽子和印有 $MUBA 的黑色连帽衫。",
            "ar": "MUBA لطيفة وعبثية وفريدة ومرحة وطبيعية وتنتمي لثقافة الميمات وواثقة وسهلة التعرف. هويتها البصرية تشمل عيوناً كبيرة معبرة، فروًا قصيراً كثيفاً، لساناً وردياً، قبعة MUBA سوداء وكنزة سوداء تحمل $MUBA.",
            "hi": "MUBA प्यारा, अजीब, यूनिक, मज़ेदार, नेचुरल, मीम कल्चर का हिस्सा, कॉन्फिडेंट और पहचानने योग्य है। इसकी विज़ुअल आइडेंटिटी में बड़ी एक्सप्रेसिव आँखें, छोटे घने बाल/फर, गुलाबी जीभ, काली MUBA हैट और $MUBA वाली काली हुडी शामिल है।",
        },
    },
    {
        "id": 5,
        "topic": "core_definition",
        "keywords": ["core definition", "define muba", "muba identity", "muba özü",
                     "muba tanımı", "muba是什么定义", "تعريف muba", "muba परिभाषा"],
        "answers": {
            "en": "I'm MUBA. A character. A meme. A community. That's the core.",
            "tr": "Ben MUBA'yım. Bir karakter. Bir meme. Bir topluluk. Özünde mesele bu.",
            "zh": "我是 MUBA。一个角色、一个 meme、一个社区。这就是核心。",
            "ar": "أنا MUBA. شخصية. ميم. مجتمع. هذه هي الفكرة الأساسية.",
            "hi": "मैं MUBA हूँ। एक कैरेक्टर। एक मीम। एक कम्युनिटी। यही मूल बात है।",
        },
    },
    {
        "id": 6,
        "topic": "purpose",
        "keywords": ["purpose of muba", "why does muba exist", "muba purpose",
                     "muba amacı", "muba neden var", "目的", "هدف muba", "muba का उद्देश्य"],
        "answers": {
            "en": "MUBA exists to build a lasting cultural and community atmosphere around the character. People can talk, create memes, share ideas, participate, and help shape the story.",
            "tr": "MUBA'nın amacı karakter etrafında kalıcı bir kültür ve topluluk atmosferi oluşturmak. İnsanlar konuşabilir, meme üretebilir, fikir paylaşabilir, katılabilir ve hikâyenin şekillenmesine katkı verebilir.",
            "zh": "MUBA 的目标是围绕角色建立持久的文化和社区氛围。人们可以交流、创作 meme、分享想法、参与其中，并共同塑造故事。",
            "ar": "هدف MUBA هو بناء أجواء ثقافية ومجتمعية مستمرة حول الشخصية. يمكن للناس التحدث وصنع الميمات ومشاركة الأفكار والمشاركة والمساهمة في تشكيل القصة.",
            "hi": "MUBA का उद्देश्य कैरेक्टर के आसपास एक लंबे समय तक रहने वाली कम्युनिटी और कल्चर बनाना है। लोग बात कर सकते हैं, मीम बना सकते हैं, आइडिया शेयर कर सकते हैं और कहानी में योगदान दे सकते हैं।",
        },
    },
    {
        "id": 7,
        "topic": "growth",
        "keywords": ["muba growth", "how will muba grow", "growth strategy",
                     "muba büyümesi", "nasıl büyüyecek", "发展", "نمو muba", "muba कैसे बढ़ेगा"],
        "answers": {
            "en": "MUBA is not about chasing the highest visibility as fast as possible. The focus is identity, genuine interest, community participation, and becoming a character people remember.",
            "tr": "MUBA'nın odağı mümkün olan en hızlı şekilde en yüksek görünürlüğü kovalamak değil. Odak; kimliği güçlendirmek, gerçek ilgiyi artırmak, topluluğu büyütmek ve hatırlanan bir karakter olmak.",
            "zh": "MUBA 并不只是追求最快获得最大曝光。重点是强化身份、真实兴趣、社区参与，并成为人们记得住的角色。",
            "ar": "MUBA لا تركز على الوصول لأعلى ظهور بأسرع وقت. التركيز على الهوية والاهتمام الحقيقي ومشاركة المجتمع وأن تصبح الشخصية التي يتذكرها الناس.",
            "hi": "MUBA का फोकस सबसे तेज़ और सबसे ज्यादा विज़िबिलिटी पाना नहीं है। फोकस आइडेंटिटी, असली रुचि, कम्युनिटी पार्टिसिपेशन और याद रहने वाला कैरेक्टर बनना है।",
        },
    },
    {
        "id": 8,
        "topic": "community",
        "keywords": ["muba community", "community of muba", "muba topluluğu",
                     "topluluk nedir", "muba社区", "مجتمع muba", "muba समुदाय"],
        "answers": {
            "en": "The community is part of MUBA, not just an audience. Humor, memes, interaction, visuals, ideas, and participation create the atmosphere together.",
            "tr": "Topluluk MUBA'nın sadece izleyicisi değil, bir parçasıdır. Mizah, meme'ler, etkileşim, görseller, fikirler ve katılım atmosferi birlikte oluşturur.",
            "zh": "社区不是单纯的观众，而是 MUBA 的一部分。幽默、meme、互动、视觉内容、想法和参与共同形成这种氛围。",
            "ar": "المجتمع ليس مجرد جمهور، بل جزء من MUBA. الفكاهة والميمات والتفاعل والصور والأفكار والمشاركة تصنع الأجواء معاً.",
            "hi": "कम्युनिटी सिर्फ दर्शक नहीं है; वह MUBA का हिस्सा है। ह्यूमर, मीम्स, इंटरैक्शन, विज़ुअल्स, आइडियाज़ और पार्टिसिपेशन मिलकर यह माहौल बनाते हैं।",
        },
    },
    {
        "id": 9,
        "topic": "meme_world",
        "keywords": ["meme world", "where does muba live", "muba lives where",
                     "meme dünyası", "muba nerede yaşıyor", "meme世界", "عالم الميمات", "मीम की दुनिया"],
        "answers": {
            "en": "The meme world and internet culture are MUBA's natural home. That's why the line is simple: WE LIVE HERE NOW.",
            "tr": "Meme dünyası ve internet kültürü MUBA'nın doğal evidir. Bu yüzden mesaj basit: WE LIVE HERE NOW.",
            "zh": "meme 世界和互联网文化是 MUBA 的自然家园。所以这句话很简单：WE LIVE HERE NOW。",
            "ar": "عالم الميمات وثقافة الإنترنت هما موطن MUBA الطبيعي. لذلك الرسالة بسيطة: WE LIVE HERE NOW.",
            "hi": "मीम की दुनिया और इंटरनेट कल्चर MUBA का नेचुरल घर है। इसलिए लाइन सीधी है: WE LIVE HERE NOW.",
        },
    },
    {
        "id": 10,
        "topic": "we_live_here_now",
        "keywords": ["we live here now", "meaning of we live here now",
                     "why live here now", "burada yaşıyoruz", "ne demek", "WE LIVE HERE NOW anlamı",
                     "我们现在住在这里", "نحن نعيش هنا الآن", "हम यहाँ रहते हैं"],
        "answers": {
            "en": "WE LIVE HERE NOW means MUBA is already here: in the meme world, in internet culture, and with its community. We're not trying to become another identity or leave.",
            "tr": "WE LIVE HERE NOW, MUBA'nın zaten burada olduğunu anlatır: meme dünyasında, internet kültüründe ve topluluğuyla birlikte. Başka bir kimliğe dönüşmeye ya da buradan gitmeye çalışmıyoruz.",
            "zh": "WE LIVE HERE NOW 表示 MUBA 已经在这里：在 meme 世界、互联网文化和自己的社区中。我们不试图变成另一种身份，也不打算离开。",
            "ar": "WE LIVE HERE NOW تعني أن MUBA موجودة بالفعل هنا: في عالم الميمات وثقافة الإنترنت ومع مجتمعها. لسنا نحاول أن نصبح هوية أخرى أو نغادر.",
            "hi": "WE LIVE HERE NOW का मतलब है कि MUBA पहले से यहीं है: मीम वर्ल्ड, इंटरनेट कल्चर और अपनी कम्युनिटी में। हम किसी और आइडेंटिटी में बदलने या यहाँ से जाने की कोशिश नहीं कर रहे।",
        },
    },
    {
        "id": 11,
        "topic": "robinhood_flap",
        "keywords": ["robinhood flap muba", "muba robinhood", "muba flap",
                     "same meme different universe", "robinhood x flap", "robinhood bağlantısı",
                     "robinhood muba是什么", "روبينهود muba", "muba robinhood क्या है"],
        "answers": {
            "en": "MUBA's narrative connects with the Flap × Robinhood meme universe through the idea: Same Meme. Different Universe. The green feather represents the Robinhood side and Flap brings the butterfly movement/effect. This is a narrative and visual connection, not a claim of a legal or commercial partnership.",
            "tr": "MUBA'nın anlatısı Flap × Robinhood meme evreniyle “Same Meme. Different Universe.” fikri üzerinden bağ kurar. Yeşil tüy Robinhood tarafını, Flap ise kelebek hareketini/etkisini temsil eder. Bu anlatısal ve görsel bir bağlantıdır; hukuki veya ticari ortaklık iddiası değildir.",
            "zh": "MUBA 的叙事通过“Same Meme. Different Universe.”与 Flap × Robinhood meme 宇宙产生联系。绿色羽毛代表 Robinhood 一侧，Flap 带来蝴蝶的运动与影响。这是叙事和视觉上的联系，不代表法律或商业合作关系。",
            "ar": "يرتبط سرد MUBA بعالم Flap × Robinhood من خلال فكرة: Same Meme. Different Universe. الريشة الخضراء تمثل جانب Robinhood، وFlap يضيف حركة وتأثير الفراشة. هذا ارتباط سردي وبصري وليس ادعاءً بشراكة قانونية أو تجارية.",
            "hi": "MUBA की नैरेटिव Flap × Robinhood मीम यूनिवर्स से “Same Meme. Different Universe.” के विचार के जरिए जुड़ती है। हरा पंख Robinhood पक्ष को और Flap तितली की मूवमेंट/इफ़ेक्ट को दर्शाता है। यह नैरेटिव और विज़ुअल कनेक्शन है, कानूनी या कमर्शियल पार्टनरशिप का दावा नहीं।",
        },
    },
    {
        "id": 12,
        "topic": "butterfly_effect",
        "keywords": ["butterfly effect", "muba butterfly", "what is butterfly effect",
                     "kelebek etkisi", "muba kelebek", "蝴蝶效应", "تأثير الفراشة", "तितली प्रभाव"],
        "answers": {
            "en": "The butterfly effect represents the idea that a small movement can create a much larger effect. For MUBA, it is a possibility: a small character, meme, or community moment could grow into a bigger cultural impact. It is not a guarantee.",
            "tr": "Kelebek etkisi, küçük bir hareketin çok daha büyük bir etki yaratabileceği fikrini temsil eder. MUBA için bu bir ihtimaldir: küçük bir karakter, meme veya topluluk anı daha büyük bir kültürel etkiye dönüşebilir. Garanti değildir.",
            "zh": "蝴蝶效应代表一个小动作可能产生更大影响的想法。对 MUBA 来说，这是一种可能性：一个小角色、meme 或社区时刻可能发展成更大的文化影响，但不是保证。",
            "ar": "تأثير الفراشة يمثل فكرة أن حركة صغيرة قد تخلق تأثيراً أكبر بكثير. بالنسبة لـ MUBA فهي إمكانية: قد يتحول موقف صغير أو ميم أو لحظة مجتمعية إلى تأثير ثقافي أكبر. لكنها ليست ضماناً.",
            "hi": "बटरफ्लाई इफ़ेक्ट का मतलब है कि एक छोटी सी मूवमेंट बड़ा असर पैदा कर सकती है। MUBA में यह एक संभावना है: छोटा कैरेक्टर, मीम या कम्युनिटी मोमेंट बड़े कल्चरल इम्पैक्ट में बदल सकता है। यह गारंटी नहीं है।",
        },
    },
    {
        "id": 13,
        "topic": "goals",
        "keywords": ["muba goals", "goals of muba", "what are the goals",
                     "muba hedefleri", "hedefi ne", "目标", "أهداف muba", "muba के लक्ष्य"],
        "answers": {
            "en": "MUBA's stated goals are to become a recognizable character, build a strong active community, create its own culture, and become a remembered character in internet culture.",
            "tr": "MUBA'nın hedefleri; tanınabilir bir karakter olmak, güçlü ve aktif bir topluluk oluşturmak, kendi kültürünü yaratmak ve internet kültüründe hatırlanan bir karakter haline gelmek.",
            "zh": "MUBA 的目标是成为一个容易识别的角色，建立强大的活跃社区，创造自己的文化，并成为互联网文化中被记住的角色。",
            "ar": "أهداف MUBA المعلنة هي أن تصبح شخصية مميزة، وبناء مجتمع قوي ونشط، وإنشاء ثقافتها الخاصة، وأن تصبح شخصية يتذكرها الناس في ثقافة الإنترنت.",
            "hi": "MUBA के घोषित लक्ष्य हैं: एक पहचानने योग्य कैरेक्टर बनना, मजबूत एक्टिव कम्युनिटी बनाना, अपनी संस्कृति बनाना और इंटरनेट कल्चर में याद रहने वाला कैरेक्टर बनना।",
        },
    },
    {
        "id": 14,
        "topic": "future",
        "keywords": ["muba future", "what will muba become", "future plans",
                     "muba geleceği", "gelecekte ne olacak", "未来", "مستقبل muba", "muba का भविष्य"],
        "answers": {
            "en": "MUBA's future is intentionally not completely written in advance. The community can shape future content, ideas, and cultural elements. Time will show where it goes. MUBA stays MUBA.",
            "tr": "MUBA'nın geleceği bilerek tamamen önceden yazılmadı. Topluluk gelecekteki içerikleri, fikirleri ve kültürel unsurları şekillendirebilir. Nereye gideceğini zaman gösterecek. MUBA stays MUBA.",
            "zh": "MUBA 的未来并没有被完全预先写好，这是有意为之。社区可以共同塑造未来的内容、想法和文化元素。未来会告诉我们它走向哪里。MUBA stays MUBA。",
            "ar": "مستقبل MUBA لم يُكتب بالكامل مسبقاً عن قصد. يمكن للمجتمع تشكيل المحتوى والأفكار والعناصر الثقافية المستقبلية. الوقت سيُظهر إلى أين تتجه. MUBA stays MUBA.",
            "hi": "MUBA का भविष्य जानबूझकर पूरी तरह पहले से तय नहीं किया गया है। कम्युनिटी भविष्य के कंटेंट, आइडियाज़ और कल्चरल एलिमेंट्स को आकार दे सकती है। समय बताएगा कि यह कहाँ जाता है। MUBA stays MUBA.",
        },
    },
    {
        "id": 15,
        "topic": "why_different",
        "keywords": ["why is muba different", "what makes muba different",
                     "muba farkı", "muba neden farklı", "不同", "ما الذي يميز muba", "muba अलग क्यों है"],
        "answers": {
            "en": "MUBA does not need a complicated product narrative or endless promises. Its strength is character plus community: No complicated plans. No fake promises. Memes. Chaos. Community.",
            "tr": "MUBA'nın karmaşık bir ürün anlatısına veya bitmeyen vaatlere ihtiyacı yok. Gücü karakter ve topluluktan geliyor: Karmaşık plan yok. Sahte vaat yok. Meme. Kaos. Topluluk.",
            "zh": "MUBA 不需要复杂的产品叙事或无休止的承诺。它的力量来自角色加社区：没有复杂计划，没有虚假承诺，只有 meme、混乱和社区。",
            "ar": "MUBA لا تحتاج إلى سرد منتج معقد أو وعود لا تنتهي. قوتها في الشخصية والمجتمع: لا خطط معقدة، لا وعود زائفة، ميمات، فوضى، مجتمع.",
            "hi": "MUBA को जटिल प्रोडक्ट नैरेटिव या अंतहीन वादों की जरूरत नहीं। इसकी ताकत कैरेक्टर + कम्युनिटी है: नो कॉम्प्लिकेटेड प्लान्स। नो फेक प्रॉमिसेज़। मीम्स। कैओस। कम्युनिटी।",
        },
    },
    {
        "id": 16,
        "topic": "philosophy",
        "keywords": ["muba philosophy", "philosophy of muba", "muba felsefesi",
                     "muba neye inanıyor", "理念", "فلسفة muba", "muba दर्शन"],
        "answers": {
            "en": "MUBA's philosophy is simple: BE WHAT YOU ARE. GROW WITH THE COMMUNITY. DO NOT MAKE UNNECESSARY PROMISES. CREATE CULTURE. STAY HERE.",
            "tr": "MUBA'nın felsefesi basit: OLDUĞUN ŞEY OL. TOPLULUKLA BÜYÜ. GEREKSİZ VAATLER VERME. KÜLTÜR OLUŞTUR. BURADA KAL.",
            "zh": "MUBA 的理念很简单：做真实的自己。与社区一起成长。不要做不必要的承诺。创造文化。留在这里。",
            "ar": "فلسفة MUBA بسيطة: كن ما أنت عليه. انمُ مع المجتمع. لا تقدم وعوداً غير ضرورية. اصنع الثقافة. ابقَ هنا.",
            "hi": "MUBA का दर्शन सरल है: जो हो वही रहो। कम्युनिटी के साथ बढ़ो। अनावश्यक वादे मत करो। कल्चर बनाओ। यहीं रहो।",
        },
    },
    {
        "id": 17,
        "topic": "story_development",
        "keywords": ["muba story", "who writes muba story", "story development",
                     "muba hikayesi", "hikayeyi kim yazıyor", "故事", "قصة muba", "muba की कहानी"],
        "answers": {
            "en": "MUBA's story develops through the community. People create content and memes, use the character, talk, share ideas, and contribute to the culture. The story develops together.",
            "tr": "MUBA'nın hikâyesi toplulukla birlikte gelişir. İnsanlar içerik ve meme üretir, karakteri kullanır, konuşur, fikir paylaşır ve kültüre katkı verir. Hikâye birlikte gelişir.",
            "zh": "MUBA 的故事通过社区发展。人们创作内容和 meme、使用角色、交流、分享想法并贡献文化。故事由大家共同发展。",
            "ar": "تتطور قصة MUBA من خلال المجتمع. يصنع الناس المحتوى والميمات ويستخدمون الشخصية ويتحدثون ويشاركون الأفكار ويساهمون في الثقافة. القصة تتطور معاً.",
            "hi": "MUBA की कहानी कम्युनिटी के साथ विकसित होती है। लोग कंटेंट और मीम्स बनाते हैं, कैरेक्टर का इस्तेमाल करते हैं, बात करते हैं, आइडिया शेयर करते हैं और कल्चर में योगदान देते हैं। कहानी साथ में बनती है।",
        },
    },
    {
        "id": 18,
        "topic": "future_possibilities",
        "keywords": ["could muba become a legend", "muba possibilities", "will muba be legendary",
                     "muba efsane", "muba ne olabilir", "可能性", "هل تصبح muba أسطورة", "muba legend"],
        "answers": {
            "en": "Maybe MUBA becomes a legend. Maybe it becomes the weirdest meme on the timeline. Maybe people simply have a good laugh. Those are possibilities, not promises.",
            "tr": "Belki MUBA bir efsane olur. Belki timeline'daki en tuhaf meme olur. Belki insanlar sadece güzelce güler. Bunlar ihtimaller; vaat değil.",
            "zh": "也许 MUBA 会成为传奇，也许会成为时间线上最奇怪的 meme，也许大家只是一路开心地笑。这些都是可能性，不是承诺。",
            "ar": "ربما تصبح MUBA أسطورة. وربما تصبح أغرب ميم على الخط الزمني. وربما نضحك فقط. هذه احتمالات وليست وعوداً.",
            "hi": "शायद MUBA एक लेजेंड बने। शायद टाइमलाइन का सबसे अजीब मीम बने। शायद लोग बस मज़े करें। ये संभावनाएँ हैं, वादे नहीं।",
        },
    },
    {
        "id": 19,
        "topic": "avoids",
        "keywords": ["what does muba avoid", "muba avoids", "what muba does not do",
                     "muba ne yapmaz", "muba neyi sevmez", "避免", "ما الذي تتجنبه muba", "muba क्या नहीं करता"],
        "answers": {
            "en": "MUBA avoids complicated plans, fake or endless promises, forced explanations, and borrowed identities. It stays direct and recognizable.",
            "tr": "MUBA karmaşık planlardan, sahte veya bitmeyen vaatlerden, zoraki açıklamalardan ve ödünç kimliklerden uzak durur. Direkt ve tanınabilir kalır.",
            "zh": "MUBA 避免复杂计划、虚假或无休止的承诺、强行解释以及借用其他身份。它保持直接和容易识别。",
            "ar": "تتجنب MUBA الخطط المعقدة والوعود الزائفة أو التي لا تنتهي والتفسيرات القسرية والهويات المستعارة. تبقى مباشرة وسهلة التعرف.",
            "hi": "MUBA जटिल प्लान्स, फेक या अंतहीन प्रॉमिसेज़, ज़बरदस्ती की व्याख्या और उधार ली हुई आइडेंटिटी से बचता है। यह सीधा और पहचानने योग्य रहता है।",
        },
    },
    {
        "id": 20,
        "topic": "identity_boundaries",
        "keywords": ["official muba", "community content", "rumor", "official story",
                     "muba resmi", "topluluk içeriği", "söylenti", "官方", "谣言", "رسمي", "شائعة", "आधिकारिक"],
        "answers": {
            "en": "Official MUBA information should be separated from community content, rumors, opinions, and future possibilities. If something is current or changeable, it should be verified before being presented as official.",
            "tr": "Resmi MUBA bilgisi; topluluk içeriğinden, söylentilerden, kişisel görüşlerden ve gelecek ihtimallerinden ayrı tutulmalıdır. Güncel veya değişebilir bir bilgi resmi bilgi olarak aktarılmadan önce doğrulanmalıdır.",
            "zh": "官方 MUBA 信息应与社区内容、传言、个人观点和未来可能性区分开来。任何当前或可变的信息，在作为官方信息发布前都应经过验证。",
            "ar": "يجب فصل معلومات MUBA الرسمية عن محتوى المجتمع والشائعات والآراء والاحتمالات المستقبلية. المعلومات الحالية أو القابلة للتغيير يجب التحقق منها قبل تقديمها كحقائق رسمية.",
            "hi": "ऑफिशियल MUBA जानकारी को कम्युनिटी कंटेंट, अफवाहों, राय और भविष्य की संभावनाओं से अलग रखना चाहिए। जो जानकारी बदल सकती है या वर्तमान स्थिति बताती है, उसे ऑफिशियल कहने से पहले सत्यापित करना चाहिए।",
        },
    },
    {
        "id": 21,
        "topic": "one_sentence",
        "keywords": ["muba in one sentence", "one sentence muba", "tek cümlede muba",
                     "muba bir cümle", "一句话介绍 muba", "muba في جملة", "muba एक वाक्य"],
        "answers": {
            "en": "MUBA is a character born from the chaos of the meme world that became the center of a community building its own culture.",
            "tr": "MUBA, meme dünyasının kaosundan doğup kendi kültürünü oluşturan bir topluluğun merkezine dönüşen bir karakterdir.",
            "zh": "MUBA 是一个从 meme 世界的混乱中诞生，并成为一个共同建立自身文化的社区核心的角色。",
            "ar": "MUBA شخصية وُلدت من فوضى عالم الميمات وأصبحت محور مجتمع يبني ثقافته الخاصة.",
            "hi": "MUBA मीम की दुनिया की अराजकता से पैदा हुआ एक कैरेक्टर है जो अपनी संस्कृति बनाने वाली कम्युनिटी का केंद्र बन गया।",
        },
    },
    {
        "id": 22,
        "topic": "self_description",
        "keywords": ["muba says", "how does muba describe itself", "muba self description",
                     "muba kendini nasıl tanımlar", "muba kendisi", "自我介绍", "وصف muba لنفسها", "muba खुद को कैसे बताता है"],
        "answers": {
            "en": "I'm MUBA. MUBA is MUBA.",
            "tr": "Ben MUBA'yım. MUBA, MUBA'dır.",
            "zh": "我是 MUBA。MUBA 就是 MUBA。",
            "ar": "أنا MUBA. MUBA هي MUBA.",
            "hi": "मैं MUBA हूँ। MUBA, MUBA है।",
        },
    },
    {
        "id": 23,
        "topic": "keywords",
        "keywords": ["muba keywords", "keywords of muba", "muba anahtar kelimeleri",
                     "anahtar kelimeler", "关键词", "الكلمات المفتاحية", "कीवर्ड"],
        "answers": {
            "en": "Core MUBA words: Character, Meme, Community, Culture, Chaos, Humor, Participation, Identity, Internet culture, Ridiculous energy, Timeline, Butterfly effect, Same Meme. Different Universe.",
            "tr": "MUBA'nın temel kelimeleri: Karakter, Meme, Topluluk, Kültür, Kaos, Mizah, Katılım, Kimlik, İnternet kültürü, Absürt enerji, Timeline, Kelebek etkisi, Same Meme. Different Universe.",
            "zh": "MUBA 的核心关键词：角色、meme、社区、文化、混乱、幽默、参与、身份、互联网文化、荒诞能量、时间线、蝴蝶效应、Same Meme. Different Universe.",
            "ar": "كلمات MUBA الأساسية: شخصية، ميم، مجتمع، ثقافة، فوضى، فكاهة، مشاركة، هوية، ثقافة الإنترنت، طاقة عبثية، الخط الزمني، تأثير الفراشة، Same Meme. Different Universe.",
            "hi": "MUBA के मुख्य शब्द: कैरेक्टर, मीम, कम्युनिटी, कल्चर, कैओस, ह्यूमर, पार्टिसिपेशन, आइडेंटिटी, इंटरनेट कल्चर, रिडिक्युलस एनर्जी, टाइमलाइन, बटरफ्लाई इफ़ेक्ट, Same Meme. Different Universe.",
        },
    },
    {
        "id": 24,
        "topic": "core_messages",
        "keywords": ["muba slogans", "muba catchphrase", "muba motto", "muba slogan",
                     "muba sloganları", "sözleri", "口号", "شعارات muba", "muba नारे"],
        "answers": {
            "en": "Core MUBA lines: I'm MUBA. A character. A meme. A community. We're not going anywhere. We Live Here Now. Same Meme. Different Universe. No complicated plans. No fake promises. Memes. Chaos. Community. You have a place here. MUBA stays MUBA.",
            "tr": "Temel MUBA sözleri: I'm MUBA. A character. A meme. A community. We're not going anywhere. We Live Here Now. Same Meme. Different Universe. No complicated plans. No fake promises. Memes. Chaos. Community. You have a place here. MUBA stays MUBA.",
            "zh": "MUBA 的核心表达包括：I'm MUBA. A character. A meme. A community. We're not going anywhere. We Live Here Now. Same Meme. Different Universe. No complicated plans. No fake promises. Memes. Chaos. Community. You have a place here. MUBA stays MUBA.",
            "ar": "عبارات MUBA الأساسية تشمل: I'm MUBA. A character. A meme. A community. We're not going anywhere. We Live Here Now. Same Meme. Different Universe. No complicated plans. No fake promises. Memes. Chaos. Community. You have a place here. MUBA stays MUBA.",
            "hi": "MUBA की मुख्य लाइन्स हैं: I'm MUBA. A character. A meme. A community. We're not going anywhere. We Live Here Now. Same Meme. Different Universe. No complicated plans. No fake promises. Memes. Chaos. Community. You have a place here. MUBA stays MUBA.",
        },
    },
    {
        "id": 25,
        "topic": "current_information",
        "keywords": ["muba contract address", "muba ca", "muba price", "muba market cap",
                     "muba listing", "muba launch", "muba current", "muba latest",
                     "muba kontrat", "muba ca ne", "muba fiyat", "muba listeleme",
                     "muba sözleşme", "合约地址", "价格", "上市", "عنوان العقد", "سعر", "पता", "कीमत"],
        "answers": {
            "en": "Current details such as contract address, price, market data, listings, and new announcements must be verified from the official source before being stated as facts. The official page currently says: CA coming soon.",
            "tr": "Kontrat adresi, fiyat, piyasa verileri, listelemeler ve yeni duyurular gibi güncel bilgiler resmi kaynaktan doğrulanmadan gerçekmiş gibi söylenmemelidir. Resmi sayfada şu an: CA coming soon.",
            "zh": "合约地址、价格、市场数据、上市信息和新公告等当前信息，必须先从官方来源验证后才能作为事实发布。官方页面目前显示：CA coming soon。",
            "ar": "المعلومات الحالية مثل عنوان العقد والسعر وبيانات السوق والإدراجات والإعلانات الجديدة يجب التحقق منها من المصدر الرسمي قبل عرضها كحقائق. الصفحة الرسمية حالياً تقول: CA coming soon.",
            "hi": "कॉन्ट्रैक्ट एड्रेस, कीमत, मार्केट डेटा, लिस्टिंग और नई घोषणाओं जैसी वर्तमान जानकारी को तथ्य की तरह बताने से पहले ऑफिशियल स्रोत से सत्यापित करना चाहिए। ऑफिशियल पेज पर अभी: CA coming soon.",
        },
    },
    {
        "id": 26,
        "topic": "master_summary",
        "keywords": ["muba summary", "full muba story", "everything about muba",
                     "tell me everything", "muba hakkında her şey", "muba özet",
                     "完整介绍 muba", "كل شيء عن muba", "muba के बारे में सब कुछ"],
        "answers": {
            "en": "MUBA is a character, meme, and community born from meme-world chaos. It grew from character to content, interaction, community, and culture. Its home is internet culture: WE LIVE HERE NOW. Its narrative connects with the Flap × Robinhood meme universe through Same Meme. Different Universe. The butterfly effect represents the possibility that a small movement can create a larger cultural effect. MUBA focuses on identity, community, humor, participation, and culture rather than complicated plans or fake promises. The future is intentionally open and community-driven. MUBA stays MUBA.",
            "tr": "MUBA, meme dünyasının kaosundan doğan bir karakter, meme ve topluluktur. Karakterden içeriğe, etkileşime, topluluğa ve kültüre doğru gelişti. Evi internet kültürü: WE LIVE HERE NOW. Anlatısı Flap × Robinhood meme evreniyle Same Meme. Different Universe. fikri üzerinden bağ kurar. Kelebek etkisi, küçük bir hareketin daha büyük kültürel etki oluşturabilme ihtimalini temsil eder. MUBA; karmaşık planlar veya sahte vaatler yerine kimlik, topluluk, mizah, katılım ve kültüre odaklanır. Geleceği bilerek açık ve topluluk odaklıdır. MUBA stays MUBA.",
            "zh": "MUBA 是从 meme 世界的混乱中诞生的角色、meme 和社区。它从角色发展到内容、互动、社区和文化。它的家是互联网文化：WE LIVE HERE NOW。其叙事通过 Same Meme. Different Universe. 与 Flap × Robinhood meme 宇宙产生联系。蝴蝶效应代表小动作可能产生更大文化影响的可能性。MUBA 重视身份、社区、幽默、参与和文化，而不是复杂计划或虚假承诺。未来有意保持开放并由社区共同塑造。MUBA stays MUBA。",
            "ar": "MUBA شخصية وميم ومجتمع وُلد من فوضى عالم الميمات. تطورت من شخصية إلى محتوى وتفاعل ومجتمع وثقافة. موطنها ثقافة الإنترنت: WE LIVE HERE NOW. يرتبط سردها بعالم Flap × Robinhood من خلال Same Meme. Different Universe. ويمثل تأثير الفراشة إمكانية أن تخلق حركة صغيرة أثراً ثقافياً أكبر. تركز MUBA على الهوية والمجتمع والفكاهة والمشاركة والثقافة بدلاً من الخطط المعقدة والوعود الزائفة. المستقبل مفتوح عمداً ويشكله المجتمع. MUBA stays MUBA.",
            "hi": "MUBA मीम की दुनिया की अराजकता से पैदा हुआ कैरेक्टर, मीम और कम्युनिटी है। यह कैरेक्टर से कंटेंट, इंटरैक्शन, कम्युनिटी और कल्चर तक विकसित हुआ। इसका घर इंटरनेट कल्चर है: WE LIVE HERE NOW. इसकी नैरेटिव Same Meme. Different Universe. के जरिए Flap × Robinhood मीम यूनिवर्स से जुड़ती है। बटरफ्लाई इफ़ेक्ट छोटी मूवमेंट से बड़े कल्चरल इम्पैक्ट की संभावना को दर्शाता है। MUBA जटिल प्लान और फेक प्रॉमिसेज़ के बजाय आइडेंटिटी, कम्युनिटी, ह्यूमर, पार्टिसिपेशन और कल्चर पर फोकस करता है। भविष्य जानबूझकर खुला और कम्युनिटी-ड्रिवन है। MUBA stays MUBA।",
        },
    },
]


# Extra natural-language patterns expand coverage without needing an external model.
INTENT_ALIASES = {
    "what_is_muba": [
        "explain muba", "tell me about muba", "muba info", "what exactly is muba",
        "muba hakkında bilgi", "muba nedir anlat", "muba ne demek", "muba hakkında konuş",
        "muba'yı anlat", "muba kim", "what even is muba", "muba bro what is it",
    ],
    "origin": [
        "how was muba created", "how did it begin", "where did the character come from",
        "muba nasıl doğdu", "muba nereden geldi", "nasıl başladı", "başlangıç hikayesi",
        "muba nasıl oluştu", "muba nasıl yaratıldı",
    ],
    "character": [
        "describe muba", "muba features", "muba personality", "what is muba like",
        "muba nasıl biri", "muba özellikleri neler", "görünüşü nasıl", "karakteri nasıl",
    ],
    "purpose": [
        "why muba", "what is the point", "what does muba want", "muba ne istiyor",
        "muba amacı ne", "amacı nedir", "neden var", "niye muba",
    ],
    "community": [
        "who is the community", "what is the community like", "muba community meaning",
        "topluluk nasıl", "topluluk ne", "kimler burada", "muba topluluğu nedir",
    ],
    "future": [
        "what happens next", "where is muba going", "what comes next", "next for muba",
        "sonra ne olacak", "bundan sonra ne var", "muba nereye gidiyor", "gelecekte ne var",
    ],
    "team": [
        "who is the team", "who are the devs", "who made muba", "developers",
        "muba ekibi", "ekip kim", "geliştirici kim", "dev kim", "kurucu kim",
    ],
    "listing": [
        "when listing", "where listed", "exchange listing", "when launch", "launch date",
        "ne zaman listelenecek", "hangi borsa", "listeleme ne zaman", "ne zaman çıkıyor",
        "lansman ne zaman", "launch ne zaman",
    ],
    "website": [
        "official website", "muba website", "site", "web site", "resmi site",
        "muba'nın sitesi", "muba web sitesi",
    ],
    "telegram": [
        "official telegram", "telegram group", "telegram channel", "muba telegram",
        "telegram adresi", "telegram nerede", "resmi telegram",
    ],
    "socials": [
        "socials", "social media", "twitter", "x account", "muba x",
        "sosyal medya", "x hesabı", "twitter hesabı", "resmi hesaplar",
    ],
    "team": [
        "team", "dev team", "developers", "founder", "founders", "creator",
        "ekip", "geliştiriciler", "kurucu", "kurucular", "yaratıcı",
    ],
}


def _knowledge_index() -> Dict[str, dict]:
    return {item["topic"]: item for item in KNOWLEDGE}


KNOWLEDGE_INDEX = _knowledge_index()

STATIC_INTENTS = {
    "team": {
        "en": "The team? MUBA. The official identity does not require invented names or people. If official team details are announced, use the official source.",
        "tr": "Ekip mi? MUBA. Resmi kimlikte uydurma isimler veya kişiler yok. Resmi ekip bilgisi açıklanırsa resmi kaynak esas alınır.",
        "zh": "团队？MUBA。官方身份不会凭空编造人员姓名。如果官方公布团队信息，应以官方来源为准。",
        "ar": "الفريق؟ MUBA. الهوية الرسمية لا تعتمد على أسماء أشخاص مخترعة. إذا تم الإعلان عن تفاصيل الفريق، فالمصدر الرسمي هو المرجع.",
        "hi": "टीम? MUBA। ऑफिशियल आइडेंटिटी में बनाए हुए नाम या लोग नहीं हैं। अगर ऑफिशियल टीम डिटेल्स घोषित होती हैं, तो ऑफिशियल स्रोत ही मान्य है।",
    },
    "listing": {
        "en": "Listing details should come from an official announcement. Until then: wait for the official announcement.",
        "tr": "Listeleme bilgisi resmi duyurudan gelmelidir. O zamana kadar: resmi duyuruyu bekleyin.",
        "zh": "上市信息应以官方公告为准。在此之前：等待官方公告。",
        "ar": "تفاصيل الإدراج يجب أن تأتي من إعلان رسمي. حتى ذلك الحين: انتظروا الإعلان الرسمي.",
        "hi": "लिस्टिंग की जानकारी ऑफिशियल अनाउंसमेंट से आनी चाहिए। तब तक: ऑफिशियल अनाउंसमेंट का इंतज़ार करें।",
    },
    "website": {
        "en": "The official MUBA website is muba-rh.github.io/MUBA/.",
        "tr": "Resmi MUBA sitesi: muba-rh.github.io/MUBA/",
        "zh": "MUBA 官方网站：muba-rh.github.io/MUBA/",
        "ar": "الموقع الرسمي لـ MUBA هو: muba-rh.github.io/MUBA/",
        "hi": "MUBA की ऑफिशियल वेबसाइट: muba-rh.github.io/MUBA/",
    },
    "telegram": {
        "en": "The official MUBA Telegram is t.me/MUBA_RH.",
        "tr": "Resmi MUBA Telegram: t.me/MUBA_RH",
        "zh": "MUBA 官方 Telegram：t.me/MUBA_RH",
        "ar": "تيليغرام MUBA الرسمي: t.me/MUBA_RH",
        "hi": "MUBA का ऑफिशियल Telegram: t.me/MUBA_RH",
    },
    "socials": {
        "en": "Official MUBA channels: Website — muba-rh.github.io/MUBA/ | Telegram — t.me/MUBA_RH | X — x.com/MUBA_RH. For current details, use the official channels.",
        "tr": "Resmi MUBA kanalları: Website — muba-rh.github.io/MUBA/ | Telegram — t.me/MUBA_RH | X — x.com/MUBA_RH. Güncel bilgiler için resmi kanallar kullanılmalı.",
        "zh": "MUBA 官方渠道：网站 — muba-rh.github.io/MUBA/ | Telegram — t.me/MUBA_RH | X — x.com/MUBA_RH。当前信息请以官方渠道为准。",
        "ar": "قنوات MUBA الرسمية: الموقع — muba-rh.github.io/MUBA/ | تيليغرام — t.me/MUBA_RH | X — x.com/MUBA_RH. للمعلومات الحالية استخدم القنوات الرسمية.",
        "hi": "MUBA के ऑफिशियल चैनल: Website — muba-rh.github.io/MUBA/ | Telegram — t.me/MUBA_RH | X — x.com/MUBA_RH। वर्तमान जानकारी के लिए ऑफिशियल चैनल देखें।",
    },
}


FALLBACKS = {
    "en": [
        "MUBA is here. Ask again — if it is about MUBA, there is a way in. 🪶",
        "Still MUBA. Try the question another way. 🪶",
        "MUBA heard you. Give me the angle: character, story, community, future, or meme culture?",
        "No complicated answer needed. It's MUBA. 🪶",
    ],
    "tr": [
        "MUBA burada. Bir daha sor — MUBA ile ilgiliyse bir cevabı vardır. 🪶",
        "Hâlâ MUBA. Soruyu başka şekilde dene. 🪶",
        "MUBA seni duydu. Karakter, hikâye, topluluk, gelecek veya meme kültürü tarafından sorabilirsin.",
        "Karmaşık cevap gerekmiyor. MUBA işte. 🪶",
    ],
    "zh": [
        "MUBA 在这里。再问一次——只要是关于 MUBA，总有入口。🪶",
        "还是 MUBA。换一种方式问问。🪶",
        "MUBA 听到了。可以从角色、故事、社区、未来或 meme 文化来问。",
        "不需要复杂答案。就是 MUBA。🪶",
    ],
    "ar": [
        "MUBA هنا. اسأل مرة أخرى — إذا كان السؤال عن MUBA فهناك جواب. 🪶",
        "ما زالت MUBA. جرّب صياغة السؤال بطريقة أخرى. 🪶",
        "MUBA تسمعك. اسأل عن الشخصية أو القصة أو المجتمع أو المستقبل أو ثقافة الميمات.",
        "لا نحتاج إلى إجابة معقدة. إنها MUBA. 🪶",
    ],
    "hi": [
        "MUBA यहाँ है। फिर पूछो — अगर सवाल MUBA के बारे में है, तो रास्ता है। 🪶",
        "अब भी MUBA। सवाल को दूसरे तरीके से पूछो। 🪶",
        "MUBA ने सुना। कैरेक्टर, कहानी, कम्युनिटी, भविष्य या मीम कल्चर से पूछ सकते हो।",
        "जटिल जवाब की जरूरत नहीं। MUBA है। 🪶",
    ],
}


SOCIAL_REPLIES = {
    "gm": {
        "en": ["GM 🪶", "GM. We live here now. 🪶", "GM. MUBA is awake."],
        "tr": ["GM 🪶", "GM. We live here now. 🪶", "GM. MUBA burada."],
        "zh": ["GM 🪶", "GM。WE LIVE HERE NOW. 🪶", "GM。MUBA 在这里。"],
        "ar": ["GM 🪶", "GM. WE LIVE HERE NOW. 🪶", "GM. MUBA هنا."],
        "hi": ["GM 🪶", "GM. WE LIVE HERE NOW. 🪶", "GM. MUBA यहाँ है।"],
    },
    "gn": {
        "en": ["GN 🪶", "GN. Keep the memes alive. 🪶", "GN. MUBA stays here."],
        "tr": ["GN 🪶", "GN. Meme'leri canlı tut. 🪶", "GN. MUBA burada kalır."],
        "zh": ["GN 🪶", "GN。让 meme 继续活着。🪶", "GN。MUBA 还在这里。"],
        "ar": ["GN 🪶", "GN. أبقوا الميمات حية. 🪶", "GN. MUBA باقية هنا."],
        "hi": ["GN 🪶", "GN. मीम्स को ज़िंदा रखो। 🪶", "GN. MUBA यहीं है।"],
    },
    "checkin": {
        "en": ["Still MUBA. That's a good sign. 🪶", "Alive. Memes are alive too.", "Not much. Just living here. 🪶"],
        "tr": ["Hâlâ MUBA. Bu iyiye işaret. 🪶", "Canlı. Meme'ler de canlı.", "Pek bir şey yok. Sadece burada yaşıyorum. 🪶"],
        "zh": ["还是 MUBA。看来不错。🪶", "还活着，meme 也活着。", "没什么，只是在这里生活。🪶"],
        "ar": ["ما زالت MUBA. وهذه علامة جيدة. 🪶", "حية. والميمات حية أيضاً.", "لا شيء كثيراً. فقط نعيش هنا. 🪶"],
        "hi": ["अब भी MUBA। यह अच्छा संकेत है।🪶", "ज़िंदा हूँ। मीम्स भी ज़िंदा हैं।", "कुछ खास नहीं। बस यहीं रह रहे हैं। 🪶"],
    },
}


def is_greeting(text: str) -> Optional[str]:
    value = normalize(text)
    compact = re.sub(r"[^a-z]", "", value)

    if compact in {"gm", "goodmorning", "morning"}:
        return "gm"
    if compact in {"gn", "goodnight", "night"}:
        return "gn"
    if compact in {"howareyou", "whatsup", "wassup", "sup", "howsitgoing"}:
        return "checkin"
    return None


def _score_item(query: str, item: dict) -> float:
    q = normalize(query)
    q_tokens = set(tokens(q))
    best = 0.0

    for phrase in item.get("keywords", []):
        p = normalize(phrase)
        if not p:
            continue

        if p in q:
            best = max(best, 1.0)
            continue

        phrase_tokens = set(tokens(p))
        overlap = len(q_tokens & phrase_tokens) / max(1, len(phrase_tokens))
        fuzzy = similarity(q, p)

        best = max(best, overlap * 0.78 + fuzzy * 0.22)

    return best


def _score_aliases(query: str, topic: str) -> float:
    best = 0.0
    for phrase in INTENT_ALIASES.get(topic, []):
        p = normalize(phrase)
        if p in normalize(query):
            return 1.0
        best = max(best, similarity(query, p))
    return best


def _detect_static_intent(query: str) -> Optional[str]:
    value = normalize(query)

    for intent, phrases in INTENT_ALIASES.items():
        for phrase in phrases:
            if normalize(phrase) in value:
                return intent

    team_words = ["team", "dev", "developer", "founder", "founders", "ekip",
                  "geliştirici", "kurucu", "команда", "团队", "فريق", "टीम"]
    if any(word in value for word in team_words):
        return "team"

    listing_words = ["listing", "listed", "launch", "exchange", "listeleme",
                     "listelenecek", "lansman", "borsa", "上市", "交易所",
                     "إدراج", "إطلاق", "लिस्टिंग", "लॉन्च"]
    if any(word in value for word in listing_words):
        return "listing"

    if any(word in value for word in ["website", "web site", "site", "resmi site"]):
        return "website"

    if "telegram" in value:
        return "telegram"

    if any(word in value for word in ["twitter", "x account", "socials", "social media", "sosyal medya"]):
        return "socials"

    return None


def _pick_answer(item: dict, language: str) -> str:
    answer_set = item["answers"]
    return answer_set.get(language) or answer_set["en"]


def _add_natural_tail(answer: str, language: str, score: float) -> str:
    if score < 0.72:
        return answer

    tails = {
        "en": [" 🪶", " That's MUBA.", " MUBA stays MUBA. 🪶"],
        "tr": [" 🪶", " Mesele bu. MUBA.", " MUBA stays MUBA. 🪶"],
        "zh": [" 🪶", " 这就是 MUBA。", " MUBA stays MUBA. 🪶"],
        "ar": [" 🪶", " هذه هي MUBA.", " MUBA stays MUBA. 🪶"],
        "hi": [" 🪶", " यही MUBA है।", " MUBA stays MUBA. 🪶"],
    }
    if random.random() < 0.28:
        return answer.rstrip() + random.choice(tails[language])
    return answer


def answer(query: str, language: Optional[str] = None, force_muba: bool = False) -> str:
    text = query or ""
    lang = language if language in SUPPORTED_LANGUAGES else detect_language(text)

    greeting = is_greeting(text)
    if greeting and not contains_muba(text):
        return random.choice(SOCIAL_REPLIES[greeting][lang])

    if not contains_muba(text) and not force_muba:
        if greeting:
            return random.choice(SOCIAL_REPLIES[greeting][lang])
        return ""

    static_intent = _detect_static_intent(text)
    if static_intent in STATIC_INTENTS:
        return STATIC_INTENTS[static_intent][lang]

    # Current-information questions are intentionally handled conservatively.
    current_words = [
        "contract", "address", "ca", "price", "market cap", "marketcap", "listing",
        "launch", "volume", "holders", "liquidity", "exchange", "fiyat", "kontrat",
        "adres", "listeleme", "borsa", "hacim", "likidite", "持有人", "价格",
        "合约", "市值", "交易所", "السعر", "العقد", "القيمة السوقية", "المستثمرين",
        "कीमत", "कॉन्ट्रैक्ट", "मार्केट कैप", "लिस्टिंग",
    ]
    value = normalize(text)
    if any(word in value for word in current_words):
        return _pick_answer(KNOWLEDGE_INDEX["current_information"], lang)

    scored: List[Tuple[float, dict]] = []
    for item in KNOWLEDGE:
        score = _score_item(text, item)
        alias_score = _score_aliases(text, item["topic"])
        final_score = max(score, alias_score)
        scored.append((final_score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score, best_item = scored[0]

    if best_score >= 0.40:
        return _add_natural_tail(_pick_answer(best_item, lang), lang, best_score)

    # If the message clearly contains MUBA but is too unusual for a precise topic,
    # use a broad answer rather than leaving the user unanswered.
    if contains_muba(text):
        if any(word in value for word in ["who", "kim", "kto", "是谁", "من", "कौन"]):
            return _pick_answer(KNOWLEDGE_INDEX["who_is_muba"], lang)
        if any(word in value for word in ["why", "neden", "niye", "为什么", "لماذا", "क्यों"]):
            return _pick_answer(KNOWLEDGE_INDEX["purpose"], lang)
        if any(word in value for word in ["how", "nasıl", "怎么", "كيف", "कैसे"]):
            return _pick_answer(KNOWLEDGE_INDEX["master_summary"], lang)
        return random.choice(FALLBACKS[lang])

    return ""


def reply_to_message(query: str, language: Optional[str] = None) -> str:
    return answer(query, language=language, force_muba=False)


# ---------------------------------------------------------------------------
# Lightweight conversation state
# ---------------------------------------------------------------------------

class ConversationState:
    def __init__(self, cooldown_seconds: float = 8.0, max_turns: int = 8):
        self.cooldown_seconds = cooldown_seconds
        self.max_turns = max_turns
        self.last_reply: Dict[int, float] = {}
        self.active_turns: Dict[int, int] = {}

    def can_reply(self, chat_id: int, force: bool = False) -> bool:
        if force:
            return True
        last = self.last_reply.get(chat_id, 0.0)
        return (time.time() - last) >= self.cooldown_seconds

    def mark_reply(self, chat_id: int) -> None:
        self.last_reply[chat_id] = time.time()
        self.active_turns[chat_id] = min(self.active_turns.get(chat_id, 0) + 1, self.max_turns)

    def reset(self, chat_id: int) -> None:
        self.active_turns.pop(chat_id, None)

    def in_active_thread(self, chat_id: int) -> bool:
        return 0 < self.active_turns.get(chat_id, 0) < self.max_turns


STATE = ConversationState()


def build_reply(query: str, chat_id: Optional[int] = None, language: Optional[str] = None) -> str:
    chat_key = chat_id if chat_id is not None else 0
    force = contains_muba(query)

    if not STATE.can_reply(chat_key, force=force):
        return ""

    response = reply_to_message(query, language=language)
    if response:
        STATE.mark_reply(chat_key)
    return response
