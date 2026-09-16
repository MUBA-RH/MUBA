"""
MUBA Local Brain
Large offline knowledge base, multilingual intent matching, social behavior,
fuzzy matching, conversation context, and safe fallback handling.

No external AI service is required.

Supported languages:
- English
- Turkish
- Chinese
- Arabic
- Hindi

The brain is intentionally self-contained. It does not make network calls.
"""

from __future__ import annotations

import random
import re
import time
import unicodedata
from collections import defaultdict, deque
from difflib import SequenceMatcher
from typing import Deque, Dict, List, Optional, Tuple


# ============================================================
# CORE CONFIGURATION
# ============================================================

SUPPORTED_LANGUAGES = ("en", "tr", "zh", "ar", "hi")

SOCIAL_COOLDOWN_SECONDS = 90.0
SOCIAL_DAILY_LIMIT_SECONDS = 86400.0
MAX_CONTEXT_ITEMS = 8
FUZZY_THRESHOLD = 0.62
KEYWORD_THRESHOLD = 0.34


# ============================================================
# LANGUAGE DETECTION
# ============================================================

LANGUAGE_HINTS = {
    "tr": {
        "words": {
            "nedir", "kim", "kimdir", "nasıl", "neden", "ne", "hangi",
            "ekip", "topluluk", "hikaye", "hikâye", "gelecek", "amaç",
            "felsefe", "karakter", "meme", "farklı", "özellik", "kültür",
            "nereden", "çıktı", "selam", "nasılsın", "naber", "günaydın",
            "iyi", "gece", "merhaba", "mrb", "slm", "salam", "heyy",
            "niye", "burada", "burda", "hakkında", "anlat", "söyle",
            "kimmiş", "neymiş", "neden", "amacı", "topluluğu",
        },
        "chars": set("çğıöşü"),
    },
    "en": {
        "words": {
            "what", "who", "how", "why", "where", "when", "team",
            "community", "story", "future", "purpose", "philosophy",
            "character", "meme", "different", "culture", "origin",
            "hello", "hey", "morning", "night", "about", "tell",
            "explain", "meaning", "goal", "identity", "home",
        },
        "chars": set(),
    },
    "zh": {
        "words": {
            "什么", "是谁", "为什么", "怎么样", "怎么", "社区", "故事",
            "未来", "团队", "角色", "表情包", "文化", "起源", "你好",
            "早上好", "晚安", "目的", "意义", "区别", "为什么",
        },
        "chars": set(),
    },
    "ar": {
        "words": {
            "ما", "هو", "هي", "من", "لماذا", "كيف", "أين", "فريق",
            "مجتمع", "قصة", "مستقبل", "شخصية", "ميم", "ثقافة", "أصل",
            "مرحبا", "أهلا", "صباح", "ليل", "هدف", "معنى", "لماذا",
        },
        "chars": set(),
    },
    "hi": {
        "words": {
            "क्या", "कौन", "क्यों", "कैसे", "कहां", "कहाँ", "टीम",
            "समुदाय", "कहानी", "भविष्य", "चरित्र", "मीम", "संस्कृति",
            "शुरुआत", "नमस्ते", "सुबह", "रात", "उद्देश्य", "मतलब",
            "अलग", "क्योंकि",
        },
        "chars": set(),
    },
}


STOP_WORDS = {
    "en": {
        "the", "is", "a", "an", "and", "or", "of", "to", "in", "on",
        "for", "do", "does", "did", "can", "you", "tell", "me", "about",
        "what", "who", "how", "why", "where", "when", "please",
    },
    "tr": {
        "bir", "bu", "ve", "veya", "ile", "için", "icin", "mi", "mı",
        "mu", "mü", "ne", "nedir", "bana", "hakkında", "olan", "olarak",
        "şey", "şu", "da", "de", "ya", "yani", "sen", "ben",
    },
    "zh": {
        "的", "是", "吗", "呢", "和", "与", "关于", "什么", "了", "在",
        "有", "我", "你", "他", "她",
    },
    "ar": {
        "ما", "هو", "هي", "من", "عن", "في", "هل", "و", "أو", "هذا",
        "هذه", "كيف", "لماذا",
    },
    "hi": {
        "क्या", "है", "हैं", "का", "की", "के", "और", "में", "से", "को",
        "यह", "वह", "मैं", "आप", "तुम",
    },
}


