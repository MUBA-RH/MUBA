"""
MUBA Local Brain
Offline knowledge, intent matching, multilingual replies, social behavior,
and conversation handling.

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
        "words": {
            "nedir", "kim", "kimdir", "nasıl", "neden", "ne", "hangi", "ekip",
            "topluluk", "hikaye", "gelecek", "amaç", "felsefe", "karakter",
            "meme", "farklı", "özellik", "kültür", "nereden", "çıktı",
            "selam", "nasılsın", "naber", "günaydın", "iyi", "gece",
        },
        "chars": set("çğıöşü"),
    },
    "en": {
        "words": {
            "what", "who", "how", "why", "where", "when", "team", "community",
            "story", "future", "purpose", "philosophy", "character", "meme",
            "different", "culture", "origin", "hello", "hey", "morning", "night",
        },
        "chars": set(),
    },
    "zh": {
        "words": {"什么", "是谁", "为什么", "怎么样", "社区", "故事", "未来", "团队",
                  "角色", "表情包", "文化", "起源", "你好", "早上好", "晚安"},
        "chars": set(),
    },
    "ar": {
        "words": {"ما", "من", "لماذا", "كيف", "أين", "فريق", "مجتمع", "قصة",
                  "مستقبل", "شخصية", "ميم", "ثقافة", "أصل", "مرحبا", "صباح", "ليل"},
        "chars": set(),
    },
    "hi": {
        "words": {"क्या", "कौन", "क्यों", "कैसे", "कहां", "टीम", "समुदाय", "कहानी",
                  "भविष्य", "चरित्र", "मीम", "संस्कृति", "शुरुआत", "नमस्ते", "सुबह", "रात"},
        "chars": set(),
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
    value = unicodedata.normalize("NFKC", text or "").lower()
    value = value.replace("ı", "i")
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", value)
    value = re.sub(r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", value))
    value = re.sub(r"[@#$%&*_+=~`|<>[\]{}()]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def tokens(text: str) -> List[str]:
    return re.findall(
        r"[a-z0-9çğıöşü]+|[\u3400-\u9fff]|[\u0600-\u06ff]+|[\u0900-\u097f]+",
        normalize(text),
    )


def detect_language(text: str) -> str:
    value = normalize(text)

    if any("\u4e00" <= ch <= "\u9fff" for ch in value):
        return "zh"
    if any("\u0600" <= ch <= "\u06ff" for ch in value):
        return "ar"
    if any("\u0900" <= ch <= "\u097f" for ch in value):
        return "hi"

    scores = {language: 0 for language in SUPPORTED_LANGUAGES}
    for language, data in LANGUAGE_HINTS.items():
        scores[language] += sum(
            1 for word in data["words"] if word in value
        )
        scores[language] += sum(
            1 for ch in data["chars"] if ch in value
        )

    if scores["tr"] > scores["en"]:
        return "tr"
    return "en"


def contains_muba(text: str) -> bool:
    value = normalize(text)
    if re.search(r"\bmub+a+\b", value):
        return True
    compact = re.sub(r"[^a-z]", "", value)
    if "muba" in compact:
        return True
    return bool(re.search(r"\bm\s*u\s*b\s*a\b", value))


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def _clean_for_match(text: str) -> str:
    value = normalize(text)
    for language_words in STOP_WORDS.values():
        for word in language_words:
            value = re.sub(rf"\b{re.escape(word)}\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


# ---------------------------------------------------------------------------
# Multilingual core knowledge
# ---------------------------------------------------------------------------

KNOWLEDGE: List[Dict] = [
    {
        "id": 1,
        "topic": "what_is_muba",
        "keywords": [
            "what is muba", "what's muba", "define muba", "muba nedir",
            "muba ne", "muba kim", "muba是什么", "什么是muba", "ما هو muba", "muba क्या है",
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
            "muba origin", "how did muba start", "where did muba come from",
            "muba nasıl çıktı", "muba nasıl ortaya çıktı", "muba nereden çıktı",
            "muba起源", "muba怎么诞生", "من أين جاءت muba", "muba कैसे शुरू हुआ",
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
            "who is muba", "muba kimdir", "muba karakteri kim", "who exactly is muba",
            "muba是谁", "谁是muba", "من هي muba", "muba कौन है",
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
            "muba character", "character traits", "what does muba look like",
            "muba appearance", "muba karakter özellikleri", "muba görünüşü",
            "muba长什么样", "muba شخصية", "muba कैरेक्टर",
        ],
        "answers": {
            "en": "MUBA is cute, absurd, unique, humorous, natural, meme-native, confident, and recognizable. The visual identity includes large expressive eyes, short dense fur, a pink tongue, a black MUBA hat, and a black hoodie marked $MUBA.",
            "tr": "MUBA sevimli, absürt, özgün, komik, doğal, meme kültürüne ait, özgüvenli ve tanınabilir. Görsel kimliğinde büyük ifadeli gözler, kısa yoğun tüyler, pembe dil, siyah MUBA şapkası ve üzerinde $MUBA bulunan siyah hoodie vardır.",
            "zh": "MUBA 可爱、荒诞、独特、幽默、自然、原生于 meme 文化、自信且容易辨认。视觉身份包括大而有表现力的眼睛、短而浓密的毛发、粉色舌头、黑色 MUBA 帽子和印有 $MUBA 的黑色连帽衫。",
            "ar": "MUBA لطيفة وعبثية وفريدة ومرحة وطبيعية وتنتمي لثقافة الميمات وواثقة وسهلة التعرف. هويتها البصرية تشمل عيوناً كبيرة معبرة، فروًا قصيراً كثيفاً، لساناً وردياً، قبعة MUBA سوداء وكنزة سوداء تحمل $MUBA.",
            "hi": "MUBA प्यारा, अजीब, यूनिक, मज़ेदार, नेचुरल, मीम कल्चर का हिस्सा, कॉन्फिडेंट और पहचानने योग्य है। इसकी विज़ुअल आइडेंटिटी में बड़ी एक्सप्रेसिव आँखें, घने फर, गुलाबी जीभ, काली MUBA हैट और $MUBA वाली काली हुडी शामिल है।",
        },
    },
    {
        "id": 5,
        "topic": "core_definition",
        "keywords": [
            "core definition", "muba identity", "muba özü", "muba tanımı",
            "muba是什么定义", "تعريف muba", "muba परिभाषा",
        ],
        "answers": {
            "en": "I'm MUBA. A character. A meme. A community. That's the core.",
            "tr": "Ben MUBA'yım. Bir karakter. Bir meme. Bir topluluk. Özünde bu var.",
            "zh": "我是 MUBA。一个角色、一个 meme、一个社区。这就是核心。",
            "ar": "أنا MUBA. شخصية، ميم، ومجتمع. هذه هي الفكرة الأساسية.",
            "hi": "मैं MUBA हूँ। एक कैरेक्टर, एक मीम, एक कम्युनिटी। यही मूल पहचान है।",
        },
    },
    {
        "id": 6,
        "topic": "purpose",
        "keywords": [
            "muba purpose", "purpose of muba", "muba goal", "what is muba for",
            "muba amacı", "muba amacı ne", "muba'nın amacı", "muba目标", "ما هدف muba", "muba का उद्देश्य",
        ],
        "answers": {
            "en": "MUBA exists to build a lasting cultural and community atmosphere around the character. People can talk, create memes, share ideas, participate, and help shape the story.",
            "tr": "MUBA'nın amacı karakter etrafında kalıcı bir kültür ve topluluk atmosferi oluşturmaktır. İnsanlar konuşabilir, meme üretebilir, fikir paylaşabilir, katılabilir ve hikâyenin şekillenmesine katkı verebilir.",
            "zh": "MUBA 的目标是围绕角色建立持久的文化和社区氛围。人们可以交流、制作 meme、分享想法、参与其中，并共同塑造故事。",
            "ar": "تهدف MUBA إلى بناء أجواء ثقافية ومجتمعية مستمرة حول الشخصية. يمكن للناس التحدث وصنع الميمات ومشاركة الأفكار والمشاركة والمساهمة في تشكيل القصة.",
            "hi": "MUBA का उद्देश्य कैरेक्टर के आसपास एक टिकाऊ कल्चरल और कम्युनिटी माहौल बनाना है। लोग बात कर सकते हैं, मीम बना सकते हैं, आइडिया शेयर कर सकते हैं और कहानी को आकार देने में हिस्सा ले सकते हैं।",
        },
    },
    {
        "id": 7,
        "topic": "growth",
        "keywords": [
            "muba growth", "how will muba grow", "muba büyüme", "muba nasıl büyür",
            "muba增长", "muba कैसे बढ़ेगा", "كيف تنمو muba",
        ],
        "answers": {
            "en": "MUBA focuses on strengthening identity, being discovered naturally, and making people feel part of the community. The idea is real interest, curiosity, conversation, and participation rather than empty hype.",
            "tr": "MUBA kimliğini güçlendirmeye, doğal biçimde keşfedilmeye ve insanların topluluğun parçası hissetmesine odaklanır. Boş hype yerine gerçek ilgi, merak, sohbet ve katılım önemlidir.",
            "zh": "MUBA 更重视强化身份、自然地被发现，以及让人们感到自己属于社区。重点是真实兴趣、好奇心、交流和参与，而不是空洞的炒作。",
            "ar": "تركز MUBA على تقوية هويتها واكتشافها بشكل طبيعي وجعل الناس يشعرون بأنهم جزء من المجتمع. الأهم هو الاهتمام الحقيقي والفضول والحوار والمشاركة، وليس الضجيج الفارغ.",
            "hi": "MUBA अपनी पहचान मजबूत करने, नेचुरल तरीके से खोजे जाने और लोगों को कम्युनिटी का हिस्सा महसूस कराने पर ध्यान देता है। खाली हाइप के बजाय असली रुचि, जिज्ञासा, बातचीत और भागीदारी महत्वपूर्ण हैं।",
        },
    },
    {
        "id": 8,
        "topic": "community",
        "keywords": [
            "muba community", "muba topluluk", "muba topluluğu", "community of muba",
            "muba社区", "muba مجتمع", "muba समुदाय",
        ],
        "answers": {
            "en": "MUBA's community is built around humor, meme culture, interaction, visuals, ideas, and participation. People are not only watching from the outside. You have a place here.",
            "tr": "MUBA topluluğu mizah, meme kültürü, etkileşim, görseller, fikirler ve katılım üzerine kurulur. İnsanlar sadece dışarıdan izleyen kişiler değildir. Burada senin de yerin var.",
            "zh": "MUBA 社区建立在幽默、meme 文化、互动、视觉内容、想法和参与之上。人们不只是旁观者。这里有你的位置。",
            "ar": "مجتمع MUBA قائم على الفكاهة وثقافة الميمات والتفاعل والصور والأفكار والمشاركة. الناس ليسوا مجرد متفرجين. لك مكان هنا.",
            "hi": "MUBA कम्युनिटी ह्यूमर, मीम कल्चर, इंटरैक्शन, विज़ुअल्स, आइडिया और भागीदारी पर बनी है। लोग सिर्फ बाहर से देखने वाले नहीं हैं। यहाँ आपकी भी जगह है।",
        },
    },
    {
        "id": 9,
        "topic": "meme_world",
        "keywords": [
            "muba meme world", "where does muba live", "muba meme world", "meme dünyası",
            "muba nerede yaşıyor", "muba在哪", "muba在哪里", "أين تعيش muba", "muba कहाँ रहता है",
        ],
        "answers": {
            "en": "The meme world and internet culture are MUBA's natural home. That's why the line is simple: WE LIVE HERE NOW.",
            "tr": "Meme dünyası ve internet kültürü MUBA'nın doğal evidir. Bu yüzden mesaj basit: WE LIVE HERE NOW.",
            "zh": "meme 世界和互联网文化是 MUBA 自然的家。所以这句话很简单：WE LIVE HERE NOW。",
            "ar": "عالم الميمات وثقافة الإنترنت هما موطن MUBA الطبيعي. لذلك الرسالة بسيطة: WE LIVE HERE NOW.",
            "hi": "मीम की दुनिया और इंटरनेट कल्चर MUBA का नेचुरल घर हैं। इसलिए संदेश सीधा है: WE LIVE HERE NOW.",
        },
    },
    {
        "id": 10,
        "topic": "we_live_here_now",
        "keywords": [
            "we live here now", "meaning of we live here now", "what does we live here now mean",
            "we live here now ne demek", "bu söz ne anlama geliyor", "we live here now什么意思",
            "ماذا تعني we live here now", "we live here now का मतलब",
        ],
        "answers": {
            "en": "WE LIVE HERE NOW means MUBA is already here: in the meme world, internet culture, and the community. MUBA is not trying to become another identity or leave. We're not going anywhere.",
            "tr": "WE LIVE HERE NOW, MUBA'nın zaten burada olduğunu anlatır: meme dünyasında, internet kültüründe ve topluluğuyla birlikte. Başka bir kimliğe dönüşmeye ya da buradan gitmeye çalışmıyoruz. Bir yere gitmiyoruz.",
            "zh": "WE LIVE HERE NOW 表示 MUBA 已经在这里：在 meme 世界、互联网文化和社区中。MUBA 不想变成另一种身份，也不会离开。我们不会走。",
            "ar": "WE LIVE HERE NOW تعني أن MUBA موجودة هنا بالفعل: في عالم الميمات وثقافة الإنترنت ومع المجتمع. لا نحاول التحول إلى هوية أخرى أو الرحيل. لن نذهب إلى أي مكان.",
            "hi": "WE LIVE HERE NOW का मतलब है कि MUBA पहले से यहीं है: मीम की दुनिया, इंटरनेट कल्चर और कम्युनिटी में। MUBA किसी और पहचान में बदलने या यहाँ से जाने की कोशिश नहीं करता। हम कहीं नहीं जा रहे।",
        },
    },
    {
        "id": 11,
        "topic": "robinhood_flap",
        "keywords": [
            "robinhood flap muba", "flap robinhood muba", "muba robinhood", "muba flap",
            "same meme different universe", "aynı meme farklı evren", "muba蝴蝶", "muba robinhood flap",
        ],
        "answers": {
            "en": "The Robinhood × Flap × MUBA concept places MUBA in a broader meme universe. The phrase is: Same Meme. Different Universe. It should not be presented as a legal, commercial, listing, ownership, or investment relationship unless independently verified.",
            "tr": "Robinhood × Flap × MUBA konsepti MUBA'yı daha geniş bir meme evreni içinde konumlandırır. Mesaj: Same Meme. Different Universe. Bu, bağımsız olarak doğrulanmadıkça hukuki, ticari, listeleme, sahiplik veya yatırım ilişkisi olarak sunulmamalıdır.",
            "zh": "Robinhood × Flap × MUBA 的概念把 MUBA 放进更大的 meme 宇宙。核心句是：Same Meme. Different Universe. 除非经过独立验证，不应把它描述为法律、商业、上市、所有权或投资关系。",
            "ar": "مفهوم Robinhood × Flap × MUBA يضع MUBA ضمن عالم ميمات أوسع. العبارة هي: Same Meme. Different Universe. ولا ينبغي وصف ذلك كعلاقة قانونية أو تجارية أو إدراج أو ملكية أو استثمار دون تحقق مستقل.",
            "hi": "Robinhood × Flap × MUBA कॉन्सेप्ट MUBA को एक बड़े मीम यूनिवर्स में रखता है। संदेश है: Same Meme. Different Universe. स्वतंत्र सत्यापन के बिना इसे कानूनी, व्यावसायिक, लिस्टिंग, स्वामित्व या निवेश संबंध न बताया जाए।",
        },
    },
    {
        "id": 12,
        "topic": "butterfly_effect",
        "keywords": [
            "butterfly effect", "muba butterfly", "kelebek etkisi", "muba kelebek",
            "蝴蝶效应 muba", "تأثير الفراشة muba", "muba तितली प्रभाव",
        ],
        "answers": {
            "en": "The butterfly effect represents the idea that a small flap or movement can create a larger effect. For MUBA, it is a symbol of possibility, not a guarantee.",
            "tr": "Kelebek etkisi, küçük bir kanat çırpışının veya hareketin daha büyük bir etki yaratabileceği fikrini temsil eder. MUBA için bu bir olasılık sembolüdür, garanti değildir.",
            "zh": "蝴蝶效应代表一个小小的动作可能产生更大的影响。对 MUBA 来说，它象征的是可能性，而不是保证。",
            "ar": "تأثير الفراشة يمثل فكرة أن حركة صغيرة قد تُحدث أثراً أكبر. بالنسبة إلى MUBA فهو رمز للإمكانية وليس ضماناً.",
            "hi": "बटरफ्लाई इफेक्ट इस विचार को दर्शाता है कि एक छोटी-सी हलचल बड़ा असर पैदा कर सकती है। MUBA के लिए यह संभावना का प्रतीक है, गारंटी नहीं।",
        },
    },
    {
        "id": 13,
        "topic": "goals",
        "keywords": [
            "muba goals", "goals of muba", "muba hedefleri", "muba hedefi",
            "muba目标", "أهداف muba", "muba के लक्ष्य",
        ],
        "answers": {
            "en": "The core goals are a recognizable character, a strong active community, an own culture, and a lasting place for MUBA in internet culture.",
            "tr": "Temel hedefler; tanınabilir bir karakter, güçlü ve aktif bir topluluk, kendine ait bir kültür ve MUBA'nın internet kültüründe kalıcı bir yer edinmesidir.",
            "zh": "核心目标是打造容易辨认的角色、强大活跃的社区、属于自己的文化，并让 MUBA 在互联网文化中留下长期的位置。",
            "ar": "الأهداف الأساسية هي شخصية مميزة، مجتمع قوي ونشط، ثقافة خاصة، ومكان دائم لـ MUBA في ثقافة الإنترنت.",
            "hi": "मुख्य लक्ष्य हैं एक पहचानने योग्य कैरेक्टर, मजबूत एक्टिव कम्युनिटी, अपनी संस्कृति और इंटरनेट कल्चर में MUBA की टिकाऊ जगह।",
        },
    },
    {
        "id": 14,
        "topic": "future",
        "keywords": [
            "muba future", "future of muba", "what happens to muba", "muba'nın geleceği",
            "muba gelecek", "muba未来", "muba مستقبل", "muba का भविष्य",
        ],
        "answers": {
            "en": "MUBA's future is not completely written. The community can shape future content, ideas, and cultural elements. Time will show where it goes. MUBA stays MUBA.",
            "tr": "MUBA'nın geleceği tamamen yazılmış değil. Topluluk gelecekteki içerikleri, fikirleri ve kültürel unsurları şekillendirebilir. Nereye gideceğini zaman gösterecek. MUBA stays MUBA.",
            "zh": "MUBA 的未来还没有完全写好。社区可以塑造未来的内容、想法和文化元素。时间会告诉我们它走向哪里。MUBA stays MUBA。",
            "ar": "مستقبل MUBA لم يُكتب بالكامل. يمكن للمجتمع تشكيل المحتوى والأفكار والعناصر الثقافية القادمة. الوقت سيُظهر إلى أين تتجه. MUBA stays MUBA.",
            "hi": "MUBA का भविष्य पूरी तरह पहले से तय नहीं है। कम्युनिटी भविष्य के कंटेंट, आइडिया और कल्चरल एलिमेंट्स को आकार दे सकती है। समय बताएगा यह कहाँ जाता है। MUBA stays MUBA.",
        },
    },
    {
        "id": 15,
        "topic": "difference",
        "keywords": [
            "why is muba different", "what makes muba different", "muba different",
            "muba neden farklı", "muba'yı farklı yapan", "muba有什么不同", "لماذا muba مختلفة", "muba अलग क्यों है",
        ],
        "answers": {
            "en": "MUBA is not built around a complicated product story or endless promises. Its strength is the combination of character and community: No complicated plans. No fake promises. Memes. Chaos. Community.",
            "tr": "MUBA karmaşık bir ürün hikâyesi veya bitmeyen vaatler üzerine kurulmaz. Gücü karakter ve topluluğun birleşimidir: Karmaşık planlar yok. Sahte vaatler yok. Memeler. Kaos. Topluluk.",
            "zh": "MUBA 不是围绕复杂的产品故事或无尽承诺建立的。它的力量来自角色与社区：没有复杂计划，没有虚假承诺。Meme、混乱、社区。",
            "ar": "MUBA لا تقوم على قصة منتج معقدة أو وعود لا تنتهي. قوتها في اجتماع الشخصية والمجتمع: لا خطط معقدة، لا وعود زائفة. ميمات، فوضى، مجتمع.",
            "hi": "MUBA किसी जटिल प्रोडक्ट स्टोरी या अंतहीन वादों पर आधारित नहीं है। इसकी ताकत कैरेक्टर और कम्युनिटी के मेल में है: कोई जटिल प्लान नहीं। कोई नकली वादा नहीं। मीम्स। कैओस। कम्युनिटी।",
        },
    },
    {
        "id": 16,
        "topic": "philosophy",
        "keywords": [
            "muba philosophy", "muba felsefesi", "muba'nın felsefesi", "muba理念",
            "فلسفة muba", "muba दर्शन",
        ],
        "answers": {
            "en": "MUBA's philosophy is simple: Be what you are. Grow with community. Do not make unnecessary promises. Create culture. Stay here.",
            "tr": "MUBA'nın felsefesi basit: Olduğun şey ol. Toplulukla büyü. Gereksiz vaatler verme. Kültür oluştur. Burada kal.",
            "zh": "MUBA 的理念很简单：做真实的自己。与社区一起成长。不要做不必要的承诺。创造文化。留在这里。",
            "ar": "فلسفة MUBA بسيطة: كن ما أنت عليه. انمُ مع المجتمع. لا تقدم وعوداً غير ضرورية. اصنع ثقافة. ابق هنا.",
            "hi": "MUBA की फिलॉसफी सरल है: जो हो वही रहो। कम्युनिटी के साथ बढ़ो। अनावश्यक वादे मत करो। संस्कृति बनाओ। यहीं रहो।",
        },
    },
    {
        "id": 17,
        "topic": "story",
        "keywords": [
            "muba story", "muba hikaye", "muba'nın hikayesi", "muba故事",
            "قصة muba", "muba कहानी",
        ],
        "answers": {
            "en": "MUBA's story develops through the community: people create content and memes, use the character, talk, share ideas, and contribute to the culture. The story develops together.",
            "tr": "MUBA'nın hikâyesi toplulukla gelişir: insanlar içerik ve meme üretir, karakteri kullanır, konuşur, fikir paylaşır ve kültüre katkıda bulunur. Hikâye birlikte gelişir.",
            "zh": "MUBA 的故事通过社区不断发展：人们制作内容和 meme、使用角色、交流想法并参与文化建设。故事是共同发展的。",
            "ar": "تتطور قصة MUBA عبر المجتمع: يصنع الناس المحتوى والميمات ويستخدمون الشخصية ويتحدثون ويتبادلون الأفكار ويساهمون في الثقافة. القصة تتطور معاً.",
            "hi": "MUBA की कहानी कम्युनिटी के साथ विकसित होती है: लोग कंटेंट और मीम बनाते हैं, कैरेक्टर का इस्तेमाल करते हैं, बात करते हैं और संस्कृति में योगदान देते हैं। कहानी साथ मिलकर बनती है।",
        },
    },
    {
        "id": 18,
        "topic": "possibilities",
        "keywords": [
            "muba possibilities", "could muba become", "muba legend", "muba ne olabilir",
            "muba可能", "ماذا يمكن أن تصبح muba", "muba क्या बन सकता है",
        ],
        "answers": {
            "en": "MUBA could become a legend, the weirdest character on the timeline, or simply remain a place where the community has a good laugh. These are possibilities, not promises.",
            "tr": "MUBA bir efsaneye, timeline'ın en tuhaf karakterine dönüşebilir ya da topluluğun birlikte eğlendiği bir yer olarak kalabilir. Bunlar olasılıktır, vaat değildir.",
            "zh": "MUBA 可能成为一个传奇、时间线里最奇怪的角色，也可能只是社区一起开心的地方。这些都是可能性，不是承诺。",
            "ar": "قد تصبح MUBA أسطورة أو أغرب شخصية على الخط الزمني، أو ببساطة تبقى مكاناً يستمتع فيه المجتمع. هذه احتمالات وليست وعوداً.",
            "hi": "MUBA एक लीजेंड बन सकता है, टाइमलाइन का सबसे अजीब कैरेक्टर बन सकता है, या बस ऐसी जगह रह सकता है जहाँ कम्युनिटी मज़े करे। ये संभावनाएँ हैं, वादे नहीं।",
        },
    },
    {
        "id": 19,
        "topic": "avoids",
        "keywords": [
            "what does muba avoid", "what muba avoids", "muba kaçınır", "muba neleri istemez",
            "muba避免", "ما الذي تتجنبه muba", "muba किन चीजों से बचता है",
        ],
        "answers": {
            "en": "MUBA avoids complicated plans, fake or endless promises, forced explanations, and borrowed identities.",
            "tr": "MUBA karmaşık planlardan, sahte veya bitmeyen vaatlerden, zoraki açıklamalardan ve ödünç alınmış kimliklerden uzak durur.",
            "zh": "MUBA 避免复杂计划、虚假或无尽承诺、强行解释，以及借来的身份。",
            "ar": "تتجنب MUBA الخطط المعقدة والوعود الزائفة أو التي لا تنتهي والتفسيرات القسرية والهويات المستعارة.",
            "hi": "MUBA जटिल प्लान, नकली या अंतहीन वादे, जबरन स्पष्टीकरण और उधार ली हुई पहचान से बचता है।",
        },
    },
    {
        "id": 20,
        "topic": "identity_boundaries",
        "keywords": [
            "official muba", "muba official", "muba identity boundaries", "muba resmi",
            "resmi muba", "muba官方", "muba الرسمية", "muba आधिकारिक",
        ],
        "answers": {
            "en": "Official MUBA information should be separated from community content. Rumors and opinions are not official facts, and future possibilities are not confirmed facts.",
            "tr": "Resmi MUBA bilgisi topluluk içeriğinden ayrılmalıdır. Söylentiler ve görüşler resmi gerçek değildir; geleceğe dair olasılıklar da doğrulanmış gerçekler değildir.",
            "zh": "官方 MUBA 信息应与社区内容区分。传闻和观点不是官方事实，未来可能性也不是已确认事实。",
            "ar": "يجب فصل المعلومات الرسمية عن محتوى المجتمع. الشائعات والآراء ليست حقائق رسمية، والاحتمالات المستقبلية ليست حقائق مؤكدة.",
            "hi": "आधिकारिक MUBA जानकारी को कम्युनिटी कंटेंट से अलग रखना चाहिए। अफवाहें और राय आधिकारिक तथ्य नहीं हैं, और भविष्य की संभावनाएँ भी पुष्ट तथ्य नहीं हैं।",
        },
    },
    {
        "id": 21,
        "topic": "one_sentence",
        "keywords": [
            "muba in one sentence", "one sentence muba", "tek cümlede muba", "muba tek cümle",
            "一句话 muba", "muba في جملة", "muba एक वाक्य में",
        ],
        "answers": {
            "en": "MUBA is a character that emerged from the chaos of the meme world, has its own identity, and became the center of a community building its own culture around it.",
            "tr": "MUBA, meme dünyasının kaosundan doğan, kendi kimliğine sahip olan ve etrafında kendi kültürünü oluşturan bir topluluğun merkezine dönüşen bir karakterdir.",
            "zh": "MUBA 是一个从 meme 世界的混乱中诞生、拥有独特身份，并逐渐成为一个围绕它建立自身文化的社区核心的角色。",
            "ar": "MUBA شخصية وُلدت من فوضى عالم الميمات، لها هويتها الخاصة، وأصبحت مركز مجتمع يبني ثقافته حولها.",
            "hi": "MUBA मीम की दुनिया की अराजकता से पैदा हुआ एक कैरेक्टर है, जिसकी अपनी पहचान है और जो अपनी संस्कृति बनाने वाली कम्युनिटी का केंद्र बन गया।",
        },
    },
    {
        "id": 22,
        "topic": "self_description",
        "keywords": [
            "describe muba", "muba describes itself", "muba kendini nasıl tanımlar",
            "muba kendini tanıt", "muba自我介绍", "كيف تصف muba نفسها", "muba अपना परिचय",
        ],
        "answers": {
            "en": "I'm MUBA. MUBA is MUBA.",
            "tr": "Ben MUBA'yım. MUBA, MUBA'dır.",
            "zh": "我是 MUBA。MUBA 就是 MUBA。",
            "ar": "أنا MUBA. MUBA هي MUBA.",
            "hi": "मैं MUBA हूँ। MUBA ही MUBA है।",
        },
    },
    {
        "id": 23,
        "topic": "keywords",
        "keywords": [
            "muba keywords", "muba key words", "muba anahtar kelimeler", "muba关键词",
            "كلمات muba", "muba कीवर्ड",
        ],
        "answers": {
            "en": "Core MUBA words include character, meme, community, culture, chaos, humor, participation, identity, internet culture, ridiculous energy, timeline, butterfly effect, Same Meme. Different Universe., and We Live Here Now.",
            "tr": "Temel MUBA kelimeleri: karakter, meme, topluluk, kültür, kaos, mizah, katılım, kimlik, internet kültürü, absürt enerji, timeline, kelebek etkisi, Same Meme. Different Universe. ve We Live Here Now.",
            "zh": "MUBA 的核心关键词包括角色、meme、社区、文化、混乱、幽默、参与、身份、互联网文化、荒诞能量、时间线、蝴蝶效应、Same Meme. Different Universe. 和 We Live Here Now。",
            "ar": "تشمل كلمات MUBA الأساسية: الشخصية، الميم، المجتمع، الثقافة، الفوضى، الفكاهة، المشاركة، الهوية، ثقافة الإنترنت، الطاقة العبثية، الخط الزمني، تأثير الفراشة، Same Meme. Different Universe. و We Live Here Now.",
            "hi": "MUBA के मुख्य कीवर्ड हैं: कैरेक्टर, मीम, कम्युनिटी, कल्चर, कैओस, ह्यूमर, पार्टिसिपेशन, आइडेंटिटी, इंटरनेट कल्चर, रिडिक्यूलस एनर्जी, टाइमलाइन, बटरफ्लाई इफेक्ट, Same Meme. Different Universe. और We Live Here Now.",
        },
    },
    {
        "id": 24,
        "topic": "core_messages",
        "keywords": [
            "muba slogans", "muba core messages", "muba slogan", "muba sloganları",
            "muba口号", "شعارات muba", "muba के स्लोगन",
        ],
        "answers": {
            "en": "MUBA's core messages are: I'm MUBA. A character. A meme. A community. We're not going anywhere. We Live Here Now. Same Meme. Different Universe. No complicated plans. No fake promises. Memes. Chaos. Community. You have a place here. MUBA stays MUBA.",
            "tr": "MUBA'nın temel mesajları: Ben MUBA'yım. Bir karakter. Bir meme. Bir topluluk. Bir yere gitmiyoruz. We Live Here Now. Same Meme. Different Universe. Karmaşık planlar yok. Sahte vaatler yok. Memeler. Kaos. Topluluk. Burada senin de yerin var. MUBA stays MUBA.",
            "zh": "MUBA 的核心信息是：我是 MUBA。一个角色、一个 meme、一个社区。我们不会离开。We Live Here Now。Same Meme. Different Universe。没有复杂计划，没有虚假承诺。Meme、混乱、社区。这里有你的位置。MUBA stays MUBA。",
            "ar": "رسائل MUBA الأساسية: أنا MUBA. شخصية، ميم، مجتمع. لن نذهب إلى أي مكان. We Live Here Now. Same Meme. Different Universe. لا خطط معقدة. لا وعود زائفة. ميمات، فوضى، مجتمع. لك مكان هنا. MUBA stays MUBA.",
            "hi": "MUBA के मुख्य संदेश हैं: मैं MUBA हूँ। एक कैरेक्टर, एक मीम, एक कम्युनिटी। हम कहीं नहीं जा रहे। We Live Here Now. Same Meme. Different Universe. कोई जटिल प्लान नहीं। कोई नकली वादा नहीं। मीम्स। कैओस। कम्युनिटी। यहाँ आपकी जगह है। MUBA stays MUBA.",
        },
    },
    {
        "id": 25,
        "topic": "current_info",
        "keywords": [
            "muba current info", "muba contract", "muba ca", "muba address",
            "muba listing", "muba price", "muba announcement", "muba güncel bilgi",
            "muba kontrat", "muba adres", "muba listeleme", "muba fiyat",
            "muba现在", "muba 合约", "muba 价格", "عنوان muba", "سعر muba",
        ],
        "answers": {
            "en": "Current MUBA information can change and must be verified before being stated as fact. The official page currently marks CA as “CA coming soon.” Do not invent a contract address, price, listing, partnership, or announcement.",
            "tr": "Güncel MUBA bilgileri değişebilir ve gerçek olarak paylaşılmadan önce doğrulanmalıdır. Resmi sayfada CA şu anda “CA coming soon.” olarak belirtiliyor. Kontrat adresi, fiyat, listeleme, ortaklık veya duyuru uydurma.",
            "zh": "MUBA 的当前信息可能变化，在作为事实陈述前必须验证。官方页面目前显示 CA 为“CA coming soon.”。不要编造合约地址、价格、上市、合作关系或公告。",
            "ar": "معلومات MUBA الحالية قد تتغير ويجب التحقق منها قبل عرضها كحقائق. الصفحة الرسمية تعرض حالياً CA على أنه “CA coming soon.”. لا تخترع عنوان عقد أو سعراً أو إدراجاً أو شراكة أو إعلاناً.",
            "hi": "MUBA की वर्तमान जानकारी बदल सकती है और तथ्य के रूप में बताने से पहले सत्यापित होनी चाहिए। आधिकारिक पेज पर CA अभी “CA coming soon.” है। कॉन्ट्रैक्ट एड्रेस, कीमत, लिस्टिंग, पार्टनरशिप या घोषणा न गढ़ें।",
        },
    },
    {
        "id": 26,
        "topic": "master_summary",
        "keywords": [
            "muba summary", "summarize muba", "muba overview", "muba özet", "muba genel",
            "muba总结", "ملخص muba", "muba सारांश",
        ],
        "answers": {
            "en": "MUBA is a character born from meme-world chaos that grew into content, interaction, community, and culture. It is a character, a meme, and a community. Its home is internet culture. WE LIVE HERE NOW. MUBA stays MUBA.",
            "tr": "MUBA, meme dünyasının kaosundan doğup içerik, etkileşim, topluluk ve kültüre dönüşen bir karakterdir. Bir karakter, bir meme ve bir topluluktur. Evi internet kültürüdür. WE LIVE HERE NOW. MUBA stays MUBA.",
            "zh": "MUBA 是一个从 meme 世界混乱中诞生，并发展为内容、互动、社区和文化的角色。它是一个角色、一个 meme 和一个社区。它的家是互联网文化。WE LIVE HERE NOW。MUBA stays MUBA。",
            "ar": "MUBA شخصية وُلدت من فوضى عالم الميمات وتطورت إلى محتوى وتفاعل ومجتمع وثقافة. هي شخصية وميم ومجتمع. موطنها ثقافة الإنترنت. WE LIVE HERE NOW. MUBA stays MUBA.",
            "hi": "MUBA मीम की दुनिया की अराजकता से पैदा हुआ कैरेक्टर है जो कंटेंट, इंटरैक्शन, कम्युनिटी और कल्चर में विकसित हुआ। यह एक कैरेक्टर, एक मीम और एक कम्युनिटी है। इसका घर इंटरनेट कल्चर है। WE LIVE HERE NOW. MUBA stays MUBA.",
        },
    },
]


# ---------------------------------------------------------------------------
# Social interaction layer
# ---------------------------------------------------------------------------

SOCIAL_INTENTS = {
    "gm": {
        "patterns": {
            "en": ["gm", "good morning", "morning muba", "morning"],
            "tr": ["günaydın", "gunaydin", "gm muba"],
            "zh": ["早安", "早上好", "早"],
            "ar": ["صباح الخير", "صباحو"],
            "hi": ["सुप्रभात", "शुभ प्रभात", "गुड मॉर्निंग"],
        },
        "replies": {
            "en": ["GM 🪶", "GM. MUBA is awake. 🪶", "GM. We live here now. 🪶"],
            "tr": ["GM 🪶", "GM. MUBA uyandı. 🪶", "Günaydın. Burada yaşıyoruz. 🪶"],
            "zh": ["GM 🪶", "GM。MUBA 醒了。🪶", "早。We live here now. 🪶"],
            "ar": ["GM 🪶", "GM. MUBA مستيقظة. 🪶", "صباح الخير. نحن هنا الآن. 🪶"],
            "hi": ["GM 🪶", "GM. MUBA जाग गया। 🪶", "सुप्रभात। We live here now. 🪶"],
        },
    },
    "gn": {
        "patterns": {
            "en": ["gn", "good night", "night muba"],
            "tr": ["iyi geceler", "gn muba"],
            "zh": ["晚安", "晚上好"],
            "ar": ["تصبح على خير", "ليلة سعيدة"],
            "hi": ["शुभ रात्रि", "गुड नाइट"],
        },
        "replies": {
            "en": ["GN 🪶", "GN. Keep the memes alive. 🪶", "GN. MUBA stays MUBA. 🪶"],
            "tr": ["GN 🪶", "GN. Memeleri canlı tut. 🪶", "GN. MUBA stays MUBA. 🪶"],
            "zh": ["GN 🪶", "晚安。让 memes 继续活着。🪶", "GN。MUBA stays MUBA. 🪶"],
            "ar": ["GN 🪶", "ليلة سعيدة. أبقِ الميمات حية. 🪶", "GN. MUBA stays MUBA. 🪶"],
            "hi": ["GN 🪶", "शुभ रात्रि। मीम्स को जिंदा रखो। 🪶", "GN. MUBA stays MUBA. 🪶"],
        },
    },
    "check_in": {
        "patterns": {
            "en": ["how are you", "how are you muba", "how's it going", "how is it going",
                   "what's up", "whats up", "what are you up to", "you good"],
            "tr": ["nasılsın", "nasilsin", "naber", "ne haber", "nasıl gidiyor", "ne yapıyorsun"],
            "zh": ["你好吗", "怎么样", "最近怎么样", "在干嘛", "你怎么样"],
            "ar": ["كيف حالك", "كيفك", "ما الأخبار", "ماذا تفعل"],
            "hi": ["कैसे हो", "क्या हाल है", "क्या चल रहा है", "क्या कर रहे हो"],
        },
        "replies": {
            "en": ["Still here. Still weird. Perfect. 🪶", "Alive. Memes are alive too. 🪶",
                   "Not much. Just living here. 🪶", "MUBA is good. The timeline is behaving. Mostly. 🪶"],
            "tr": ["Hâlâ buradayım. Hâlâ tuhafım. Mükemmel. 🪶", "Hayattayım. Memeler de hayatta. 🪶",
                   "Pek bir şey yok. Sadece burada yaşıyorum. 🪶", "MUBA iyi. Timeline da idare ediyor. Çoğunlukla. 🪶"],
            "zh": ["还在这里。还是很怪。完美。🪶", "活着。meme 也活着。🪶",
                   "没什么，就在这里生活。🪶", "MUBA 状态不错。时间线也还行。大概。🪶"],
            "ar": ["ما زلت هنا. وما زلت غريباً. ممتاز. 🪶", "أنا بخير. والميمات بخير أيضاً. 🪶",
                   "لا شيء كثيراً. فقط أعيش هنا. 🪶", "MUBA بخير. والخط الزمني يتصرف. غالباً. 🪶"],
            "hi": ["अभी भी यहीं हूँ। अभी भी अजीब हूँ। परफेक्ट। 🪶", "जिंदा हूँ। मीम्स भी जिंदा हैं। 🪶",
                   "कुछ खास नहीं। बस यहीं रह रहा हूँ। 🪶", "MUBA ठीक है। टाइमलाइन भी ठीक चल रही है। शायद। 🪶"],
        },
    },
    "direct_address": {
        "patterns": {
            "en": ["hey muba", "hi muba", "hello muba", "yo muba", "muba hey", "muba hi", "muba hello"],
            "tr": ["selam muba", "merhaba muba", "hey muba", "muba selam", "muba naber"],
            "zh": ["你好muba", "嗨muba", "muba你好"],
            "ar": ["مرحبا muba", "هاي muba", "muba مرحبا"],
            "hi": ["हाय muba", "नमस्ते muba", "muba नमस्ते"],
        },
        "replies": {
            "en": ["MUBA is here. 🪶", "Hey. MUBA never left. 🪶", "Yo. We live here now. 🪶"],
            "tr": ["MUBA burada. 🪶", "Selam. MUBA hiç gitmedi. 🪶", "Yo. Burada yaşıyoruz. 🪶"],
            "zh": ["MUBA 在这里。🪶", "嗨。MUBA 从未离开。🪶", "Yo。We live here now. 🪶"],
            "ar": ["MUBA هنا. 🪶", "مرحباً. MUBA لم تغادر أبداً. 🪶", "Yo. نحن هنا الآن. 🪶"],
            "hi": ["MUBA यहाँ है। 🪶", "हे। MUBA कभी गया ही नहीं। 🪶", "Yo. We live here now. 🪶"],
        },
    },
    "casual_reaction": {
        "patterns": {
            "en": ["muba lol", "muba lmao", "muba haha", "lol muba", "lmao muba", "haha muba"],
            "tr": ["muba lol", "muba haha", "muba güldüm", "muba komik"],
            "zh": ["muba 哈哈", "muba 笑死", "哈哈 muba"],
            "ar": ["muba ههه", "muba ههههه", "ههه muba"],
            "hi": ["muba haha", "muba lol", "muba हाहा"],
        },
        "replies": {
            "en": ["Memes are alive. 🪶", "Exactly. Ridiculous energy. 🪶", "That's the spirit. 🪶"],
            "tr": ["Memeler hayatta. 🪶", "Aynen. Absürt enerji. 🪶", "Ruh bu işte. 🪶"],
            "zh": ["Meme 还活着。🪶", "没错。荒诞能量。🪶", "就是这个感觉。🪶"],
            "ar": ["الميمات حية. 🪶", "بالضبط. طاقة عبثية. 🪶", "هذه هي الروح. 🪶"],
            "hi": ["मीम्स जिंदा हैं। 🪶", "बिल्कुल। रिडिक्यूलस एनर्जी। 🪶", "यही स्पिरिट है। 🪶"],
        },
    },
}

SOCIAL_COOLDOWN_SECONDS = 18.0
_last_social_reply: Dict[Tuple[int, str], float] = {}


def _phrase_match(text: str, phrase: str) -> bool:
    value = normalize(text)
    target = normalize(phrase)

    if target in value:
        return True

    return similarity(value, target) >= 0.88


def detect_social_intent(text: str) -> Optional[str]:
    value = normalize(text)

    for intent, data in SOCIAL_INTENTS.items():
        for patterns in data["patterns"].values():
            for pattern in patterns:
                if _phrase_match(value, pattern):
                    return intent

    # Lightweight multilingual/fuzzy checks for short casual messages.
    if re.fullmatch(r"(gm|g\.m\.|good morning)+[.!🪶 ]*", value):
        return "gm"
    if re.fullmatch(r"(gn|g\.n\.|good night)+[.!🪶 ]*", value):
        return "gn"

    return None


def is_social_message(text: str) -> bool:
    return detect_social_intent(text) is not None


def _social_reply(
    intent: str,
    language: str,
    chat_id: int,
) -> Optional[str]:
    now = time.monotonic()
    key = (chat_id, intent)
    last = _last_social_reply.get(key, 0.0)

    if now - last < SOCIAL_COOLDOWN_SECONDS:
        return None

    _last_social_reply[key] = now
    replies = SOCIAL_INTENTS[intent]["replies"].get(
        language,
        SOCIAL_INTENTS[intent]["replies"]["en"],
    )

    return random.choice(replies)


# ---------------------------------------------------------------------------
# Knowledge matching
# ---------------------------------------------------------------------------

def _keyword_score(text: str, keyword: str) -> float:
    value = _clean_for_match(text)
    target = _clean_for_match(keyword)

    if not target:
        return 0.0

    if target in value:
        return 1.0

    target_words = set(tokens(target))
    value_words = set(tokens(value))

    if target_words and target_words.issubset(value_words):
        return 0.96

    overlap = len(target_words & value_words)
    if overlap:
        return min(0.90, 0.40 + 0.14 * overlap)

    return similarity(value, target)


def match_knowledge(text: str) -> Optional[Dict]:
    value = normalize(text)
    best_item: Optional[Dict] = None
    best_score = 0.0

    for item in KNOWLEDGE:
        item_score = 0.0

        for keyword in item["keywords"]:
            score = _keyword_score(value, keyword)
            if score > item_score:
                item_score = score

        if item_score > best_score:
            best_score = item_score
            best_item = item

    if best_item is None:
        return None

    # Exact/fuzzy knowledge matches need a meaningful threshold.
    threshold = 0.70 if len(value) > 12 else 0.82
    if best_score < threshold:
        return None

    return best_item


def _generic_fallback(language: str) -> str:
    replies = {
        "en": [
            "I'm MUBA. Ask me about the character, community, culture, story, philosophy, or WE LIVE HERE NOW. 🪶",
            "MUBA is here. Ask about the meme, the community, the story, or the culture. 🪶",
            "Not sure which MUBA corner you mean. Try asking about MUBA's identity, origin, purpose, community, or future. 🪶",
        ],
        "tr": [
            "Ben MUBA'yım. Karakteri, topluluğu, kültürü, hikâyeyi, felsefeyi veya WE LIVE HERE NOW mesajını sor. 🪶",
            "MUBA burada. Meme, topluluk, hikâye veya kültür hakkında sorabilirsin. 🪶",
            "Hangi MUBA konusunu kastettiğinden emin değilim. Kimliği, kökeni, amacı, topluluğu veya geleceği hakkında sor. 🪶",
        ],
        "zh": [
            "我是 MUBA。你可以问我关于角色、社区、文化、故事、理念或 WE LIVE HERE NOW 的问题。🪶",
            "MUBA 在这里。可以问 meme、社区、故事或文化。🪶",
            "不确定你指的是 MUBA 的哪一部分。可以问身份、起源、目标、社区或未来。🪶",
        ],
        "ar": [
            "أنا MUBA. اسألني عن الشخصية أو المجتمع أو الثقافة أو القصة أو الفلسفة أو WE LIVE HERE NOW. 🪶",
            "MUBA هنا. يمكنك السؤال عن الميمات أو المجتمع أو القصة أو الثقافة. 🪶",
            "لست متأكداً أي جانب من MUBA تقصد. اسأل عن الهوية أو الأصل أو الهدف أو المجتمع أو المستقبل. 🪶",
        ],
        "hi": [
            "मैं MUBA हूँ। कैरेक्टर, कम्युनिटी, कल्चर, कहानी, फिलॉसफी या WE LIVE HERE NOW के बारे में पूछो। 🪶",
            "MUBA यहाँ है। मीम, कम्युनिटी, कहानी या कल्चर के बारे में पूछ सकते हो। 🪶",
            "पक्का नहीं कि MUBA के किस हिस्से की बात है। पहचान, शुरुआत, उद्देश्य, कम्युनिटी या भविष्य के बारे में पूछो। 🪶",
        ],
    }

    return random.choice(replies.get(language, replies["en"]))


def build_reply(
    text: str,
    chat_id: int = 0,
    language: Optional[str] = None,
) -> str:
    value = (text or "").strip()

    if not value:
        return ""

    language = language or detect_language(value)

    # Social intent has priority over long-form knowledge.
    social_intent = detect_social_intent(value)
    if social_intent:
        social_response = _social_reply(
            social_intent,
            language,
            chat_id,
        )
        if social_response:
            return social_response

    # Direct MUBA identity questions and knowledge questions.
    match = match_knowledge(value)
    if match:
        return match["answers"].get(
            language,
            match["answers"]["en"],
        )

    # A direct MUBA address without a known intent gets a character response.
    if contains_muba(value):
        direct = _social_reply(
            "direct_address",
            language,
            chat_id,
        )
        if direct:
            return direct

    return _generic_fallback(language)


def get_knowledge_topics() -> List[str]:
    return [item["topic"] for item in KNOWLEDGE]


def get_brain_stats() -> Dict[str, int]:
    return {
        "knowledge_topics": len(KNOWLEDGE),
        "supported_languages": len(SUPPORTED_LANGUAGES),
        "social_intents": len(SOCIAL_INTENTS),
        "social_reply_variants": sum(
            len(replies)
            for intent in SOCIAL_INTENTS.values()
            for replies in intent["replies"].values()
        ),
    }