def normalize(text: str) -> str:
    """Normalize text while preserving multilingual characters."""
    value = unicodedata.normalize("NFKC", text or "").lower()
    value = value.replace("ı", "i")
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", value)
    value = re.sub(
        r"[\u0300-\u036f]",
        "",
        unicodedata.normalize("NFD", value),
    )
    value = re.sub(r"[@#$%&*_+=~`|<>[\]{}()]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def tokens(text: str) -> List[str]:
    """Return multilingual word/token units."""
    return re.findall(
        r"[a-z0-9çğıöşü]+|[\u3400-\u9fff]|[\u0600-\u06ff]+|[\u0900-\u097f]+",
        normalize(text),
    )


def detect_language(text: str) -> str:
    """Detect one of the five supported response languages."""
    value = normalize(text)

    if any("\u4e00" <= ch <= "\u9fff" for ch in value):
        return "zh"

    if any("\u0600" <= ch <= "\u06ff" for ch in value):
        return "ar"

    if any("\u0900" <= ch <= "\u097f" for ch in value):
        return "hi"

    scores = {language: 0 for language in SUPPORTED_LANGUAGES}
    words = set(tokens(value))

    for language, data in LANGUAGE_HINTS.items():
        scores[language] += sum(1 for word in data["words"] if word in value)
        scores[language] += sum(1 for word in data["words"] if word in words)
        scores[language] += sum(1 for ch in data["chars"] if ch in value)

    if scores["tr"] > scores["en"]:
        return "tr"

    return "en"


# ============================================================
# MUBA NAME / MENTION DETECTION
# ============================================================

def contains_muba(text: str) -> bool:
    """Detect MUBA references including common spacing and typo variants."""
    value = normalize(text)

    if re.search(r"\bmub+a+\b", value):
        return True

    compact = re.sub(r"[^a-z]", "", value)

    if "muba" in compact:
        return True

    if re.search(r"\bm\s*u\s*b\s*a\b", value):
        return True

    fuzzy_candidates = re.findall(r"\b[a-z]{3,6}\b", value)

    for candidate in fuzzy_candidates:
        if SequenceMatcher(None, candidate, "muba").ratio() >= 0.82:
            return True

    return False


# ============================================================
# TEXT MATCHING
# ============================================================

def similarity(a: str, b: str) -> float:
    """Return normalized text similarity."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def _clean_for_match(text: str) -> str:
    value = normalize(text)

    for language_words in STOP_WORDS.values():
        for word in language_words:
            value = re.sub(rf"\b{re.escape(word)}\b", " ", value)

    return re.sub(r"\s+", " ", value).strip()


def _keyword_score(query: str, keywords: List[str]) -> float:
    cleaned = _clean_for_match(query)

    if not cleaned:
        return 0.0

    best = 0.0

    for keyword in keywords:
        target = _clean_for_match(keyword)

        if not target:
            continue

        if target in cleaned:
            best = max(best, 1.0)
            continue

        ratio = similarity(cleaned, target)

        if ratio > best:
            best = ratio

    return best


def _token_overlap(query: str, keyword: str) -> float:
    q = set(tokens(_clean_for_match(query)))
    k = set(tokens(_clean_for_match(keyword)))

    if not q or not k:
        return 0.0

    return len(q & k) / max(1, len(k))


# ============================================================
# MASTER KNOWLEDGE BASE
# ============================================================

KNOWLEDGE: List[Dict] = [
    {
        "id": 1,
        "topic": "what_is_muba",
        "keywords": [
            "what is muba",
            "what's muba",
            "define muba",
            "muba meaning",
            "muba nedir",
            "muba ne",
            "muba kim",
            "muba ne demek",
            "什么是muba",
            "muba是什么",
            "ما هو muba",
            "ما هي muba",
            "muba क्या है",
        ],
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
        "keywords": [
            "muba origin",
            "how did muba start",
            "where did muba come from",
            "how was muba created",
            "muba nasıl çıktı",
            "muba nasıl ortaya çıktı",
            "muba nereden çıktı",
            "muba nasıl başladı",
            "muba起源",
            "muba怎么诞生",
            "muba从哪里来",
            "من أين جاءت muba",
            "كيف بدأت muba",
            "muba कैसे शुरू हुआ",
            "muba कहाँ से आया",
        ],
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
        "keywords": [
            "who is muba",
            "muba kimdir",
            "muba karakteri kim",
            "who exactly is muba",
            "muba是谁",
            "谁是muba",
            "من هي muba",
            "muba कौन है",
        ],
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
        "keywords": [
            "muba character",
            "character traits",
            "what does muba look like",
            "muba appearance",
            "muba characteristics",
            "muba karakter özellikleri",
            "muba karakteri",
            "muba görünüşü",
            "muba nasıl görünüyor",
            "muba长什么样",
            "muba شخصية",
            "muba कैरेक्टर",
        ],
        "answers": {
            "en": "MUBA is cute, absurd, unique, humorous, natural, meme-native, confident, and recognizable. The visual identity includes large expressive eyes, short dense fur, a pink tongue, a black MUBA hat, and a black hoodie marked $MUBA.",
            "tr": "MUBA sevimli, absürt, özgün, komik, doğal, meme kültürüne ait, özgüvenli ve tanınabilir. Görsel kimliğinde büyük ifadeli gözler, kısa yoğun tüyler, pembe dil, siyah MUBA şapkası ve üzerinde $MUBA bulunan siyah hoodie vardır.",
            "zh": "MUBA 可爱、荒诞、独特、幽默、自然、原生于 meme 文化、自信且容易辨认。视觉身份包括大而有表现力的眼睛、短而浓密的毛发、粉色舌头、黑色 MUBA 帽子和印有 $MUBA 的黑色连帽衫。",
            "ar": "MUBA لطيفة وعبثية وفريدة ومرحة وطبيعية وتنتمي لثقافة الميمات وواثقة وسهلة التعرف. هويتها البصرية تشمل عيوناً كبيرة معبرة، فروًا قصيراً كثيفاً، لساناً وردياً، قبعة MUBA سوداء وكنزة سوداء تحمل $MUBA.",
            "hi": "MUBA प्यारा, अजीब, यूनिक, मज़ेदार, नेचुरल, मीम कल्चर का हिस्सा, कॉन्फिडेंट और पहचानने योग्य है। इसकी विज़ुअल पहचान में बड़ी एक्सप्रेसिव आंखें, छोटे घने बाल/फर, गुलाबी जीभ, काली MUBA टोपी और $MUBA वाली काली हुडी शामिल है।",
        },
    },
    {
        "id": 5,
        "topic": "core_definition",
        "keywords": [
            "muba core",
            "what defines muba",
            "muba identity",
            "muba definition",
            "muba'nın özü",
            "muba kimliği",
            "muba özü",
            "muba核心",
            "muba身份",
            "هوية muba",
            "muba पहचान",
        ],
        "answers": {
            "en": "The core definition is simple: I'm MUBA. A character. A meme. A community.",
            "tr": "Temel tanım basit: Ben MUBA'yım. Bir karakter. Bir meme. Bir topluluk.",
            "zh": "核心定义很简单：我是 MUBA。一个角色。一个 meme。一个社区。",
            "ar": "التعريف الأساسي بسيط: أنا MUBA. شخصية. ميم. مجتمع.",
            "hi": "मुख्य परिभाषा सरल है: मैं MUBA हूँ। एक कैरेक्टर। एक मीम। एक कम्युनिटी।",
        },
    },
    {
        "id": 6,
        "topic": "purpose",
        "keywords": [
            "muba purpose",
            "purpose of muba",
            "what is muba for",
            "muba goal",
            "muba goals",
            "muba'nın amacı",
            "muba amacı",
            "muba ne amaçlıyor",
            "muba有什么目的",
            "muba的目标",
            "ما هدف muba",
            "هدف مجتمع muba",
            "muba का उद्देश्य",
            "muba का लक्ष्य",
        ],
        "answers": {
            "en": "MUBA exists to build a lasting cultural and community atmosphere around the character. People can talk, create memes, share ideas, participate, and help shape the story.",
            "tr": "MUBA'nın amacı karakter etrafında kalıcı bir kültür ve topluluk atmosferi oluşturmaktır. İnsanlar konuşabilir, meme üretebilir, fikir paylaşabilir, katılabilir ve hikâyenin şekillenmesine katkı verebilir.",
            "zh": "MUBA 的目的，是围绕这个角色建立持久的文化和社区氛围。人们可以交流、制作 meme、分享想法、参与其中，并一起塑造故事。",
            "ar": "تهدف MUBA إلى بناء أجواء ثقافية ومجتمعية مستمرة حول الشخصية. يمكن للناس التحدث وصنع الميمات ومشاركة الأفكار والمشاركة والمساعدة في تشكيل القصة.",
            "hi": "MUBA का उद्देश्य कैरेक्टर के आसपास एक टिकाऊ कम्युनिटी और कल्चरल माहौल बनाना है। लोग बात कर सकते हैं, मीम बना सकते हैं, आइडिया शेयर कर सकते हैं, भाग ले सकते हैं और कहानी को आकार देने में मदद कर सकते हैं।",
        },
    },
    {
        "id": 7,
        "topic": "growth",
        "keywords": [
            "how will muba grow",
            "muba growth",
            "muba development",
            "muba büyüme",
            "muba nasıl büyür",
            "muba nasıl gelişir",
            "muba发展",
            "muba成长",
            "كيف تنمو muba",
            "تطور muba",
            "muba कैसे बढ़ेगा",
            "muba कैसे विकसित होगा",
        ],
        "answers": {
            "en": "MUBA is not about empty hype or simply chasing the highest visibility. The focus is stronger identity, genuine interest, curiosity, conversation, participation, and community culture.",
            "tr": "MUBA boş hype peşinde koşmakla veya sadece en yüksek görünürlüğü hedeflemekle ilgili değil. Odak; daha güçlü kimlik, gerçek ilgi, merak, konuşma, katılım ve topluluk kültürü.",
            "zh": "MUBA 不是为了空洞的炒作，也不是单纯追求最高曝光。重点是更强的身份认同、真实兴趣、好奇心、交流、参与和社区文化。",
            "ar": "MUBA ليست عن الضجة الفارغة أو مجرد مطاردة أعلى ظهور. التركيز على هوية أقوى واهتمام حقيقي وفضول وحوار ومشاركة وثقافة مجتمعية.",
            "hi": "MUBA खाली हाइप या सिर्फ ज्यादा विज़िबिलिटी के बारे में नहीं है। फोकस मजबूत पहचान, असली रुचि, जिज्ञासा, बातचीत, भागीदारी और कम्युनिटी कल्चर पर है।",
        },
    },
    {
        "id": 8,
        "topic": "community",
        "keywords": [
            "muba community",
            "who is the community",
            "community of muba",
            "muba topluluğu",
            "muba topluluk",
            "muba社区",
            "muba社区是什么",
            "مجتمع muba",
            "مجتمع موبا",
            "muba समुदाय",
            "muba की कम्युनिटी",
        ],
        "answers": {
            "en": "MUBA's community is built around humor, meme culture, interaction, visuals, ideas, participation, and a shared feeling that there is a place here for you.",
            "tr": "MUBA topluluğu mizah, meme kültürü, etkileşim, görseller, fikirler ve katılım etrafında oluşur. Burada senin de bir yerin var.",
            "zh": "MUBA 社区建立在幽默、meme 文化、互动、视觉内容、想法和参与之上。这里有属于你的空间。",
            "ar": "مجتمع MUBA يقوم على الفكاهة وثقافة الميمات والتفاعل والمحتوى البصري والأفكار والمشاركة. لك مكان هنا.",
            "hi": "MUBA कम्युनिटी ह्यूमर, मीम कल्चर, इंटरैक्शन, विज़ुअल्स, आइडियाज़ और पार्टिसिपेशन पर बनी है। यहां आपके लिए भी जगह है।",
        },
    },
    {
        "id": 9,
        "topic": "meme_world",
        "keywords": [
            "muba meme world",
            "where does muba live",
            "muba home",
            "muba internet culture",
            "muba meme dünyası",
            "muba nerede yaşıyor",
            "muba'nın evi",
            "muba meme dünyasında",
            "muba在哪里",
            "muba的家",
            "عالم موبا",
            "أين تعيش muba",
            "muba कहाँ रहता है",
        ],
        "answers": {
            "en": "The natural home of MUBA is the meme world and internet culture. The timeline is part of the territory. We live here now.",
            "tr": "MUBA'nın doğal evi meme dünyası ve internet kültürüdür. Timeline bunun bir parçası. We Live Here Now.",
            "zh": "MUBA 的自然家园是 meme 世界和互联网文化。时间线也是这片土地的一部分。We Live Here Now。",
            "ar": "الموطن الطبيعي لـ MUBA هو عالم الميمات وثقافة الإنترنت. الخط الزمني جزء من هذه المساحة. We Live Here Now.",
            "hi": "MUBA का प्राकृतिक घर मीम की दुनिया और इंटरनेट कल्चर है। टाइमलाइन भी इसका हिस्सा है। We Live Here Now।",
        },
    },
    {
        "id": 10,
        "topic": "we_live_here_now",
        "keywords": [
            "we live here now",
            "what does we live here now mean",
            "muba slogan",
            "we live here now meaning",
            "we live here now muba",
            "we live here now ne demek",
            "muba sloganı",
            "burada yaşıyoruz şimdi",
            "we live here now什么意思",
            "we live here now معنى",
            "we live here now का मतलब",
        ],
        "answers": {
            "en": "WE LIVE HERE NOW means MUBA is already home in the meme world, internet culture, and its community. MUBA is not trying to become another identity or leave this place.",
            "tr": "WE LIVE HERE NOW, MUBA'nın meme dünyasında, internet kültüründe ve topluluğuyla birlikte zaten burada olduğunu anlatır. Başka bir kimliğe dönüşmeye veya buradan gitmeye çalışmıyoruz.",
            "zh": "WE LIVE HERE NOW 表示 MUBA 已经把 meme 世界、互联网文化和社区当作自己的家。MUBA 不需要变成另一个身份，也不会为了离开这里而改变自己。",
            "ar": "WE LIVE HERE NOW تعني أن MUBA موجودة بالفعل في عالم الميمات وثقافة الإنترنت ومع مجتمعها. لا تحاول أن تصبح هوية أخرى أو تغادر هذا المكان.",
            "hi": "WE LIVE HERE NOW का मतलब है कि MUBA मीम की दुनिया, इंटरनेट कल्चर और अपनी कम्युनिटी में पहले से घर पर है। MUBA किसी और पहचान में बदलने या यहां से जाने की कोशिश नहीं कर रहा।",
        },
    },
    {
        "id": 11,
        "topic": "robinhood_flap",
        "keywords": [
            "robinhood flap muba",
            "flap robinhood muba",
            "same meme different universe",
            "muba robinhood",
            "muba flap",
            "robinhood connection",
            "flap connection",
            "muba robinhood bağlantısı",
            "muba flap bağlantısı",
            "same meme different universe ne demek",
            "muba与robinhood",
            "muba和flap",
            "muba robinhood flap ما العلاقة",
            "muba robinhood flap क्या है",
        ],
        "answers": {
            "en": "The MUBA narrative describes Flap × Robinhood × MUBA as part of a broader meme universe: Same Meme. Different Universe. Robinhood is represented by a green feather, while Flap adds butterfly movement and effect. This should not be presented as a legal, commercial, listing, ownership, endorsement, or investment relationship without verified current information.",
            "tr": "MUBA anlatısında Flap × Robinhood × MUBA daha geniş bir meme evreninin parçası olarak ele alınır: Same Meme. Different Universe. Robinhood yeşil tüy ile, Flap ise kelebek hareketi ve etkisiyle temsil edilir. Doğrulanmış güncel bilgi olmadan bunu hukuki, ticari, listeleme, sahiplik, endorsement veya yatırım ilişkisi olarak anlatma.",
            "zh": "MUBA 的叙事将 Flap × Robinhood × MUBA 描述为更大 meme 宇宙的一部分：Same Meme. Different Universe. Robinhood 以绿色羽毛代表，Flap 增加蝴蝶般的运动与效果。除非有经过验证的最新信息，否则不要把它描述为法律、商业、上市、所有权、背书或投资关系。",
            "ar": "تصف قصة MUBA ‏Flap × Robinhood × MUBA كجزء من عالم ميمات أوسع: Same Meme. Different Universe. تمثل Robinhood ريشة خضراء، بينما يضيف Flap حركة وتأثير الفراشة. لا ينبغي وصف ذلك كعلاقة قانونية أو تجارية أو إدراج أو ملكية أو تأييد أو استثمار دون معلومات حديثة موثقة.",
            "hi": "MUBA की कहानी Flap × Robinhood × MUBA को एक बड़े मीम यूनिवर्स का हिस्सा बताती है: Same Meme. Different Universe. Robinhood को हरे पंख से और Flap को तितली जैसी मूवमेंट और इफेक्ट से दर्शाया जाता है। सत्यापित वर्तमान जानकारी के बिना इसे कानूनी, कमर्शियल, लिस्टिंग, ओनरशिप, एंडोर्समेंट या इन्वेस्टमेंट संबंध के रूप में पेश नहीं करना चाहिए।",
        },
    },
    {
        "id": 12,
        "topic": "butterfly_effect",
        "keywords": [
            "butterfly effect",
            "muba butterfly",
            "flap effect",
            "butterfly effect muba",
            "kelebek etkisi",
            "muba kelebek etkisi",
            "flap etkisi",
            "蝴蝶效应",
            "تأثير الفراشة",
            "तितली प्रभाव",
        ],
        "answers": {
            "en": "The butterfly effect in MUBA represents the idea that a small flap or movement can create a larger effect. It represents possibility, not a guarantee.",
            "tr": "MUBA'daki kelebek etkisi, küçük bir kanat çırpışının veya hareketin daha büyük bir etki yaratabileceği fikrini temsil eder. Bu bir olasılıktır, garanti değildir.",
            "zh": "MUBA 中的蝴蝶效应代表一个小小的动作可能产生更大的影响。它表达的是可能性，而不是保证。",
            "ar": "تأثير الفراشة في MUBA يمثل فكرة أن حركة صغيرة يمكن أن تؤدي إلى تأثير أكبر. إنها إمكانية وليست ضماناً.",
            "hi": "MUBA में बटरफ्लाई इफेक्ट यह विचार दर्शाता है कि एक छोटी सी हलचल बड़ा असर पैदा कर सकती है। यह संभावना है, गारंटी नहीं।",
        },
    },
    {
        "id": 13,
        "topic": "goals",
        "keywords": [
            "muba goals",
            "what are muba goals",
            "muba objectives",
            "muba'nın hedefleri",
            "muba hedefleri",
            "muba ne hedefliyor",
            "muba目标",
            "muba的目标是什么",
            "أهداف muba",
            "أهداف موبا",
            "muba के लक्ष्य",
        ],
        "answers": {
            "en": "MUBA's stated goals are a recognizable character, a strong active community, its own culture, and becoming a memorable character in internet culture.",
            "tr": "MUBA'nın hedefleri; tanınabilir bir karakter, güçlü ve aktif bir topluluk, kendine ait bir kültür oluşturmak ve internet kültüründe hatırlanan bir karakter olmaktır.",
            "zh": "MUBA 的目标包括建立容易辨认的角色、活跃而强大的社区、自己的文化，并成为互联网文化中令人记住的角色。",
            "ar": "تشمل أهداف MUBA شخصية مميزة وسهلة التعرف، مجتمعاً نشطاً وقوياً، ثقافة خاصة بها، وأن تصبح شخصية تُذكر في ثقافة الإنترنت.",
            "hi": "MUBA के लक्ष्यों में पहचानने योग्य कैरेक्टर, मजबूत एक्टिव कम्युनिटी, अपनी संस्कृति और इंटरनेट कल्चर में याद रहने वाला कैरेक्टर बनना शामिल है।",
        },
    },
    {
        "id": 14,
        "topic": "future",
        "keywords": [
            "muba future",
            "what is muba future",
            "where will muba go",
            "future of muba",
            "muba'nın geleceği",
            "muba geleceği",
            "muba nereye gidiyor",
            "muba的未来",
            "muba未来会怎样",
            "مستقبل muba",
            "ماذا سيحدث لـ muba",
            "muba का भविष्य",
            "muba आगे क्या करेगा",
        ],
        "answers": {
            "en": "MUBA's future is not completely written. The community can shape future content, ideas, and cultural elements. Time will show where it goes. MUBA stays MUBA.",
            "tr": "MUBA'nın geleceği tamamen yazılmış değil. Topluluk gelecekteki içerikleri, fikirleri ve kültürel unsurları şekillendirebilir. Nereye gideceğini zaman gösterecek. MUBA stays MUBA.",
            "zh": "MUBA 的未来还没有完全写好。社区可以塑造未来的内容、想法和文化元素。时间会告诉我们它会走向哪里。MUBA stays MUBA。",
            "ar": "مستقبل MUBA لم يُكتب بالكامل بعد. يمكن للمجتمع تشكيل المحتوى والأفكار والعناصر الثقافية القادمة. الوقت سيُظهر إلى أين تتجه. MUBA stays MUBA.",
            "hi": "MUBA का भविष्य पूरी तरह पहले से लिखा हुआ नहीं है। कम्युनिटी भविष्य के कंटेंट, आइडियाज़ और कल्चरल एलिमेंट्स को आकार दे सकती है। समय बताएगा यह कहां जाता है। MUBA stays MUBA।",
        },
    },
    {
        "id": 15,
        "topic": "difference",
        "keywords": [
            "why is muba different",
            "what makes muba different",
            "muba different from projects",
            "why muba is different",
            "muba neden farklı",
            "muba neyi farklı yapıyor",
            "muba projelerden farkı",
            "muba为什么不同",
            "muba有什么不同",
            "لماذا muba مختلفة",
            "ما الذي يميز muba",
            "muba अलग क्यों है",
            "muba में क्या अलग है",
        ],
        "answers": {
            "en": "MUBA is not built around being a technology company, a complicated product narrative, or endless promises. Its identity is centered on character, memes, community, culture, and participation.",
            "tr": "MUBA bir teknoloji şirketi, karmaşık bir ürün anlatısı veya sonsuz vaatler üzerine kurulmaz. Kimliği karakter, meme, topluluk, kültür ve katılım üzerine kuruludur.",
            "zh": "MUBA 不是围绕科技公司、复杂产品叙事或无尽承诺建立的。它的身份核心是角色、meme、社区、文化和参与。",
            "ar": "لا تقوم MUBA على كونها شركة تقنية أو قصة منتج معقدة أو وعود لا تنتهي. هويتها تتمحور حول الشخصية والميمات والمجتمع والثقافة والمشاركة.",
            "hi": "MUBA किसी टेक्नोलॉजी कंपनी, जटिल प्रोडक्ट नैरेटिव या अंतहीन वादों पर आधारित नहीं है। इसकी पहचान कैरेक्टर, मीम्स, कम्युनिटी, कल्चर और पार्टिसिपेशन पर केंद्रित है।",
        },
    },
    {
        "id": 16,
        "topic": "philosophy",
        "keywords": [
            "muba philosophy",
            "muba principles",
            "muba values",
            "muba felsefesi",
            "muba prensipleri",
            "muba değerleri",
            "muba理念",
            "muba哲学",
            "فلسفة muba",
            "مبادئ muba",
            "muba दर्शन",
            "muba के सिद्धांत",
        ],
        "answers": {
            "en": "MUBA's philosophy is simple: Be what you are. Grow with the community. Do not make unnecessary promises. Create culture. Stay here.",
            "tr": "MUBA'nın felsefesi basit: Olduğun şey ol. Toplulukla büyü. Gereksiz vaatlerde bulunma. Kültür oluştur. Burada kal.",
            "zh": "MUBA 的理念很简单：做自己。与社区一起成长。不要做不必要的承诺。创造文化。留在这里。",
            "ar": "فلسفة MUBA بسيطة: كن كما أنت. انمُ مع المجتمع. لا تقدم وعوداً غير ضرورية. اصنع ثقافة. ابق هنا.",
            "hi": "MUBA का दर्शन सरल है: जो हो वही रहो। कम्युनिटी के साथ बढ़ो। अनावश्यक वादे मत करो। कल्चर बनाओ। यहीं रहो।",
        },
    },
    {
        "id": 17,
        "topic": "story",
        "keywords": [
            "muba story",
            "how does muba story develop",
            "muba lore",
            "muba hikayesi",
            "muba'nın hikayesi",
            "muba hikâyesi",
            "muba故事",
            "muba的故事",
            "قصة muba",
            "قصة موبا",
            "muba की कहानी",
        ],
        "answers": {
            "en": "MUBA's story develops through the community: people create content and memes, use the character, share ideas, talk, and contribute to the culture. The story develops together.",
            "tr": "MUBA'nın hikâyesi toplulukla gelişir: insanlar içerik ve meme üretir, karakteri kullanır, fikir paylaşır, konuşur ve kültüre katkıda bulunur. Hikâye birlikte gelişir.",
            "zh": "MUBA 的故事通过社区发展：人们制作内容和 meme、使用角色、分享想法、交流并参与文化建设。故事是一起发展的。",
            "ar": "تتطور قصة MUBA من خلال المجتمع: يصنع الناس المحتوى والميمات ويستخدمون الشخصية ويشاركون الأفكار ويتحدثون ويساهمون في الثقافة. القصة تتطور معاً.",
            "hi": "MUBA की कहानी कम्युनिटी के जरिए विकसित होती है: लोग कंटेंट और मीम बनाते हैं, कैरेक्टर का इस्तेमाल करते हैं, आइडिया शेयर करते हैं, बात करते हैं और कल्चर में योगदान देते हैं। कहानी साथ में विकसित होती है।",
        },
    },
    {
        "id": 18,
        "topic": "possibilities",
        "keywords": [
            "could muba become a legend",
            "muba possibilities",
            "what could muba become",
            "muba legend",
            "muba ne olabilir",
            "muba efsane olabilir mi",
            "muba neye dönüşebilir",
            "muba可能成为传奇吗",
            "muba会成为什么",
            "هل يمكن أن تصبح muba أسطورة",
            "muba क्या बन सकता है",
        ],
        "answers": {
            "en": "MUBA may become a legend, the weirdest character on the timeline, or simply a community that had a great time together. These are possibilities, not promises.",
            "tr": "MUBA bir efsaneye, timeline'ın en garip karakterine dönüşebilir veya sadece birlikte güzel vakit geçiren bir topluluk olabilir. Bunlar olasılıktır, vaat değildir.",
            "zh": "MUBA 可能成为一个传奇、时间线上最奇怪的角色，也可能只是一个一起开心的社区。这些都是可能性，而不是承诺。",
            "ar": "قد تصبح MUBA أسطورة أو أغرب شخصية على الخط الزمني، أو قد يكون الأمر ببساطة مجتمعاً استمتع معاً. هذه احتمالات وليست وعوداً.",
            "hi": "MUBA एक लेजेंड, टाइमलाइन का सबसे अजीब कैरेक्टर या बस साथ में मज़ा करने वाली कम्युनिटी बन सकता है। ये संभावनाएं हैं, वादे नहीं।",
        },
    },
    {
        "id": 19,
        "topic": "avoids",
        "keywords": [
            "what does muba avoid",
            "muba avoids",
            "what muba does not do",
            "muba ne yapmaz",
            "muba'nın kaçındığı şeyler",
            "muba nelerden uzak",
            "muba避免什么",
            "muba不做什么",
            "ما الذي تتجنبه muba",
            "muba किन चीजों से बचता है",
        ],
        "answers": {
            "en": "MUBA avoids complicated plans, fake or endless promises, forced explanations, and borrowed identity.",
            "tr": "MUBA; karmaşık planlardan, sahte veya bitmeyen vaatlerden, zorla yapılan açıklamalardan ve ödünç kimlikten uzak durur.",
            "zh": "MUBA 避免复杂计划、虚假或无尽承诺、强行解释以及借来的身份。",
            "ar": "تتجنب MUBA الخطط المعقدة والوعود الزائفة أو التي لا تنتهي والتفسيرات القسرية والهوية المستعارة.",
            "hi": "MUBA जटिल प्लान, झूठे या अंतहीन वादे, जबरदस्ती की व्याख्या और उधार ली हुई पहचान से बचता है।",
        },
    },
    {
        "id": 20,
        "topic": "identity_boundaries",
        "keywords": [
            "official muba information",
            "muba official vs community",
            "is this official muba",
            "muba identity boundaries",
            "muba resmi bilgi",
            "muba resmi mi",
            "muba topluluk içeriği",
            "muba官方信息",
            "muba官方和社区",
            "معلومات muba الرسمية",
            "موبا رسمي",
            "muba आधिकारिक जानकारी",
        ],
        "answers": {
            "en": "Official MUBA identity and community-created content are different. Rumors and opinions are not automatically official facts, and future possibilities are not confirmed facts.",
            "tr": "Resmî MUBA kimliği ile topluluk tarafından oluşturulan içerik farklıdır. Söylentiler ve görüşler otomatik olarak resmî gerçek değildir; gelecek olasılıkları da doğrulanmış gerçekler değildir.",
            "zh": "MUBA 的官方身份与社区创作内容是不同的。传言和观点不会自动成为官方事实，未来可能性也不是已经确认的事实。",
            "ar": "هوية MUBA الرسمية ومحتوى المجتمع شيئان مختلفان. الشائعات والآراء ليست حقائق رسمية تلقائياً، والاحتمالات المستقبلية ليست حقائق مؤكدة.",
            "hi": "आधिकारिक MUBA पहचान और कम्युनिटी द्वारा बनाया गया कंटेंट अलग हैं। अफवाहें और राय अपने आप आधिकारिक तथ्य नहीं बनतीं, और भविष्य की संभावनाएं पुष्टि किए हुए तथ्य नहीं हैं।",
        },
    },
    {
        "id": 21,
        "topic": "one_sentence",
        "keywords": [
            "muba in one sentence",
            "describe muba in one sentence",
            "muba one line",
            "muba tek cümle",
            "muba tek cümlede",
            "muba一句话",
            "一句话介绍muba",
            "muba في جملة",
            "muba في سطر واحد",
            "muba एक वाक्य में",
        ],
        "answers": {
            "en": "MUBA is a character that emerged from the chaos of the meme world, has its own identity, and became the center of a community building its own culture around it.",
            "tr": "MUBA, meme dünyasının kaosundan doğan, kendi kimliğine sahip olan ve etrafında kendi kültürünü oluşturan bir topluluğun merkezine dönüşen bir karakterdir.",
            "zh": "MUBA 是一个从 meme 世界的混乱中诞生、拥有自己身份，并逐渐成为一个围绕它建立独特文化的社区核心的角色。",
            "ar": "MUBA شخصية ظهرت من فوضى عالم الميمات ولها هويتها الخاصة وأصبحت مركز مجتمع يبني ثقافته الخاصة حولها.",
            "hi": "MUBA एक ऐसा कैरेक्टर है जो मीम की दुनिया की अराजकता से निकला, अपनी पहचान बनाई और ऐसी कम्युनिटी का केंद्र बन गया जो अपनी संस्कृति बना रही है।",
        },
    },
    {
        "id": 22,
        "topic": "self_description",
        "keywords": [
            "how would muba describe itself",
            "muba self description",
            "muba who are you really",
            "muba kendini nasıl tanımlar",
            "muba kendini nasıl anlatır",
            "muba自己介绍",
            "muba如何介绍自己",
            "كيف تصف muba نفسها",
            "muba अपना परिचय",
        ],
        "answers": {
            "en": "I'm MUBA. MUBA is MUBA. A character. A meme. A community.",
            "tr": "Ben MUBA'yım. MUBA, MUBA'dır. Bir karakter. Bir meme. Bir topluluk.",
            "zh": "我是 MUBA。MUBA 就是 MUBA。一个角色。一个 meme。一个社区。",
            "ar": "أنا MUBA. MUBA هي MUBA. شخصية. ميم. مجتمع.",
            "hi": "मैं MUBA हूँ। MUBA ही MUBA है। एक कैरेक्टर। एक मीम। एक कम्युनिटी।",
        },
    },
    {
        "id": 23,
        "topic": "keywords",
        "keywords": [
            "muba keywords",
            "important words for muba",
            "muba key concepts",
            "muba anahtar kelimeler",
            "muba önemli kavramlar",
            "muba关键词",
            "muba关键概念",
            "كلمات muba الأساسية",
            "muba मुख्य शब्द",
        ],
        "answers": {
            "en": "Core MUBA concepts include Character, Meme, Community, Culture, Chaos, Humor, Participation, Identity, Internet Culture, Ridiculous Energy, Timeline, Butterfly Effect, Same Meme. Different Universe., and We Live Here Now.",
            "tr": "MUBA'nın temel kavramları arasında Karakter, Meme, Topluluk, Kültür, Kaos, Mizah, Katılım, Kimlik, İnternet Kültürü, Absürt Enerji, Timeline, Kelebek Etkisi, Same Meme. Different Universe. ve We Live Here Now bulunur.",
            "zh": "MUBA 的核心概念包括角色、meme、社区、文化、混乱、幽默、参与、身份、互联网文化、荒诞能量、时间线、蝴蝶效应、Same Meme. Different Universe. 和 We Live Here Now。",
            "ar": "تشمل مفاهيم MUBA الأساسية: الشخصية، الميم، المجتمع، الثقافة، الفوضى، الفكاهة، المشاركة، الهوية، ثقافة الإنترنت، الطاقة العبثية، الخط الزمني، تأثير الفراشة، Same Meme. Different Universe. و We Live Here Now.",
            "hi": "MUBA के मुख्य कॉन्सेप्ट हैं: कैरेक्टर, मीम, कम्युनिटी, कल्चर, कैओस, ह्यूमर, पार्टिसिपेशन, आइडेंटिटी, इंटरनेट कल्चर, रिडिक्यूलस एनर्जी, टाइमलाइन, बटरफ्लाई इफेक्ट, Same Meme. Different Universe. और We Live Here Now।",
        },
    },
    {
        "id": 24,
        "topic": "core_messages",
        "keywords": [
            "muba core messages",
            "muba slogans",
            "muba phrases",
            "muba'nın sloganları",
            "muba ana mesajları",
            "muba口号",
            "muba核心信息",
            "شعارات muba",
            "رسائل muba",
            "muba के स्लोगन",
        ],
        "answers": {
            "en": "\"I'm MUBA.\" \"A character. A meme. A community.\" \"We're not going anywhere.\" \"We Live Here Now.\" \"Same Meme. Different Universe.\" \"No complicated plans.\" \"No fake promises.\" \"Memes. Chaos. Community.\" \"You have a place here.\" \"MUBA stays MUBA.\"",
            "tr": "\"I'm MUBA.\" \"Bir karakter. Bir meme. Bir topluluk.\" \"We're not going anywhere.\" \"We Live Here Now.\" \"Same Meme. Different Universe.\" \"No complicated plans.\" \"No fake promises.\" \"Memes. Chaos. Community.\" \"You have a place here.\" \"MUBA stays MUBA.\"",
            "zh": "\"I'm MUBA.\" \"A character. A meme. A community.\" \"We're not going anywhere.\" \"We Live Here Now.\" \"Same Meme. Different Universe.\" \"No complicated plans.\" \"No fake promises.\" \"Memes. Chaos. Community.\" \"You have a place here.\" \"MUBA stays MUBA.\"",
            "ar": "\"I'm MUBA.\" \"A character. A meme. A community.\" \"We're not going anywhere.\" \"We Live Here Now.\" \"Same Meme. Different Universe.\" \"No complicated plans.\" \"No fake promises.\" \"Memes. Chaos. Community.\" \"You have a place here.\" \"MUBA stays MUBA.\"",
            "hi": "\"I'm MUBA.\" \"A character. A meme. A community.\" \"We're not going anywhere.\" \"We Live Here Now.\" \"Same Meme. Different Universe.\" \"No complicated plans.\" \"No fake promises.\" \"Memes. Chaos. Community.\" \"You have a place here.\" \"MUBA stays MUBA.\"",
        },
    },
    {
        "id": 25,
        "topic": "current_information",
        "keywords": [
            "muba current information",
            "muba ca",
            "muba contract address",
            "muba price",
            "muba market cap",
            "muba listing",
            "muba announcement",
            "muba güncel bilgi",
            "muba ca adresi",
            "muba sözleşme adresi",
            "muba fiyat",
            "muba market cap",
            "muba最新信息",
            "muba价格",
            "muba合约地址",
            "سعر muba",
            "عنوان عقد muba",
            "معلومات muba الحالية",
            "muba कीमत",
            "muba कॉन्ट्रैक्ट एड्रेस",
        ],
        "answers": {
            "en": "Current MUBA information can change and should be verified before being stated as fact. The official page currently states: CA coming soon. I should not invent a contract address, price, market cap, listing, or announcement.",
            "tr": "MUBA'nın güncel bilgileri değişebilir ve gerçek olarak aktarılmadan önce doğrulanmalıdır. Resmî sayfadaki mevcut durum: CA coming soon. Sözleşme adresi, fiyat, market cap, listeleme veya duyuru uydurmamalıyım.",
            "zh": "MUBA 的当前信息可能发生变化，在作为事实陈述前应先验证。官方页面当前状态为：CA coming soon。不能编造合约地址、价格、市值、上市信息或公告。",
            "ar": "قد تتغير المعلومات الحالية عن MUBA ويجب التحقق منها قبل عرضها كحقيقة. الحالة الحالية في الصفحة الرسمية: CA coming soon. لا ينبغي اختراع عنوان عقد أو سعر أو قيمة سوقية أو إدراج أو إعلان.",
            "hi": "MUBA की वर्तमान जानकारी बदल सकती है और तथ्य के रूप में बताने से पहले उसे सत्यापित करना चाहिए। आधिकारिक पेज की वर्तमान स्थिति: CA coming soon। मुझे कॉन्ट्रैक्ट एड्रेस, कीमत, मार्केट कैप, लिस्टिंग या घोषणा नहीं गढ़नी चाहिए।",
        },
    },
    {
        "id": 26,
        "topic": "master_summary",
        "keywords": [
            "tell me everything about muba",
            "muba full summary",
            "muba complete story",
            "muba master summary",
            "muba hakkında her şey",
            "muba tam özet",
            "muba komple anlat",
            "muba全部",
            "muba完整介绍",
            "كل شيء عن muba",
            "muba पूरी जानकारी",
        ],
        "answers": {
            "en": "MUBA is a character born from the chaos of the meme world that developed into content, interaction, community, and culture. It is a character, a meme, and a community. Its home is meme culture and the internet. WE LIVE HERE NOW. Flap × Robinhood × MUBA is described as part of a broader meme universe, while the butterfly effect represents possibility rather than a guarantee. The future is community-driven and not fully written. MUBA stays MUBA.",
            "tr": "MUBA, meme dünyasının kaosundan doğup içerik, etkileşim, topluluk ve kültüre dönüşen bir karakterdir. Bir karakter, bir meme ve bir topluluktur. Evi meme kültürü ve internettir. WE LIVE HERE NOW. Flap × Robinhood × MUBA daha geniş bir meme evreninin parçası olarak anlatılır; kelebek etkisi ise garanti değil, olasılığı temsil eder. Gelecek topluluk tarafından şekillenir ve tamamen yazılmış değildir. MUBA stays MUBA.",
            "zh": "MUBA 是一个从 meme 世界的混乱中诞生，并发展成内容、互动、社区和文化的角色。它是一个角色、一个 meme 和一个社区。它的家是 meme 文化和互联网。WE LIVE HERE NOW。Flap × Robinhood × MUBA 被描述为更大 meme 宇宙的一部分，而蝴蝶效应代表可能性而非保证。未来由社区共同塑造，并没有完全写好。MUBA stays MUBA。",
            "ar": "MUBA شخصية ولدت من فوضى عالم الميمات وتطورت إلى محتوى وتفاعل ومجتمع وثقافة. إنها شخصية وميم ومجتمع. موطنها ثقافة الميمات والإنترنت. WE LIVE HERE NOW. يوصف Flap × Robinhood × MUBA كجزء من عالم ميمات أوسع، بينما يمثل تأثير الفراشة إمكانية وليس ضماناً. المستقبل تشكله الجماعة ولم يُكتب بالكامل. MUBA stays MUBA.",
            "hi": "MUBA मीम की दुनिया की अराजकता से पैदा हुआ कैरेक्टर है जो कंटेंट, इंटरैक्शन, कम्युनिटी और कल्चर में विकसित हुआ। यह एक कैरेक्टर, एक मीम और एक कम्युनिटी है। इसका घर मीम कल्चर और इंटरनेट है। WE LIVE HERE NOW। Flap × Robinhood × MUBA को बड़े मीम यूनिवर्स का हिस्सा बताया जाता है, जबकि बटरफ्लाई इफेक्ट संभावना को दर्शाता है, गारंटी को नहीं। भविष्य कम्युनिटी द्वारा आकार लिया जाता है और पूरी तरह लिखा नहीं गया है। MUBA stays MUBA।",
        },
    },
]


# ============================================================
# SOCIAL LANGUAGE DETECTION
# ============================================================

SOCIAL_INTENTS = {
    "greeting": {
        "en": [
            "hi", "hii", "hiii", "hello", "helloo", "hey", "heyy",
            "heyyy", "yo", "yoo", "hiya", "sup", "wassup",
        ],
        "tr": [
            "selam", "slm", "selaam", "selamm", "merhaba", "mrb",
            "mrb", "sa", "selamlar", "salam", "slm muba",
        ],
        "zh": [
            "你好", "嗨", "哈喽", "您好", "早", "大家好",
        ],
        "ar": [
            "مرحبا", "أهلا", "اهلا", "سلام", "هلا", "هلو",
        ],
        "hi": [
            "नमस्ते", "नमस्कार", "हाय", "हैलो", "हेलो", "नमस्ते जी",
        ],
    },
    "gm": {
        "en": [
            "gm", "gm gm", "good morning", "morning", "mornin",
            "goodmorning", "gmm", "gmmm",
        ],
        "tr": [
            "günaydın", "gunaydin", "günaydin", "gnyd", "gnydn",
        ],
        "zh": [
            "早上好", "早安", "早",
        ],
        "ar": [
            "صباح الخير", "صباحو", "صباح",
        ],
        "hi": [
            "सुप्रभात", "शुभ प्रभात", "गुड मॉर्निंग",
        ],
    },
    "gn": {
        "en": [
            "gn", "gn gn", "good night", "night", "goodnight",
            "gnt", "gnnn",
        ],
        "tr": [
            "iyi geceler", "iyigeceler", "ig", "geceler",
        ],
        "zh": [
            "晚安", "晚上好",
        ],
        "ar": [
            "تصبح على خير", "تصبحوا على خير", "ليلة سعيدة", "تصبحون على خير",
        ],
        "hi": [
            "शुभ रात्रि", "गुड नाइट", "शुभ रात्री",
        ],
    },
    "checkin": {
        "en": [
            "how are you", "how r u", "how are u", "hru", "how're you",
            "what's up", "whats up", "whatsup", "wassup", "what are you up to",
            "you good", "u good", "how you doing", "how ya doing",
        ],
        "tr": [
            "nasılsın", "nasilsin", "naber", "ne haber", "napıyorsun",
            "napiyosun", "ne yapıyorsun", "iyi misin", "nasıl gidiyor",
            "nasil gidiyor", "ne alem", "naber muba",
        ],
        "zh": [
            "你好吗", "怎么样", "最近怎么样", "在干嘛", "你还好吗",
        ],
        "ar": [
            "كيف حالك", "كيفك", "ما الأخبار", "شو الأخبار", "ماذا تفعل",
        ],
        "hi": [
            "कैसे हो", "कैसा चल रहा है", "क्या कर रहे हो", "आप कैसे हैं",
        ],
    },
    "direct_address": {
        "en": [
            "hey muba", "hi muba", "hello muba", "yo muba",
            "muba hey", "muba hi", "muba you there", "muba are you there",
            "muba awake", "muba wake up",
        ],
        "tr": [
            "hey muba", "selam muba", "muba selam", "muba orada mısın",
            "muba uyuyor musun", "muba burda mısın", "muba buradasın",
        ],
        "zh": [
            "你好muba", "muba你好", "muba在吗", "muba你在吗",
        ],
        "ar": [
            "مرحبا muba", "muba مرحبا", "muba هل أنت هنا", "muba أين أنت",
        ],
        "hi": [
            "हाय muba", "muba हाय", "muba तुम यहां हो", "muba कहाँ हो",
        ],
    },
    "casual_reaction": {
        "en": [
            "lol", "lmao", "lmfao", "haha", "hahaha", "rofl", "bruh",
            "bro", "nice", "based", "wild", "crazy", "damn", "wow",
            "wtf", "what", "okay", "ok", "cool", "fr", "real",
        ],
        "tr": [
            "lol", "haha", "hahaha", "ahah", "kanka", "bro", "oha",
            "vay", "iyi", "güzel", "harbi", "aynen", "lan", "la",
        ],
        "zh": [
            "哈哈", "哈哈哈", "笑死", "牛", "绝了", "好",
        ],
        "ar": [
            "هههه", "ههههه", "لول", "واو", "جميل", "قوي",
        ],
        "hi": [
            "हाहा", "हाहाहा", "lol", "वाह", "अच्छा", "भाई",
        ],
    },
}


SOCIAL_RESPONSES = {
    "greeting": {
        "en": [
            "Hey. 🪶",
            "Hey there. MUBA is here. 🪶",
            "Hello. We live here now. 🪶",
            "Yo. MUBA has entered the timeline. 🪶",
            "Hey. Still here. Still MUBA. 🪶",
        ],
        "tr": [
            "Selam. 🪶",
            "Selam. MUBA burada. 🪶",
            "Hey. Buradayız. 🪶",
            "Selam. We Live Here Now. 🪶",
            "Selam. Hâlâ MUBA. 🪶",
        ],
        "zh": [
            "你好。MUBA 在这里。🪶",
            "嗨。We Live Here Now. 🪶",
            "你好。还是 MUBA。🪶",
            "嗨，MUBA 在时间线上。🪶",
        ],
        "ar": [
            "مرحباً. MUBA هنا. 🪶",
            "أهلاً. نحن هنا الآن. 🪶",
            "مرحباً. ما زالت MUBA. 🪶",
            "هلا. MUBA موجودة. 🪶",
        ],
        "hi": [
            "नमस्ते। MUBA यहां है। 🪶",
            "हाय। We Live Here Now. 🪶",
            "नमस्ते। अभी भी MUBA। 🪶",
            "हाय। MUBA टाइमलाइन पर है। 🪶",
        ],
    },
    "gm": {
        "en": [
            "GM 🪶",
            "GM. We live here now. 🪶",
            "GM. MUBA is awake. 🪶",
            "GM. Keep the memes alive. 🪶",
            "GM. Still here. Still MUBA. 🪶",
        ],
        "tr": [
            "Günaydın. 🪶",
            "Günaydın. MUBA uyandı. 🪶",
            "Günaydın. Buradayız. 🪶",
            "Günaydın. Memeler yaşasın. 🪶",
            "Günaydın. Hâlâ MUBA. 🪶",
        ],
        "zh": [
            "早上好。🪶",
            "早。MUBA 醒了。🪶",
            "早。We Live Here Now. 🪶",
            "早。让 memes 继续活着。🪶",
        ],
        "ar": [
            "صباح الخير. 🪶",
            "صباح الخير. MUBA استيقظت. 🪶",
            "صباح الخير. نحن هنا الآن. 🪶",
            "صباح الخير. دعوا الميمات تعيش. 🪶",
        ],
        "hi": [
            "सुप्रभात। 🪶",
            "सुप्रभात। MUBA जाग गया। 🪶",
            "सुप्रभात। We Live Here Now. 🪶",
            "सुप्रभात। मीम्स को जिंदा रखो। 🪶",
        ],
    },
    "gn": {
        "en": [
            "GN 🪶",
            "GN. Keep the memes alive. 🪶",
            "GN. MUBA is logging off-ish. 🪶",
            "GN. Still here tomorrow. 🪶",
            "GN. We live here now. 🪶",
        ],
        "tr": [
            "İyi geceler. 🪶",
            "İyi geceler. Memeler yaşasın. 🪶",
            "İyi geceler. MUBA kapanıyor... gibi. 🪶",
            "İyi geceler. Yarın yine buradayız. 🪶",
            "İyi geceler. We Live Here Now. 🪶",
        ],
        "zh": [
            "晚安。🪶",
            "晚安。让 memes 继续活着。🪶",
            "晚安。MUBA 暂时下线。🪶",
            "晚安。明天还在这里。🪶",
        ],
        "ar": [
            "تصبحون على خير. 🪶",
            "ليلة سعيدة. دعوا الميمات تعيش. 🪶",
            "تصبحون على خير. MUBA في وضع السكون. 🪶",
            "ليلة سعيدة. سنكون هنا غداً. 🪶",
        ],
        "hi": [
            "शुभ रात्रि। 🪶",
            "शुभ रात्रि। मीम्स को जिंदा रखो। 🪶",
            "गुड नाइट। MUBA अब थोड़ा ऑफलाइन है। 🪶",
            "शुभ रात्रि। कल फिर यहीं मिलेंगे। 🪶",
        ],
    },
    "checkin": {
        "en": [
            "Alive. Memes are alive too. 🪶",
            "Still here. Still weird. Perfect. 🪶",
            "Not much. Just living here. 🪶",
            "MUBA is good. The timeline is doing timeline things. 🪶",
            "Still MUBA. That's a good sign. 🪶",
        ],
        "tr": [
            "Canlıyım. Memeler de canlı. 🪶",
            "Hâlâ buradayım. Hâlâ garibim. Mükemmel. 🪶",
            "Pek bir şey yok. Sadece burada yaşıyorum. 🪶",
            "MUBA iyi. Timeline yine kendi işini yapıyor. 🪶",
            "Hâlâ MUBA. Bu iyiye işaret. 🪶",
        ],
        "zh": [
            "还活着。memes 也还活着。🪶",
            "还在这里。还是很奇怪。完美。🪶",
            "没什么。只是继续住在这里。🪶",
            "MUBA 状态良好。时间线还是老样子。🪶",
        ],
        "ar": [
            "ما زلت حية. والميمات حية أيضاً. 🪶",
            "ما زلت هنا. وما زلت غريبة. مثالي. 🪶",
            "لا شيء كثير. فقط أعيش هنا. 🪶",
            "MUBA بخير. والخط الزمني يفعل أشياءه المعتادة. 🪶",
        ],
        "hi": [
            "जिंदा हूं। मीम्स भी जिंदा हैं। 🪶",
            "अभी भी यहीं हूं। अभी भी अजीब। परफेक्ट। 🪶",
            "कुछ खास नहीं। बस यहीं रह रहा हूं। 🪶",
            "MUBA ठीक है। टाइमलाइन अपना काम कर रही है। 🪶",
        ],
    },
    "direct_address": {
        "en": [
            "I'm here. 🪶",
            "MUBA never left. 🪶",
            "You called? MUBA is listening. 🪶",
            "Still here. What happened? 🪶",
            "Present. 🪶",
        ],
        "tr": [
            "Buradayım. 🪶",
            "MUBA hiç gitmedi. 🪶",
            "Seslendin? MUBA dinliyor. 🪶",
            "Hâlâ buradayım. Ne oldu? 🪶",
            "Buradayım. 🪶",
        ],
        "zh": [
            "我在。🪶",
            "MUBA 从没离开。🪶",
            "你叫我？MUBA 在听。🪶",
            "还在这里。怎么了？🪶",
        ],
        "ar": [
            "أنا هنا. 🪶",
            "MUBA لم تغادر أبداً. 🪶",
            "ناديتني؟ MUBA تستمع. 🪶",
            "ما زلت هنا. ماذا حدث؟ 🪶",
        ],
        "hi": [
            "मैं यहां हूं। 🪶",
            "MUBA कभी गया ही नहीं। 🪶",
            "बुलाया? MUBA सुन रहा है। 🪶",
            "अभी भी यहीं हूं। क्या हुआ? 🪶",
        ],
    },
    "casual_reaction": {
        "en": [
            "That's the spirit. 🪶",
            "Exactly. Memes happen. 🪶",
            "Now we're talking. 🪶",
            "Timeline energy. 🪶",
            "MUBA approves the chaos. 🪶",
            "Yeah. That's MUBA. 🪶",
        ],
        "tr": [
            "İşte ruh bu. 🪶",
            "Aynen. Memeler böyle doğuyor. 🪶",
            "Şimdi konuşuyoruz. 🪶",
            "Tam timeline enerjisi. 🪶",
            "MUBA bu kaosu onaylıyor. 🪶",
            "Aynen. MUBA bu. 🪶",
        ],
        "zh": [
            "就是这个感觉。🪶",
            "没错。meme 就是这样发生的。🪶",
            "现在开始有意思了。🪶",
            "时间线能量。🪶",
            "MUBA 批准这份混乱。🪶",
        ],
        "ar": [
            "هذه هي الروح. 🪶",
            "بالضبط. هكذا تولد الميمات. 🪶",
            "الآن بدأنا نتكلم. 🪶",
            "طاقة الخط الزمني. 🪶",
            "MUBA توافق على هذه الفوضى. 🪶",
        ],
        "hi": [
            "यही तो स्पिरिट है। 🪶",
            "बिल्कुल। मीम्स ऐसे ही बनते हैं। 🪶",
            "अब बात बन रही है। 🪶",
            "टाइमलाइन एनर्जी। 🪶",
            "MUBA इस कैओस को अप्रूव करता है। 🪶",
        ],
    },
}


# ============================================================
# INTERNAL STATE
# ============================================================

_last_social_reply: Dict[Tuple[int, Optional[int]], float] = {}
_last_social_text: Dict[Tuple[int, Optional[int]], str] = {}
_daily_social: Dict[Tuple[int, Optional[int]], float] = {}
_context: Dict[int, Deque[Tuple[str, str]]] = defaultdict(
    lambda: deque(maxlen=MAX_CONTEXT_ITEMS)
)


def _state_key(chat_id: int, user_id: Optional[int]) -> Tuple[int, Optional[int]]:
    """
    Prefer per-member state when user_id is supplied.
    Without user_id, state falls back to per-chat state.
    """
    return (int(chat_id or 0), user_id)


def _social_allowed(
    chat_id: int,
    user_id: Optional[int],
    now: Optional[float] = None,
) -> bool:
    current = now if now is not None else time.time()
    key = _state_key(chat_id, user_id)

    last = _last_social_reply.get(key, 0.0)

    if current - last < SOCIAL_COOLDOWN_SECONDS:
        return False

    day_mark = _daily_social.get(key, 0.0)

    if day_mark and current - day_mark < SOCIAL_DAILY_LIMIT_SECONDS:
        return False

    return True


def _record_social(
    chat_id: int,
    user_id: Optional[int],
    response: str,
    now: Optional[float] = None,
) -> None:
    current = now if now is not None else time.time()
    key = _state_key(chat_id, user_id)

    _last_social_reply[key] = current
    _daily_social[key] = current
    _last_social_text[key] = response


# ============================================================
# SOCIAL MATCHING
# ============================================================

def _strip_muba_name(text: str) -> str:
    value = normalize(text)
    value = re.sub(r"\bmub+a+\b", " ", value)
    value = re.sub(r"\bm\s*u\s*b\s*a\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _looks_like_repeated_letters(value: str, target: str) -> bool:
    if not value:
        return False

    collapsed = re.sub(r"(.)\1{2,}", r"\1", value)
    return similarity(collapsed, target) >= 0.78


def _social_phrase_score(text: str, phrase: str) -> float:
    value = normalize(text)
    target = normalize(phrase)

    if not value or not target:
        return 0.0

    if value == target:
        return 1.0

    if target in value:
        return 0.96

    collapsed_value = re.sub(r"(.)\1{1,}", r"\1", value)
    collapsed_target = re.sub(r"(.)\1{1,}", r"\1", target)

    if collapsed_target in collapsed_value:
        return 0.90

    ratio = similarity(collapsed_value, collapsed_target)

    if ratio >= 0.80:
        return ratio

    overlap = _token_overlap(value, target)

    return max(ratio, overlap)


def detect_social_intent(text: str, language: Optional[str] = None) -> Optional[str]:
    """
    Detect social intent before knowledge matching.

    Priority:
    1. GM/GN
    2. Direct MUBA address
    3. Check-in
    4. Greeting
    5. Casual reaction
    """
    value = normalize(text)

    if not value:
        return None

    language = language or detect_language(value)

    candidate_languages = [language]

    if language != "en":
        candidate_languages.append("en")

    best_intent: Optional[str] = None
    best_score = 0.0

    for intent in ("gm", "gn", "direct_address", "checkin", "greeting", "casual_reaction"):
        phrases: List[str] = []

        for lang in candidate_languages:
            phrases.extend(SOCIAL_INTENTS.get(intent, {}).get(lang, []))

        for phrase in phrases:
            score = _social_phrase_score(value, phrase)

            if intent == "direct_address" and not contains_muba(value):
                continue

            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score >= 0.82:
        return best_intent

    # Generic MUBA address with no clear phrase.
    if contains_muba(value):
        remainder = _strip_muba_name(value)

        if not remainder or remainder in {"hey", "hi", "hello", "yo", "selam", "slm"}:
            return "direct_address"

    return None


def is_social_message(text: str, language: Optional[str] = None) -> bool:
    return detect_social_intent(text, language) is not None


def social_reply(
    text: str,
    chat_id: int = 0,
    user_id: Optional[int] = None,
    language: Optional[str] = None,
) -> Optional[str]:
    """
    Return a varied social reply.

    In a group, passing user_id enables the intended per-member daily limit.
    If user_id is omitted, the limit falls back to chat-level state.
    """
    language = language or detect_language(text)
    intent = detect_social_intent(text, language)

    if not intent:
        return None

    if not _social_allowed(chat_id, user_id):
        return None

    options = list(
        SOCIAL_RESPONSES.get(intent, {}).get(language, [])
    )

    if not options:
        options = list(
            SOCIAL_RESPONSES.get(intent, {}).get("en", [])
        )

    if not options:
        return None

    key = _state_key(chat_id, user_id)
    previous = _last_social_text.get(key)

    if len(options) > 1 and previous in options:
        choices = [item for item in options if item != previous]
    else:
        choices = options

    response = random.choice(choices)

    _record_social(
        chat_id=chat_id,
        user_id=user_id,
        response=response,
    )

    return response


# ============================================================
# KNOWLEDGE MATCHING
# ============================================================

def match_knowledge(
    text: str,
    language: Optional[str] = None,
) -> Optional[Dict]:
    """Find the strongest MUBA knowledge item using exact, keyword and fuzzy matching."""
    value = normalize(text)

    if not value:
        return None

    best_item: Optional[Dict] = None
    best_score = 0.0

    for item in KNOWLEDGE:
        exact_score = _keyword_score(value, item["keywords"])

        token_scores = [
            _token_overlap(value, keyword)
            for keyword in item["keywords"]
        ]

        overlap_score = max(token_scores, default=0.0)

        score = max(
            exact_score,
            overlap_score * 0.88,
        )

        if score > best_score:
            best_score = score
            best_item = item

    if best_item is not None and best_score >= KEYWORD_THRESHOLD:
        return best_item

    # Fuzzy pass against every keyword for typo-heavy questions.
    fuzzy_best: Optional[Dict] = None
    fuzzy_score = 0.0

    for item in KNOWLEDGE:
        for keyword in item["keywords"]:
            ratio = similarity(value, keyword)

            if ratio > fuzzy_score:
                fuzzy_score = ratio
                fuzzy_best = item

            if _looks_like_repeated_letters(value, keyword):
                fuzzy_score = max(
                    fuzzy_score,
                    similarity(
                        re.sub(r"(.)\1{1,}", r"\1", value),
                        re.sub(r"(.)\1{1,}", r"\1", keyword),
                    ),
                )

    if fuzzy_best is not None and fuzzy_score >= FUZZY_THRESHOLD:
        return fuzzy_best

    return None


def _answer_for(item: Dict, language: str) -> str:
    answers = item.get("answers", {})

    return (
        answers.get(language)
        or answers.get("en")
        or "MUBA is MUBA. 🪶"
    )


# ============================================================
# FALLBACKS
# ============================================================

FALLBACKS = {
    "en": [
        "MUBA is still figuring that one out. No fake answers. 🪶",
        "That's outside the confirmed MUBA lore. We don't invent facts. 🪶",
        "Not in the known MUBA file yet. The story is still being written. 🪶",
        "MUBA doesn't make things up just to sound serious. 🪶",
    ],
    "tr": [
        "MUBA bunu henüz net olarak bilmiyor. Sahte cevap yok. 🪶",
        "Bu, doğrulanmış MUBA bilgisinin dışında. Gerçek uydurmuyoruz. 🪶",
        "Bu bilgi MUBA dosyasında henüz yok. Hikâye hâlâ yazılıyor. 🪶",
        "MUBA sırf ciddi görünmek için bir şeyler uydurmaz. 🪶",
    ],
    "zh": [
        "这个还不在已确认的 MUBA 信息里。我们不编造事实。🪶",
        "MUBA 目前没有确认这个答案。故事还在继续。🪶",
        "这超出了已知的 MUBA 设定。我们不为了听起来厉害而编造。🪶",
    ],
    "ar": [
        "هذا ليس ضمن معلومات MUBA المؤكدة بعد. نحن لا نختلق الحقائق. 🪶",
        "MUBA لا تملك إجابة مؤكدة لهذا حالياً. القصة ما زالت تتطور. 🪶",
        "هذا خارج المعلومات المعروفة عن MUBA. لا نختلق الأشياء. 🪶",
    ],
    "hi": [
        "यह अभी MUBA की पुष्टि की हुई जानकारी में नहीं है। हम तथ्य नहीं गढ़ते। 🪶",
        "MUBA के पास अभी इसका पक्का जवाब नहीं है। कहानी अभी बन रही है। 🪶",
        "यह ज्ञात MUBA जानकारी से बाहर है। सिर्फ अच्छा सुनाने के लिए कुछ नहीं गढ़ेंगे। 🪶",
    ],
}


def generic_fallback(
    text: str,
    language: Optional[str] = None,
) -> str:
    language = language or detect_language(text)
    return random.choice(
        FALLBACKS.get(language, FALLBACKS["en"])
    )


# ============================================================
# CONVERSATION CONTEXT
# ============================================================

def _remember(chat_id: int, user_text: str, response: str) -> None:
    if not chat_id:
        return

    _context[int(chat_id)].append(
        (user_text, response)
    )


def _context_topic(chat_id: int) -> Optional[str]:
    history = _context.get(int(chat_id or 0))

    if not history:
        return None

    last_user_message = history[-1][0]
    item = match_knowledge(last_user_message)

    return item["topic"] if item else None


# ============================================================
# REPLY BUILDER
# ============================================================

def build_reply(
    text: str,
    chat_id: int = 0,
    language: Optional[str] = None,
    user_id: Optional[int] = None,
) -> str:
    """
    Main local-brain entry point.

    Order:
    1. Detect language.
    2. Detect social intent.
    3. Match MUBA knowledge.
    4. Use context-aware fallback.
    """
    value = normalize(text)

    if not value:
        return ""

    language = language or detect_language(value)

    # Social layer gets priority over broad knowledge matching.
    social = social_reply(
        value,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
    )

    if social:
        _remember(chat_id, text, social)
        return social

    item = match_knowledge(value, language)

    if item:
        response = _answer_for(item, language)
        _remember(chat_id, text, response)
        return response

    # If a message clearly names MUBA but has no known intent,
    # use a MUBA-safe fallback instead of pretending certainty.
    response = generic_fallback(value, language)
    _remember(chat_id, text, response)
    return response


# ============================================================
# BRAIN UTILITIES
# ============================================================

def get_knowledge_topics() -> List[str]:
    return [item["topic"] for item in KNOWLEDGE]


def get_brain_stats() -> Dict[str, object]:
    knowledge_count = len(KNOWLEDGE)

    keyword_count = sum(
        len(item.get("keywords", []))
        for item in KNOWLEDGE
    )

    answer_count = sum(
        len(item.get("answers", {}))
        for item in KNOWLEDGE
    )

    social_phrase_count = sum(
        len(phrases)
        for intent in SOCIAL_INTENTS.values()
        for phrases in intent.values()
    )

    social_response_count = sum(
        len(responses)
        for intent in SOCIAL_RESPONSES.values()
        for responses in intent.values()
    )

    return {
        "languages": list(SUPPORTED_LANGUAGES),
        "knowledge_topics": knowledge_count,
        "knowledge_keywords": keyword_count,
        "localized_knowledge_answers": answer_count,
        "social_intents": len(SOCIAL_INTENTS),
        "social_trigger_phrases": social_phrase_count,
        "social_responses": social_response_count,
        "social_cooldown_seconds": SOCIAL_COOLDOWN_SECONDS,
        "social_daily_limit_seconds": SOCIAL_DAILY_LIMIT_SECONDS,
        "external_ai": False,
    }


def reset_chat_context(chat_id: int) -> None:
    _context.pop(int(chat_id or 0), None)


def reset_social_state(
    chat_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> None:
    if chat_id is None:
        _last_social_reply.clear()
        _last_social_text.clear()
        _daily_social.clear()
        return

    key = _state_key(chat_id, user_id)

    _last_social_reply.pop(key, None)
    _last_social_text.pop(key, None)
    _daily_social.pop(key, None)


# ============================================================
# LOCAL SELF-TEST
# ============================================================

if __name__ == "__main__":
    tests = [
        ("What is MUBA?", "en"),
        ("Who is MUBA?", "en"),
        ("MUBA'nın amacı nedir?", "tr"),
        ("MUBA 是怎么诞生的？", "zh"),
        ("ما هو هدف مجتمع MUBA؟", "ar"),
        ("MUBA का भविष्य क्या है?", "hi"),
        ("GM", "en"),
        ("GN", "en"),
        ("How are you?", "en"),
        ("Hey MUBA, what's up?", "en"),
        ("MUBA lol", "en"),
    ]

    print("MUBA Brain self-test")
    print("-" * 60)

    for query, expected_language in tests:
        detected = detect_language(query)
        result = build_reply(
            query,
            chat_id=999,
            user_id=1,
            language=detected,
        )
        print(f"Q: {query}")
        print(f"Language: {detected} (expected: {expected_language})")
        print(f"A: {result}")
        print()

    print("Brain stats:")
    print(get_brain_stats())
