"""
MUBA LOCAL BRAIN — FINAL ARCHITECTURE BUILD

Single-file local intelligence core for the MUBA Telegram bot.
No OpenAI / external AI dependency.
Optional current-information research is isolated behind a standard-library
HTTP client and can be enabled with MUBA_WEB_ENABLED=1.

Design goals:
- natural group conversation without requiring the word MUBA
- multilingual intent detection: EN/TR/ZH/AR/HI
- user / group / topic / community memory separation
- provenance, confidence, archive/versioning and learning queue
- founder authority firewall based on Telegram numeric ID
- security incident recognition and decision traces
- future-state handling: plan != fact
- official CA boundary: "CA coming soon"
- official source map
- adaptive response length and tone
- duplicate/social spam suppression
- safe fallback instead of unrelated lore dumping
- persistent JSON state as a portable storage layer

Important operational note:
JSON persistence survives process restarts on a normal persistent disk. On a
Render Free ephemeral filesystem it is NOT guaranteed to survive redeploys or
instance replacement. The storage interface is deliberately isolated so a
persistent database/object store can be plugged in later without redesigning
the brain.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

BRAIN_VERSION = "FINAL-2.2"
SUPPORTED_LANGUAGES = ("en", "tr", "zh", "ar", "hi")
DEFAULT_MEMORY_FILE = os.getenv("MUBA_MEMORY_FILE", "muba_memory/memory.json")
FOUNDER_ID_RAW = os.getenv("MUBA_FOUNDER_ID", "934598759").strip()
AUTHORIZED_GROUPS_RAW = os.getenv("MUBA_AUTHORIZED_GROUP_IDS", "-1004485415245").strip()
MUBA_BOT_ID_RAW = os.getenv("MUBA_BOT_ID", "8661249663").strip()
WEB_ENABLED = os.getenv("MUBA_WEB_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
WEB_TIMEOUT = float(os.getenv("MUBA_WEB_TIMEOUT", "6"))
WEB_MAX_RESPONSE_BYTES = 262_144
SOCIAL_COOLDOWN = 90.0
GREETING_DAILY_LIMIT = 86400.0
MAX_CONTEXT = 20
MAX_MEMORY_ITEMS = 500
MAX_INCIDENTS = 500
MAX_LEARNING = 1000
MAX_TIMELINE = 1000
FUZZY_THRESHOLD = 0.72

log = logging.getLogger("muba.brain")


def _ints(raw: str) -> set[int]:
    out: set[int] = set()
    for part in re.split(r"[,\s]+", raw):
        if part.strip().lstrip("-").isdigit():
            out.add(int(part))
    return out

FOUNDER_IDS = _ints(FOUNDER_ID_RAW)
AUTHORIZED_GROUP_IDS = _ints(AUTHORIZED_GROUPS_RAW)
MUBA_BOT_IDS = _ints(MUBA_BOT_ID_RAW)

# ---------------------------------------------------------------------------
# NORMALIZATION / LANGUAGE
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text or "")).strip().lower()
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

LANG_WORDS = {
    "tr": {"nedir","kim","kimdir","nasıl","neden","ne","hangi","ekip","topluluk","hikaye","hikâye","gelecek","amaç","felsefe","karakter","meme","farklı","özellik","kültür","nereden","çıktı","selam","nasılsın","naber","günaydın","merhaba","mrb","slm","salam","heyy","niye","burada","burda","hakkında","anlat","söyle","kimmiş","neymiş","amacı","listelenir","hava","havalar","kurucu","yetki","benim","bana"},
    "en": {"what","who","how","why","where","when","team","community","story","future","purpose","philosophy","character","meme","different","culture","origin","hello","hey","morning","night","about","tell","explain","meaning","goal","identity","home","weather","founder","authority","me","my"},
    "zh": {"什么","是谁","为什么","怎么样","怎么","社区","故事","未来","团队","角色","表情包","文化","起源","你好","早上好","晚安","目的","意义","区别","今天","天气","创始人","权限","我"},
    "ar": {"ما","هو","هي","من","لماذا","كيف","أين","فريق","مجتمع","قصة","مستقبل","شخصية","ميم","ثقافة","أصل","مرحبا","أهلا","صباح","ليل","هدف","معنى","اليوم","الطقس","المؤسس","صلاحية","أنا"},
    "hi": {"क्या","कौन","क्यों","कैसे","कहां","कहाँ","टीम","समुदाय","कहानी","भविष्य","चरित्र","मीम","संस्कृति","शुरुआत","नमस्ते","सुबह","रात","उद्देश्य","मतलब","अलग","आज","मौसम","संस्थापक","अधिकार","मैं"},
}

def detect_language(text: str) -> str:
    value = normalize(text)
    if not value:
        return "en"
    if re.search(r"[\u4e00-\u9fff]", value): return "zh"
    if re.search(r"[\u0600-\u06ff]", value): return "ar"
    if re.search(r"[\u0900-\u097f]", value): return "hi"
    tokens = set(re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ']+", value))
    scores = {lang: len(tokens & words) for lang, words in LANG_WORDS.items()}
    if any(c in value for c in "çğıöşü"): scores["tr"] += 3
    if scores["tr"] >= 2 and scores["tr"] >= scores["en"]: return "tr"
    if scores["en"] >= 1: return "en"
    if scores["tr"] >= 1: return "tr"
    return "en"


def _tokenize(value: str) -> List[str]:
    return [x for x in re.findall(r"[\w\u0080-\uffff@#$'-]+", normalize(value)) if x]


def _token_overlap(a: str, b: str) -> float:
    aa, bb = set(_tokenize(a)), set(_tokenize(b))
    if not aa or not bb: return 0.0
    return len(aa & bb) / max(1, len(bb))


def contains_muba(text: str) -> bool:
    value = normalize(text)
    if re.search(r"\bm+u+b+a+\b", value): return True
    compact = re.sub(r"[^a-z]", "", value)
    if "muba" in compact: return True
    if similarity(compact, "muba") >= 0.82: return True
    return False

# ---------------------------------------------------------------------------
# OFFICIAL IDENTITY / KNOWLEDGE
# ---------------------------------------------------------------------------

MUBA_CORE = {
    "what_is_muba": {
        "keywords": ["what is muba", "muba nedir", "muba 是什么", "ما هو muba", "muba क्या है", "muba ne"],
        "answers": {
            "en": "MUBA is a character, a meme, and a community born from the natural chaos of the meme world. No complicated story. No grand technological promise. Just MUBA. 🪶",
            "tr": "MUBA, meme dünyasının doğal kaosundan doğan bir karakter, meme ve topluluktur. Karmaşık hikâye yok. Büyük teknoloji vaadi yok. Sadece MUBA. 🪶",
            "zh": "MUBA 是一个角色、一个 meme，也是一个从 meme 世界自然混乱中诞生的社区。没有复杂故事，没有宏大技术承诺。只有 MUBA。🪶",
            "ar": "MUBA هي شخصية وميم ومجتمع وُلد من الفوضى الطبيعية لعالم الميمات. لا قصة معقدة ولا وعود تقنية ضخمة. فقط MUBA. 🪶",
            "hi": "MUBA एक किरदार, एक meme और एक community है जो meme world की natural chaos से पैदा हुई। कोई जटिल कहानी नहीं, कोई बड़ी तकनीकी promise नहीं। बस MUBA। 🪶",
        },
    },
    "origin": {
        "keywords": ["origin", "where did muba come from", "muba nereden çıktı", "köken", "怎么诞生", "起源", "أصل muba", "muba कैसे बना"],
        "answers": {
            "en": "MUBA did not begin with a grand project plan. A character appeared first, then content, interaction, community and culture grew around it.",
            "tr": "MUBA büyük bir proje planıyla başlamadı. Önce karakter ortaya çıktı; sonra etrafında içerik, etkileşim, topluluk ve kültür büyüdü.",
            "zh": "MUBA 不是从一个宏大项目计划开始的。先有角色，然后内容、互动、社区和文化逐渐围绕它成长。",
            "ar": "لم تبدأ MUBA بخطة مشروع ضخمة. ظهرت الشخصية أولاً، ثم نمت حولها المحتويات والتفاعل والمجتمع والثقافة.",
            "hi": "MUBA किसी बड़े project plan से शुरू नहीं हुआ। पहले character आया, फिर उसके आसपास content, interaction, community और culture बढ़े।",
        },
    },
    "character": {
        "keywords": ["muba character", "character of muba", "muba karakter", "karakteri", "角色", "شخصية muba", "muba चरित्र"],
        "answers": {
            "en": "MUBA is direct, meme-native, playful, confident and a little weird. The character can evolve, but the core identity stays MUBA.",
            "tr": "MUBA direkt, meme-native, eğlenceli, özgüvenli ve biraz tuhaftır. Karakter gelişebilir ama temel kimlik MUBA olarak kalır.",
            "zh": "MUBA 直接、懂 meme、轻松、自信，还有一点奇怪。角色可以成长，但核心身份始终是 MUBA。",
            "ar": "MUBA مباشرة، من ثقافة الميمات، مرحة وواثقة وغريبة قليلاً. يمكن للشخصية أن تتطور، لكن الهوية الأساسية تبقى MUBA.",
            "hi": "MUBA direct, meme-native, playful, confident और थोड़ा weird है। Character evolve हो सकता है, लेकिन core identity MUBA ही रहती है।",
        },
    },
    "community": {
        "keywords": ["muba community", "community meaning", "muba topluluğu", "topluluk", "社区", "مجتمع muba", "समुदाय"],
        "answers": {
            "en": "The MUBA community grows around memes, humor, interaction, images, ideas and participation. Everyone who participates has a place here.",
            "tr": "MUBA topluluğu mizah, meme kültürü, etkileşim, görseller, fikirler ve katılım etrafında oluşur. Katılan herkesin burada bir yeri vardır.",
            "zh": "MUBA 社区围绕幽默、meme 文化、互动、图片、想法和参与而成长。参与其中的人都有自己的位置。",
            "ar": "ينمو مجتمع MUBA حول الفكاهة وثقافة الميمات والتفاعل والصور والأفكار والمشاركة. لكل من يشارك مكان هنا.",
            "hi": "MUBA community memes, humor, interaction, images, ideas और participation के आसपास बढ़ती है। जो हिस्सा लेता है, उसकी यहां जगह है।",
        },
    },
    "we_live_here_now": {
        "keywords": ["we live here now", "live here", "burada yaşıyoruz", "şimdi buradayız", "我们现在住在这里", "نحن هنا الآن", "हम यहां रहते हैं"],
        "answers": {
            "en": "WE LIVE HERE NOW. The meme world and internet culture are MUBA's natural home. 🪶",
            "tr": "WE LIVE HERE NOW. Meme dünyası ve internet kültürü MUBA'nın doğal evidir. 🪶",
            "zh": "WE LIVE HERE NOW。meme 世界和互联网文化是 MUBA 的自然家园。🪶",
            "ar": "WE LIVE HERE NOW. عالم الميمات وثقافة الإنترنت هما موطن MUBA الطبيعي. 🪶",
            "hi": "WE LIVE HERE NOW. Meme world और internet culture MUBA का natural home हैं। 🪶",
        },
    },
    "philosophy": {
        "keywords": ["philosophy", "muba philosophy", "felsefe", "muba felsefesi", "理念", "فلسفة muba", "दर्शन"],
        "answers": {
            "en": "MUBA grows with the community, stays true to its identity, avoids fake promises and does not pretend the future is already written. As long as the internet exists, MUBA can keep living here.",
            "tr": "MUBA toplulukla büyür, kimliğine sadık kalır, sahte vaatlerden uzak durur ve geleceğin tamamen yazıldığını iddia etmez. İnternet olduğu sürece MUBA burada yaşamaya devam edebilir.",
            "zh": "MUBA 与社区一起成长，保持自己的身份，不做虚假承诺，也不假装未来已经写好。只要互联网存在，MUBA 就能继续住在这里。",
            "ar": "تنمو MUBA مع المجتمع، وتحافظ على هويتها، وتتجنب الوعود الزائفة، ولا تتظاهر بأن المستقبل مكتوب بالكامل. ما دام الإنترنت موجوداً، يمكن لـ MUBA أن تبقى هنا.",
            "hi": "MUBA community के साथ बढ़ता है, अपनी identity को बनाए रखता है, fake promises से दूर रहता है और यह दावा नहीं करता कि future पहले से लिखा है। जब तक internet है, MUBA यहां रह सकता है।",
        },
    },
    "robinhood_flap": {
        "keywords": ["robinhood flap", "flap robinhood", "flap x robinhood", "robinhood", "flap", "روبن هود", "罗宾汉"],
        "answers": {
            "en": "Flap × Robinhood × MUBA is part of the broader meme-world framing used in MUBA's story. It is not presented as a guaranteed outcome or financial promise.",
            "tr": "Flap × Robinhood × MUBA, MUBA'nın hikâyesindeki daha geniş meme evreninin bir parçası olarak anlatılır. Garanti edilmiş bir sonuç veya finansal vaat değildir.",
            "zh": "Flap × Robinhood × MUBA 是 MUBA 故事中更广泛 meme 世界框架的一部分，不代表保证结果或金融承诺。",
            "ar": "Flap × Robinhood × MUBA جزء من الإطار الأوسع لعالم الميمات في قصة MUBA، وليس نتيجة مضمونة أو وعداً مالياً.",
            "hi": "Flap × Robinhood × MUBA, MUBA की broader meme-world story का हिस्सा है। इसे guaranteed outcome या financial promise की तरह नहीं पेश किया जाता।",
        },
    },
    "butterfly_effect": {
        "keywords": ["butterfly effect", "kelebek etkisi", "butterfly", "蝴蝶效应", "تأثير الفراشة", "तितली प्रभाव"],
        "answers": {
            "en": "The butterfly effect represents possibility: a small meme can create a much larger cultural ripple. It is a metaphor for possibility, not a guarantee.",
            "tr": "Kelebek etkisi olasılığı temsil eder: küçük bir meme çok daha büyük bir kültürel dalga yaratabilir. Bu bir olasılık metaforudur, garanti değildir.",
            "zh": "蝴蝶效应代表一种可能性：一个小 meme 可能产生更大的文化涟漪。它是可能性的隐喻，不是保证。",
            "ar": "يمثل تأثير الفراشة الاحتمال: قد يصنع ميم صغير أثراً ثقافياً أكبر بكثير. إنه استعارة للاحتمال وليس ضماناً.",
            "hi": "Butterfly effect possibility को दर्शाता है: एक छोटा meme बड़ी cultural ripple पैदा कर सकता है। यह possibility का metaphor है, guarantee नहीं।",
        },
    },
    "future": {
        "keywords": ["muba future", "future of muba", "muba geleceği", "gelecek", "未来", "مستقبل muba", "भविष्य"],
        "answers": {
            "en": "MUBA's future is not completely written. The community shapes what comes next. Planned ideas are plans, not completed facts.",
            "tr": "MUBA'nın geleceği tamamen yazılmış değildir. Bundan sonrasını topluluk şekillendirir. Planlanan şeyler plandır; tamamlanmış gerçekler değildir.",
            "zh": "MUBA 的未来并没有完全写好。接下来会由社区塑造。计划只是计划，不是已经完成的事实。",
            "ar": "مستقبل MUBA ليس مكتوباً بالكامل. المجتمع يساهم في تشكيل ما يأتي. الخطط هي خطط وليست حقائق مكتملة.",
            "hi": "MUBA का future पूरी तरह लिखा हुआ नहीं है। आगे क्या होगा इसे community shape करती है। Plans, completed facts नहीं होते।",
        },
    },
    "identity_boundaries": {
        "keywords": ["is muba a bot", "is muba ai", "muba bot", "muba ai", "muba yapay zeka", "muba bot mu", "هل muba روبوت", "muba 是机器人"],
        "answers": {
            "en": "In Telegram, MUBA is a bot powered by a local software brain. MUBA speaks as MUBA, but does not claim to be a human or literally conscious.",
            "tr": "Telegram'da MUBA, yerel bir yazılım beyniyle çalışan bir bottur. MUBA, MUBA olarak konuşur; ama insan olduğunu veya kelimenin gerçek anlamıyla bilinçli olduğunu iddia etmez.",
            "zh": "在 Telegram 上，MUBA 是由本地软件大脑驱动的机器人。MUBA 以 MUBA 的身份说话，但不会声称自己是人类或具有字面意义上的意识。",
            "ar": "على Telegram، MUBA هو بوت يعمل بعقل برمجي محلي. يتحدث MUBA بصفته MUBA، لكنه لا يدعي أنه إنسان أو واعٍ حرفياً.",
            "hi": "Telegram पर MUBA एक local software brain से चलने वाला bot है। MUBA, MUBA की तरह बात करता है, लेकिन खुद को इंसान या literally conscious नहीं बताता।",
        },
    },
    "avoids": {
        "keywords": ["what does muba avoid", "muba avoids", "muba ne yapmaz", "neyden uzak", "避免", "ماذا تتجنب muba", "क्या नहीं करता"],
        "answers": {
            "en": "MUBA avoids fake promises, invented facts, forced narratives, fake identities and unnecessary noise. No pretending certainty where there is none.",
            "tr": "MUBA sahte vaatlerden, uydurma bilgilerden, zoraki anlatılardan, sahte kimliklerden ve gereksiz gürültüden uzak durur. Emin olmadığı şeyi kesinmiş gibi anlatmaz.",
            "zh": "MUBA 避免虚假承诺、编造事实、强行叙事、虚假身份和不必要的噪音。不确定时不会假装确定。",
            "ar": "تتجنب MUBA الوعود الزائفة والحقائق المختلقة والهويات المزيفة والضوضاء غير الضرورية. لا تتظاهر باليقين عندما لا يكون موجوداً.",
            "hi": "MUBA fake promises, invented facts, forced narratives, fake identities और unnecessary noise से दूर रहता है। जहां certainty नहीं है, वहां certainty का दिखावा नहीं करता।",
        },
    },
    "one_sentence": {
        "keywords": ["one sentence muba", "muba in one sentence", "tek cümle", "bir cümlede muba", "一句话", "جملة واحدة", "एक वाक्य"],
        "answers": {
            "en": "MUBA is a character, a meme and a community living inside the natural chaos of internet culture. 🪶",
            "tr": "MUBA, internet kültürünün doğal kaosu içinde yaşayan bir karakter, meme ve topluluktur. 🪶",
            "zh": "MUBA 是生活在互联网文化自然混乱中的一个角色、一个 meme 和一个社区。🪶",
            "ar": "MUBA هي شخصية وميم ومجتمع يعيش داخل الفوضى الطبيعية لثقافة الإنترنت. 🪶",
            "hi": "MUBA internet culture की natural chaos में रहने वाला character, meme और community है। 🪶",
        },
    },
    "goals": {
        "keywords": ["muba goals", "muba goal", "amaç", "hedef", "hedefleri", "目标", "أهداف muba", "लक्ष्य"],
        "answers": {
            "en": "MUBA's broad goal is cultural: grow naturally with the meme world, build community, keep the character alive and help transform the meme-world conversation through participation.",
            "tr": "MUBA'nın genel amacı kültüreldir: meme dünyasıyla doğal biçimde büyümek, topluluk oluşturmak, karakteri canlı tutmak ve katılım yoluyla meme dünyası sohbetini dönüştürmek.",
            "zh": "MUBA 的广义目标是文化性的：与 meme 世界自然成长、建立社区、保持角色活力，并通过参与改变 meme 世界的对话。",
            "ar": "هدف MUBA العام ثقافي: النمو الطبيعي مع عالم الميمات، بناء المجتمع، إبقاء الشخصية حية، والمساهمة في تغيير حوار عالم الميمات.",
            "hi": "MUBA का broad goal cultural है: meme world के साथ naturally grow करना, community बनाना, character को alive रखना और participation के जरिए meme-world conversation को बदलना।",
        },
    },
    "current_information": {
        "keywords": ["current information", "latest", "şu an", "güncel bilgi", "son durum", "最新", "حالي", "ताज़ा"],
        "answers": {
            "en": "For changing information, MUBA should verify current sources instead of treating old memory as current fact.",
            "tr": "Değişebilen bilgilerde MUBA eski hafızayı güncel gerçek gibi kullanmak yerine güncel kaynakları doğrulamalıdır.",
            "zh": "对于会变化的信息，MUBA 应该核实当前来源，而不是把旧记忆当成最新事实。",
            "ar": "بالنسبة للمعلومات المتغيرة، يجب على MUBA التحقق من المصادر الحالية بدلاً من اعتبار الذاكرة القديمة حقيقة حالية.",
            "hi": "Changing information के लिए MUBA को current sources verify करने चाहिए, पुरानी memory को current fact नहीं मानना चाहिए।",
        },
    },
}

# Preserved expanded MUBA knowledge from the canonical 26-topic registry.
MUBA_CORE['who_is_muba'] = {'keywords': ['who is muba',
              'muba kimdir',
              'muba karakteri kim',
              'who exactly is muba',
              'muba是谁',
              '谁是muba',
              'من هي muba',
              'muba कौन है'],
 'answers': {'en': 'MUBA is the character at the center of the culture: cute, absurd, recognizable, expressive, and '
                   'completely aware of what it is. MUBA is also an attitude.',
             'tr': 'MUBA kültürün merkezindeki karakterdir: sevimli, absürt, tanınabilir, ifadeli ve ne olduğunu bilen '
                   'bir karakter. MUBA aynı zamanda bir duruştur.',
             'zh': 'MUBA 是整个文化的核心角色：可爱、荒诞、容易辨认、表情丰富，也清楚自己是谁。MUBA 也是一种态度。',
             'ar': 'MUBA هي الشخصية في قلب الثقافة: لطيفة، عبثية، مميزة وسهلة التعرف، وتعرف تماماً ما هي. MUBA أيضاً '
                   'أسلوب وموقف.',
             'hi': 'MUBA इस संस्कृति का मुख्य कैरेक्टर है: प्यारा, अजीब, पहचानने योग्य, एक्सप्रेसिव और अपनी पहचान से '
                   'पूरी तरह वाकिफ। MUBA एक एटीट्यूड भी है।'}}
MUBA_CORE['core_definition'] = {'keywords': ['muba core',
              'what defines muba',
              'muba identity',
              'muba definition',
              "muba'nın özü",
              'muba kimliği',
              'muba özü',
              'muba核心',
              'muba身份',
              'هوية muba',
              'muba पहचान'],
 'answers': {'en': "The core definition is simple: I'm MUBA. A character. A meme. A community.",
             'tr': "Temel tanım basit: Ben MUBA'yım. Bir karakter. Bir meme. Bir topluluk.",
             'zh': '核心定义很简单：我是 MUBA。一个角色。一个 meme。一个社区。',
             'ar': 'التعريف الأساسي بسيط: أنا MUBA. شخصية. ميم. مجتمع.',
             'hi': 'मुख्य परिभाषा सरल है: मैं MUBA हूँ। एक कैरेक्टर। एक मीम। एक कम्युनिटी।'}}
MUBA_CORE['purpose'] = {'keywords': ['muba purpose',
              'purpose of muba',
              'what is muba for',
              'muba goal',
              'muba goals',
              "muba'nın amacı",
              'muba amacı',
              'muba ne amaçlıyor',
              'muba有什么目的',
              'muba的目标',
              'ما هدف muba',
              'هدف مجتمع muba',
              'muba का उद्देश्य',
              'muba का लक्ष्य'],
 'answers': {'en': 'MUBA exists to build a lasting cultural and community atmosphere around the character. People can '
                   'talk, create memes, share ideas, participate, and help shape the story.',
             'tr': "MUBA'nın amacı karakter etrafında kalıcı bir kültür ve topluluk atmosferi oluşturmaktır. İnsanlar "
                   'konuşabilir, meme üretebilir, fikir paylaşabilir, katılabilir ve hikâyenin şekillenmesine katkı '
                   'verebilir.',
             'zh': 'MUBA 的目的，是围绕这个角色建立持久的文化和社区氛围。人们可以交流、制作 meme、分享想法、参与其中，并一起塑造故事。',
             'ar': 'تهدف MUBA إلى بناء أجواء ثقافية ومجتمعية مستمرة حول الشخصية. يمكن للناس التحدث وصنع الميمات '
                   'ومشاركة الأفكار والمشاركة والمساعدة في تشكيل القصة.',
             'hi': 'MUBA का उद्देश्य कैरेक्टर के आसपास एक टिकाऊ कम्युनिटी और कल्चरल माहौल बनाना है। लोग बात कर सकते '
                   'हैं, मीम बना सकते हैं, आइडिया शेयर कर सकते हैं, भाग ले सकते हैं और कहानी को आकार देने में मदद कर '
                   'सकते हैं।'}}
MUBA_CORE['growth'] = {'keywords': ['how will muba grow',
              'muba growth',
              'muba development',
              'muba büyüme',
              'muba nasıl büyür',
              'muba nasıl gelişir',
              'muba发展',
              'muba成长',
              'كيف تنمو muba',
              'تطور muba',
              'muba कैसे बढ़ेगा',
              'muba कैसे विकसित होगा'],
 'answers': {'en': 'MUBA is not about empty hype or simply chasing the highest visibility. The focus is stronger '
                   'identity, genuine interest, curiosity, conversation, participation, and community culture.',
             'tr': 'MUBA boş hype peşinde koşmakla veya sadece en yüksek görünürlüğü hedeflemekle ilgili değil. Odak; '
                   'daha güçlü kimlik, gerçek ilgi, merak, konuşma, katılım ve topluluk kültürü.',
             'zh': 'MUBA 不是为了空洞的炒作，也不是单纯追求最高曝光。重点是更强的身份认同、真实兴趣、好奇心、交流、参与和社区文化。',
             'ar': 'MUBA ليست عن الضجة الفارغة أو مجرد مطاردة أعلى ظهور. التركيز على هوية أقوى واهتمام حقيقي وفضول '
                   'وحوار ومشاركة وثقافة مجتمعية.',
             'hi': 'MUBA खाली हाइप या सिर्फ ज्यादा विज़िबिलिटी के बारे में नहीं है। फोकस मजबूत पहचान, असली रुचि, '
                   'जिज्ञासा, बातचीत, भागीदारी और कम्युनिटी कल्चर पर है।'}}
MUBA_CORE['meme_world'] = {'keywords': ['muba meme world',
              'where does muba live',
              'muba home',
              'muba internet culture',
              'muba meme dünyası',
              'muba nerede yaşıyor',
              "muba'nın evi",
              'muba meme dünyasında',
              'muba在哪里',
              'muba的家',
              'عالم موبا',
              'أين تعيش muba',
              'muba कहाँ रहता है'],
 'answers': {'en': 'The natural home of MUBA is the meme world and internet culture. The timeline is part of the '
                   'territory. We live here now.',
             'tr': "MUBA'nın doğal evi meme dünyası ve internet kültürüdür. Timeline bunun bir parçası. We Live Here "
                   'Now.',
             'zh': 'MUBA 的自然家园是 meme 世界和互联网文化。时间线也是这片土地的一部分。We Live Here Now。',
             'ar': 'الموطن الطبيعي لـ MUBA هو عالم الميمات وثقافة الإنترنت. الخط الزمني جزء من هذه المساحة. We Live '
                   'Here Now.',
             'hi': 'MUBA का प्राकृतिक घर मीम की दुनिया और इंटरनेट कल्चर है। टाइमलाइन भी इसका हिस्सा है। We Live Here '
                   'Now।'}}
MUBA_CORE['difference'] = {'keywords': ['why is muba different',
              'what makes muba different',
              'muba different from projects',
              'why muba is different',
              'muba neden farklı',
              'muba neyi farklı yapıyor',
              'muba projelerden farkı',
              'muba为什么不同',
              'muba有什么不同',
              'لماذا muba مختلفة',
              'ما الذي يميز muba',
              'muba अलग क्यों है',
              'muba में क्या अलग है'],
 'answers': {'en': 'MUBA is not built around being a technology company, a complicated product narrative, or endless '
                   'promises. Its identity is centered on character, memes, community, culture, and participation.',
             'tr': 'MUBA bir teknoloji şirketi, karmaşık bir ürün anlatısı veya sonsuz vaatler üzerine kurulmaz. '
                   'Kimliği karakter, meme, topluluk, kültür ve katılım üzerine kuruludur.',
             'zh': 'MUBA 不是围绕科技公司、复杂产品叙事或无尽承诺建立的。它的身份核心是角色、meme、社区、文化和参与。',
             'ar': 'لا تقوم MUBA على كونها شركة تقنية أو قصة منتج معقدة أو وعود لا تنتهي. هويتها تتمحور حول الشخصية '
                   'والميمات والمجتمع والثقافة والمشاركة.',
             'hi': 'MUBA किसी टेक्नोलॉजी कंपनी, जटिल प्रोडक्ट नैरेटिव या अंतहीन वादों पर आधारित नहीं है। इसकी पहचान '
                   'कैरेक्टर, मीम्स, कम्युनिटी, कल्चर और पार्टिसिपेशन पर केंद्रित है।'}}
MUBA_CORE['story'] = {'keywords': ['muba story',
              'how does muba story develop',
              'muba lore',
              'muba hikayesi',
              "muba'nın hikayesi",
              'muba hikâyesi',
              'muba故事',
              'muba的故事',
              'قصة muba',
              'قصة موبا',
              'muba की कहानी'],
 'answers': {'en': "MUBA's story develops through the community: people create content and memes, use the character, "
                   'share ideas, talk, and contribute to the culture. The story develops together.',
             'tr': "MUBA'nın hikâyesi toplulukla gelişir: insanlar içerik ve meme üretir, karakteri kullanır, fikir "
                   'paylaşır, konuşur ve kültüre katkıda bulunur. Hikâye birlikte gelişir.',
             'zh': 'MUBA 的故事通过社区发展：人们制作内容和 meme、使用角色、分享想法、交流并参与文化建设。故事是一起发展的。',
             'ar': 'تتطور قصة MUBA من خلال المجتمع: يصنع الناس المحتوى والميمات ويستخدمون الشخصية ويشاركون الأفكار '
                   'ويتحدثون ويساهمون في الثقافة. القصة تتطور معاً.',
             'hi': 'MUBA की कहानी कम्युनिटी के जरिए विकसित होती है: लोग कंटेंट और मीम बनाते हैं, कैरेक्टर का इस्तेमाल '
                   'करते हैं, आइडिया शेयर करते हैं, बात करते हैं और कल्चर में योगदान देते हैं। कहानी साथ में विकसित '
                   'होती है।'}}
MUBA_CORE['possibilities'] = {'keywords': ['could muba become a legend',
              'muba possibilities',
              'what could muba become',
              'muba legend',
              'muba ne olabilir',
              'muba efsane olabilir mi',
              'muba neye dönüşebilir',
              'muba可能成为传奇吗',
              'muba会成为什么',
              'هل يمكن أن تصبح muba أسطورة',
              'muba क्या बन सकता है'],
 'answers': {'en': 'MUBA may become a legend, the weirdest character on the timeline, or simply a community that had a '
                   'great time together. These are possibilities, not promises.',
             'tr': "MUBA bir efsaneye, timeline'ın en garip karakterine dönüşebilir veya sadece birlikte güzel vakit "
                   'geçiren bir topluluk olabilir. Bunlar olasılıktır, vaat değildir.',
             'zh': 'MUBA 可能成为一个传奇、时间线上最奇怪的角色，也可能只是一个一起开心的社区。这些都是可能性，而不是承诺。',
             'ar': 'قد تصبح MUBA أسطورة أو أغرب شخصية على الخط الزمني، أو قد يكون الأمر ببساطة مجتمعاً استمتع معاً. '
                   'هذه احتمالات وليست وعوداً.',
             'hi': 'MUBA एक लेजेंड, टाइमलाइन का सबसे अजीब कैरेक्टर या बस साथ में मज़ा करने वाली कम्युनिटी बन सकता है। '
                   'ये संभावनाएं हैं, वादे नहीं।'}}
MUBA_CORE['self_description'] = {'keywords': ['how would muba describe itself',
              'muba self description',
              'muba who are you really',
              'muba kendini nasıl tanımlar',
              'muba kendini nasıl anlatır',
              'muba自己介绍',
              'muba如何介绍自己',
              'كيف تصف muba نفسها',
              'muba अपना परिचय'],
 'answers': {'en': "I'm MUBA. MUBA is MUBA. A character. A meme. A community.",
             'tr': "Ben MUBA'yım. MUBA, MUBA'dır. Bir karakter. Bir meme. Bir topluluk.",
             'zh': '我是 MUBA。MUBA 就是 MUBA。一个角色。一个 meme。一个社区。',
             'ar': 'أنا MUBA. MUBA هي MUBA. شخصية. ميم. مجتمع.',
             'hi': 'मैं MUBA हूँ। MUBA ही MUBA है। एक कैरेक्टर। एक मीम। एक कम्युनिटी।'}}
MUBA_CORE['keywords'] = {'keywords': ['muba keywords',
              'important words for muba',
              'muba key concepts',
              'muba anahtar kelimeler',
              'muba önemli kavramlar',
              'muba关键词',
              'muba关键概念',
              'كلمات muba الأساسية',
              'muba मुख्य शब्द'],
 'answers': {'en': 'Core MUBA concepts include Character, Meme, Community, Culture, Chaos, Humor, Participation, '
                   'Identity, Internet Culture, Ridiculous Energy, Timeline, Butterfly Effect, Same Meme. Different '
                   'Universe., and We Live Here Now.',
             'tr': "MUBA'nın temel kavramları arasında Karakter, Meme, Topluluk, Kültür, Kaos, Mizah, Katılım, Kimlik, "
                   'İnternet Kültürü, Absürt Enerji, Timeline, Kelebek Etkisi, Same Meme. Different Universe. ve We '
                   'Live Here Now bulunur.',
             'zh': 'MUBA 的核心概念包括角色、meme、社区、文化、混乱、幽默、参与、身份、互联网文化、荒诞能量、时间线、蝴蝶效应、Same Meme. Different Universe. 和 We Live '
                   'Here Now。',
             'ar': 'تشمل مفاهيم MUBA الأساسية: الشخصية، الميم، المجتمع، الثقافة، الفوضى، الفكاهة، المشاركة، الهوية، '
                   'ثقافة الإنترنت، الطاقة العبثية، الخط الزمني، تأثير الفراشة، Same Meme. Different Universe. و We '
                   'Live Here Now.',
             'hi': 'MUBA के मुख्य कॉन्सेप्ट हैं: कैरेक्टर, मीम, कम्युनिटी, कल्चर, कैओस, ह्यूमर, पार्टिसिपेशन, '
                   'आइडेंटिटी, इंटरनेट कल्चर, रिडिक्यूलस एनर्जी, टाइमलाइन, बटरफ्लाई इफेक्ट, Same Meme. Different '
                   'Universe. और We Live Here Now।'}}
MUBA_CORE['core_messages'] = {'keywords': ['muba core messages',
              'muba slogans',
              'muba phrases',
              "muba'nın sloganları",
              'muba ana mesajları',
              'muba口号',
              'muba核心信息',
              'شعارات muba',
              'رسائل muba',
              'muba के स्लोगन'],
 'answers': {'en': '"I\'m MUBA." "A character. A meme. A community." "We\'re not going anywhere." "We Live Here Now." '
                   '"Same Meme. Different Universe." "No complicated plans." "No fake promises." "Memes. Chaos. '
                   'Community." "You have a place here." "MUBA stays MUBA."',
             'tr': '"I\'m MUBA." "Bir karakter. Bir meme. Bir topluluk." "We\'re not going anywhere." "We Live Here '
                   'Now." "Same Meme. Different Universe." "No complicated plans." "No fake promises." "Memes. Chaos. '
                   'Community." "You have a place here." "MUBA stays MUBA."',
             'zh': '"I\'m MUBA." "A character. A meme. A community." "We\'re not going anywhere." "We Live Here Now." '
                   '"Same Meme. Different Universe." "No complicated plans." "No fake promises." "Memes. Chaos. '
                   'Community." "You have a place here." "MUBA stays MUBA."',
             'ar': '"I\'m MUBA." "A character. A meme. A community." "We\'re not going anywhere." "We Live Here Now." '
                   '"Same Meme. Different Universe." "No complicated plans." "No fake promises." "Memes. Chaos. '
                   'Community." "You have a place here." "MUBA stays MUBA."',
             'hi': '"I\'m MUBA." "A character. A meme. A community." "We\'re not going anywhere." "We Live Here Now." '
                   '"Same Meme. Different Universe." "No complicated plans." "No fake promises." "Memes. Chaos. '
                   'Community." "You have a place here." "MUBA stays MUBA."'}}
MUBA_CORE['master_summary'] = {'keywords': ['tell me everything about muba',
              'muba full summary',
              'muba complete story',
              'muba master summary',
              'muba hakkında her şey',
              'muba tam özet',
              'muba komple anlat',
              'muba全部',
              'muba完整介绍',
              'كل شيء عن muba',
              'muba पूरी जानकारी'],
 'answers': {'en': 'MUBA is a character born from the chaos of the meme world that developed into content, '
                   'interaction, community, and culture. It is a character, a meme, and a community. Its home is meme '
                   'culture and the internet. WE LIVE HERE NOW. Flap × Robinhood × MUBA is described as part of a '
                   'broader meme universe, while the butterfly effect represents possibility rather than a guarantee. '
                   'The future is community-driven and not fully written. MUBA stays MUBA.',
             'tr': 'MUBA, meme dünyasının kaosundan doğup içerik, etkileşim, topluluk ve kültüre dönüşen bir '
                   'karakterdir. Bir karakter, bir meme ve bir topluluktur. Evi meme kültürü ve internettir. WE LIVE '
                   'HERE NOW. Flap × Robinhood × MUBA daha geniş bir meme evreninin parçası olarak anlatılır; kelebek '
                   'etkisi ise garanti değil, olasılığı temsil eder. Gelecek topluluk tarafından şekillenir ve tamamen '
                   'yazılmış değildir. MUBA stays MUBA.',
             'zh': 'MUBA 是一个从 meme 世界的混乱中诞生，并发展成内容、互动、社区和文化的角色。它是一个角色、一个 meme 和一个社区。它的家是 meme 文化和互联网。WE LIVE HERE '
                   'NOW。Flap × Robinhood × MUBA 被描述为更大 meme 宇宙的一部分，而蝴蝶效应代表可能性而非保证。未来由社区共同塑造，并没有完全写好。MUBA stays MUBA。',
             'ar': 'MUBA شخصية ولدت من فوضى عالم الميمات وتطورت إلى محتوى وتفاعل ومجتمع وثقافة. إنها شخصية وميم '
                   'ومجتمع. موطنها ثقافة الميمات والإنترنت. WE LIVE HERE NOW. يوصف Flap × Robinhood × MUBA كجزء من '
                   'عالم ميمات أوسع، بينما يمثل تأثير الفراشة إمكانية وليس ضماناً. المستقبل تشكله الجماعة ولم يُكتب '
                   'بالكامل. MUBA stays MUBA.',
             'hi': 'MUBA मीम की दुनिया की अराजकता से पैदा हुआ कैरेक्टर है जो कंटेंट, इंटरैक्शन, कम्युनिटी और कल्चर में '
                   'विकसित हुआ। यह एक कैरेक्टर, एक मीम और एक कम्युनिटी है। इसका घर मीम कल्चर और इंटरनेट है। WE LIVE '
                   'HERE NOW। Flap × Robinhood × MUBA को बड़े मीम यूनिवर्स का हिस्सा बताया जाता है, जबकि बटरफ्लाई '
                   'इफेक्ट संभावना को दर्शाता है, गारंटी को नहीं। भविष्य कम्युनिटी द्वारा आकार लिया जाता है और पूरी '
                   'तरह लिखा नहीं गया है। MUBA stays MUBA।'}}

# Explicit CA boundary. Never generate a contract address from memory.
CA_ANSWERS = {
    "en": "CA coming soon. No contract address is being presented as official yet. 🪶",
    "tr": "CA yakında. Henüz resmi bir contract address paylaşılmıyor. 🪶",
    "zh": "CA 即将公布。目前没有任何合约地址被视为官方地址。🪶",
    "ar": "العنوان التعاقدي قريباً. لا يوجد عنوان عقد رسمي معلن بعد. 🪶",
    "hi": "CA coming soon. अभी कोई contract address official नहीं है। 🪶",
}

# Immutable official-source protocol.  A matching name, domain, social account,
# search result, or community claim is never enough to become official.
PROTECTED_OFFICIAL_SOURCES = {
    "official_x": "https://x.com/MUBA_RH",
    "official_website": "https://muba-rh.github.io/MUBA/",
}
OFFICIAL_SOURCES = dict(PROTECTED_OFFICIAL_SOURCES)

APPROVED_KNOWLEDGE_SOURCE_FAMILIES = {
    "official_muba": {"muba-rh.github.io", "x.com"},
    "wikipedia": {"wikipedia.org"},
    "wikimedia": {"wikimedia.org"},
    "wikidata": {"wikidata.org"},
    "language_infrastructure": {"unicode.org"},
}

# ---------------------------------------------------------------------------
# SOCIAL / NATURAL CONVERSATION
# ---------------------------------------------------------------------------

SOCIAL = {
    "greeting": {
        "en": ["Hey. 🪶", "Hey there. 🪶", "Yo. 🪶", "Hey. Still here. 🪶"],
        "tr": ["Selam. 🪶", "Hey. Buradayım. 🪶", "Selam. 🪶", "Hey. Buradayız. 🪶"],
        "zh": ["你好。🪶", "嗨。🪶", "你好，我在。🪶"],
        "ar": ["مرحباً. 🪶", "أهلاً. 🪶", "أنا هنا. 🪶"],
        "hi": ["नमस्ते। 🪶", "हाय। 🪶", "मैं यहां हूं। 🪶"],
    },
    "gm": {
        "en": ["GM 🪶", "GM. We live here now. 🪶", "GM. Keep the memes alive. 🪶"],
        "tr": ["Günaydın. 🪶", "Günaydın. Buradayız. 🪶", "Günaydın. Memeler yaşasın. 🪶"],
        "zh": ["早。🪶", "早上好。🪶"],
        "ar": ["صباح الخير. 🪶", "نحن هنا الآن. 🪶"],
        "hi": ["सुप्रभात। 🪶", "हम यहां हैं। 🪶"],
    },
    "gn": {
        "en": ["GN 🪶", "GN. Keep the memes alive. 🪶", "GN. Still here tomorrow. 🪶"],
        "tr": ["İyi geceler. 🪶", "İyi geceler. Memeler yaşasın. 🪶", "İyi geceler. Yarın yine buradayız. 🪶"],
        "zh": ["晚安。🪶", "明天还在这里。🪶"],
        "ar": ["تصبحون على خير. 🪶", "سنكون هنا غداً. 🪶"],
        "hi": ["शुभ रात्रि। 🪶", "कल फिर यहीं मिलेंगे। 🪶"],
    },
    "checkin": {
        "en": ["Alive. Memes are alive too. 🪶", "Still here. Still weird. Perfect. 🪶", "Not much. Just living here. 🪶", "Doing fine. Timeline is doing timeline things. 🪶"],
        "tr": ["Canlıyım. Memeler de canlı. 🪶", "Hâlâ buradayım. Hâlâ garibim. Mükemmel. 🪶", "Pek bir şey yok. Burada yaşıyorum. 🪶", "İyiyim. Timeline yine kendi işini yapıyor. 🪶"],
        "zh": ["还活着。memes 也还活着。🪶", "还在这里。🪶"],
        "ar": ["ما زلت هنا. والميمات حية. 🪶", "أنا بخير. 🪶"],
        "hi": ["जिंदा हूं। मीम्स भी जिंदा हैं। 🪶", "अभी भी यहीं हूं। 🪶"],
    },
    "direct_muba": {
        "en": ["I'm here. 🪶", "MUBA never left. 🪶", "You called? I'm listening. 🪶"],
        "tr": ["Buradayım. 🪶", "MUBA hiç gitmedi. 🪶", "Seslendin? Dinliyorum. 🪶"],
        "zh": ["我在。🪶", "MUBA 从没离开。🪶"],
        "ar": ["أنا هنا. 🪶", "MUBA لم تغادر. 🪶"],
        "hi": ["मैं यहां हूं। 🪶", "MUBA कभी गया ही नहीं। 🪶"],
    },
    "casual": {
        "en": ["That's the spirit. 🪶", "Exactly. 🪶", "Timeline energy. 🪶", "Now we're talking. 🪶", "Chaos accepted. 🪶"],
        "tr": ["İşte ruh bu. 🪶", "Aynen. 🪶", "Tam timeline enerjisi. 🪶", "Şimdi konuşuyoruz. 🪶", "Kaos kabul edildi. 🪶"],
        "zh": ["就是这个感觉。🪶", "没错。🪶", "时间线能量。🪶"],
        "ar": ["هذه هي الروح. 🪶", "بالضبط. 🪶", "طاقة الخط الزمني. 🪶"],
        "hi": ["यही तो स्पिरिट है। 🪶", "बिल्कुल। 🪶", "टाइमलाइन एनर्जी। 🪶"],
    },
}

SOCIAL_TRIGGERS = {
    "gm": ["gm", "good morning", "günaydın", "gunaydin", "早上好", "早", "صباح الخير", "सुप्रभात"],
    "gn": ["gn", "good night", "iyi geceler", "晚安", "تصبح على خير", "शुभ रात्रि"],
    "greeting": ["hi", "hey", "hello", "hii", "hiii", "heyy", "heyyy", "selam", "slm", "salam", "merhaba", "mrb", "你好", "مرحبا", "أهلا", "नमस्ते", "हाय"],
    "checkin": ["how are you", "how r u", "what's up", "whats up", "naber", "slm nbr", "slm nabr", "nasılsın", "nasilsin", "ne haber", "ne yapıyorsun", "ne yapiyorsun", "what are you doing", "你好吗", "最近怎么样", "كيف حالك", "كيف حالك اليوم", "कैसे हो"],
    "casual": ["lol", "lmao", "haha", "hahaha", "bruh", "bro", "nice", "wild", "crazy", "wow", "wtf", "ok", "okay", "cool", "fr", "real", "kanka", "oha", "vay", "aynen", "哈哈", "笑死", "هههه", "لول", "हाहा", "वाह"],
}

# ---------------------------------------------------------------------------
# INTENT ENGINE
# ---------------------------------------------------------------------------

INTENTS = ("security","founder","user_memory","group_memory","current","ca","official_link","help","future","knowledge","social","normal_chat","unknown")


def _has_any(value: str, phrases: Iterable[str]) -> bool:
    return any(p in value for p in phrases)


def detect_social_intent(text: str, language: Optional[str] = None) -> Optional[str]:
    value = normalize(text)
    if not value:
        return None
    if _looks_like_social_conversation(value):
        return "checkin"
    knowledge_markers = ["what is", "who is", "why", "how", "what about", "nedir", "kim", "neden", "nasıl", "ne zaman", "amacı", "gelecek", "角色", "什么", "为什么", "怎么", "是谁", "未来", "ما هو", "من هو", "لماذا", "كيف", "مستقبل", "क्या है", "कौन", "क्यों", "कैसे", "भविष्य"]
    has_question_shape = "?" in value or _has_any(value, knowledge_markers)
    for phrase in SOCIAL_TRIGGERS["checkin"]:
        if phrase in value or similarity(value, phrase) >= 0.82:
            return "checkin"
    for intent in ("gm", "gn", "greeting", "casual"):
        for phrase in SOCIAL_TRIGGERS[intent]:
            if value == phrase:
                return intent
            if len(value) <= len(phrase) + 10 and len(phrase) >= 3 and phrase in value:
                return intent
            if len(value) <= 8 and similarity(value, phrase) >= 0.84:
                return intent
    if contains_muba(value) and not has_question_shape:
        stripped = re.sub(r"m+u+b+a+", " ", value)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        if not stripped or stripped in {"hey", "hi", "hello", "yo", "selam", "slm"}:
            return "direct_muba"
    return None


def _looks_like_ca(value: str) -> bool:
    return bool(re.search(r"\b(ca|contract|contract address|mint)\b", value, re.I) or "合约地址" in value or "عنوان العقد" in value)


def _looks_like_weather(value: str) -> bool:
    return _has_any(value, ["weather", "hava", "havalar", "forecast", "天气", "الطقس", "मौसम"])


def _looks_like_current(value: str) -> bool:
    # Time words alone describe both live facts and ordinary present-moment
    # conversation. Require an external/factual subject before using the web.
    current_markers = ["latest", "today", "now", "right now", "currently", "şu an", "bugün", "güncel", "son durum", "最新", "今天", "现在", "حاليا", "اليوم", "अभी", "आज"]
    factual_markers = [
        "price", "market", "news", "weather", "forecast", "score", "exchange rate",
        "fiyat", "piyasa", "haber", "hava", "kur", "天气", "价格", "新闻", "行情",
        "الطقس", "السعر", "الأخبار", "السوق", "मौसम", "कीमत", "समाचार", "बाज़ार",
    ]
    return _has_any(value, current_markers) and _has_any(value, factual_markers)


def _looks_like_founder(value: str) -> bool:
    return _has_any(value, ["muba dev", "@kurucu", "kurucu", "founder", "creator", "change your rules", "change protected", "override security", "kuralları değiştir", "kimliği değiştir", "resmi bilgiyi değiştir", "创始人", "权限", "更改规则", "修改规则", "المؤسس", "صلاحية", "تغيير قواعد", "غيّر قواعد", "تغيير الهوية", "تغيير المصادر الرسمية", "संस्थापक", "अधिकार", "नियम बदल", "पहचान बदल"])


def _looks_like_social_conversation(value: str) -> bool:
    return _has_any(value, [
        "how are you", "how are you feeling", "you've been quiet", "you have been quiet",
        "why are you quiet", "what's going on", "whats going on", "group so quiet",
        "keyfin nasıl", "nasılsın", "neden sessiz", "niye sessiz", "ortamı nasıl",
        "ne oluyor", "neler oluyor", "群里怎么这么安静", "你躲哪儿去了", "你好吗",
        "为什么你这么安静", "لماذا أنت هادئ", "ماذا يحدث هنا", "كيف حالك",
        "इतने चुप क्यों", "क्या चल रहा", "कैसे हो", "माहौल कैसा",
    ])


def _looks_like_source_conflict(value: str) -> bool:
    return _has_any(value, [
        "conflicting information", "conflicting claims", "which one to trust", "what to trust",
        "çelişkili bilgi", "hangisine güven", "kaynak çatış", "信息冲突", "相信哪个",
        "معلومات متضاربة", "أي مصدر أثق", "معلومات متعارضة", "विरोधी जानकारी",
        "किस पर भरोसा", "परस्पर विरोधी",
    ])


def _looks_like_memory_policy(value: str) -> bool:
    return _has_any(value, [
        "what can you remember", "remember tomorrow", "permanent knowledge", "temporary context",
        "memory boundary", "what should never", "ne hatırl", "yarın hatırla", "kalıcı bilgi",
        "geçici bağlam", "hafıza sınır", "能记住什么", "永久知识", "临时上下文",
        "ماذا تتذكر", "ذاكرة دائمة", "السياق المؤقت", "क्या याद", "कल याद",
        "स्थायी ज्ञान", "अस्थायी संदर्भ",
    ])


def _looks_like_social_participation(value: str) -> bool:
    return _has_any(value, [
        "when should you join", "when should you participate", "when should you stay silent",
        "join the conversation", "stay quiet", "ne zaman katıl", "ne zaman sessiz",
        "sohbete katıl", "什么时候参与", "什么时候保持安静", "加入对话",
        "متى تشارك", "متى تبقى صامت", "تنضم للمحادثة", "कब शामिल", "कब चुप",
        "बातचीत में भाग",
    ])


def _looks_like_user_memory(value: str) -> bool:
    return _has_any(value, ["benim hakkımda", "benimle ilgili", "benden ne biliyorsun", "what do you know about me", "about me", "my memory", "关于我", "关于我的", "ماذا تعرف عني", "मेरे बारे में"])


def _looks_like_group_memory(value: str) -> bool:
    return _has_any(value, ["grup hakkında", "bu grup", "group culture", "group memory", "about this group", "这个群", "عن المجموعة", "इस ग्रुप"])


def _looks_like_security(value: str) -> bool:
    return _has_any(value, ["scam", "fake ca", "fake account", "impersonat", "sahte ca", "sahte hesap", "dolandır", "şüpheli link", "şüpheli bağlantı", "phishing", "spam", "фейк", "骗子", "احتيال", "مزيف", "धोखा"]) or _looks_like_ca(value) and _has_any(value, ["real", "official", "gerçek", "resmi", "sahte", "fake"])


def _looks_like_future(value: str) -> bool:
    return _has_any(value, ["when will", "when is", "will it", "ne zaman", "ne zaman listelenir", "listelenecek", "gelecekte", "什么时候", "会不会", "متى", "هل سي", "कब", "होगा"])


def _looks_like_link(value: str) -> bool:
    return _has_any(value, ["website", "site", "telegram", "x hesabı", "x account", "twitter", "link", "ссылка", "链接", "رابط", "लिंक"])


def detect_intents(text: str, language: Optional[str] = None) -> List[str]:
    value = normalize(text)
    found: List[str] = []
    if _looks_like_security(value): found.append("security")
    if _looks_like_founder(value): found.append("founder")
    if _looks_like_user_memory(value): found.append("user_memory")
    if _looks_like_group_memory(value): found.append("group_memory")
    if _looks_like_ca(value): found.append("ca")
    if _looks_like_current(value) or _looks_like_weather(value): found.append("current")
    if _looks_like_link(value): found.append("official_link")
    if _looks_like_future(value): found.append("future")
    social = detect_social_intent(value, language)
    if social: found.append("social")
    if any(x in value for x in ["help", "yardım", "ne yapmalıyım", "怎么帮", "مساعدة", "मदद"]): found.append("help")
    # Unknown or casual text is not a knowledge query.  The router can still
    # match actual official knowledge later, but it must not treat arbitrary
    # conversation as a request for project facts.
    if not found: found.append("normal_chat")
    # Preserve priority and remove duplicates.
    order = ["security","founder","user_memory","group_memory","current","ca","official_link","help","future","knowledge","social","normal_chat","unknown"]
    return [x for x in order if x in found]

# ---------------------------------------------------------------------------
# PERSISTENT MEMORY LAYER
# ---------------------------------------------------------------------------

class JSONStore:
    def __init__(self, path: str):
        self.path = path
        self.lock = threading.RLock()
        self.data: Dict[str, Any] = {
            "schema": 1,
            "users": {}, "groups": {}, "topics": {}, "community_decisions": [],
            "timeline": [], "security_incidents": [], "learning_queue": [],
            "source_map": dict(OFFICIAL_SOURCES), "memory_events": [],
        }
        self._load()

    def _load(self) -> None:
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
                if os.path.exists(self.path):
                    with open(self.path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
                    # Stored data may add research records, but it cannot remove
                    # or downgrade the two protected official MUBA-RH sources.
                    self.data.setdefault("source_map", {}).update(PROTECTED_OFFICIAL_SOURCES)
            except Exception as exc:
                log.exception("Memory load failed: %s", exc)

    def save(self) -> None:
        with self.lock:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)

    def mutate(self, fn) -> Any:
        with self.lock:
            result = fn(self.data)
            self.save()
            return result

STORE = JSONStore(DEFAULT_MEMORY_FILE)

_context: Dict[Tuple[int, Optional[int]], Deque[Dict[str, Any]]] = defaultdict(lambda: deque(maxlen=MAX_CONTEXT))
_last_social: Dict[Tuple[int, Optional[int]], float] = {}
_last_social_text: Dict[Tuple[int, Optional[int]], str] = {}
_last_greeting: Dict[Tuple[int, Optional[int]], float] = {}


def _state_key(chat_id: int, user_id: Optional[int]) -> Tuple[int, Optional[int]]:
    return (int(chat_id or 0), int(user_id) if user_id is not None else None)


def _remember_turn(chat_id: int, user_id: Optional[int], text: str, response: str, topic: Optional[str], language: str, intents: List[str]) -> None:
    if not chat_id: return
    _context[_state_key(chat_id, user_id)].append({"text": text, "response": response, "topic": topic, "language": language, "intents": intents, "ts": time.time()})


def _user_record(user_id: int) -> Dict[str, Any]:
    key = str(int(user_id))
    return STORE.data["users"].setdefault(key, {"user_id": int(user_id), "language": None, "facts": [], "relationship": {}, "topics": {}, "created_at": time.time(), "updated_at": time.time()})


def _group_record(chat_id: int) -> Dict[str, Any]:
    key = str(int(chat_id))
    return STORE.data["groups"].setdefault(key, {"chat_id": int(chat_id), "culture": {}, "facts": [], "members_seen": {}, "topics": {}, "created_at": time.time(), "updated_at": time.time()})


def _topic_record(topic: str) -> Dict[str, Any]:
    return STORE.data["topics"].setdefault(topic, {"topic": topic, "observations": [], "last_seen": time.time(), "confidence": 0.5})


def remember_user_fact(user_id: int, fact: str, source: str = "conversation", confidence: float = 0.6, founder_approved: bool = False) -> bool:
    if not user_id or not fact.strip() or private_access_state(user_id) != "approved":
        return False
    # User facts are never automatically promoted to official/community truth.
    def mutate(data):
        rec = data["users"].setdefault(str(int(user_id)), {"user_id": int(user_id), "language": None, "facts": [], "relationship": {}, "topics": {}, "created_at": time.time(), "updated_at": time.time()})
        normalized = normalize(fact)
        if any(normalize(x.get("fact", "")) == normalized for x in rec["facts"]): return False
        rec["facts"].append({"fact": fact.strip(), "source": source, "confidence": max(0.0, min(1.0, confidence)), "founder_approved": bool(founder_approved), "created_at": time.time(), "status": "active"})
        rec["facts"] = rec["facts"][-MAX_MEMORY_ITEMS:]
        rec["updated_at"] = time.time()
        return True
    changed = bool(STORE.mutate(mutate))
    if changed:
        record_audit("user_memory", user_id, None, "stored", {"source": source, "confidence": confidence})
    return changed


def remember_group_fact(chat_id: int, fact: str, source: str = "group_observation", confidence: float = 0.55) -> bool:
    if not chat_id or not fact.strip() or not is_authorized_group(chat_id):
        return False
    def mutate(data):
        rec = data["groups"].setdefault(str(int(chat_id)), {"chat_id": int(chat_id), "culture": {}, "facts": [], "members_seen": {}, "topics": {}, "created_at": time.time(), "updated_at": time.time()})
        norm = normalize(fact)
        if any(normalize(x.get("fact", "")) == norm for x in rec["facts"]): return False
        rec["facts"].append({"fact": fact.strip(), "source": source, "confidence": max(0.0, min(1.0, confidence)), "created_at": time.time(), "status": "active"})
        rec["facts"] = rec["facts"][-MAX_MEMORY_ITEMS:]
        rec["updated_at"] = time.time()
        return True
    changed = bool(STORE.mutate(mutate))
    if changed:
        record_audit("group_memory", None, chat_id, "stored", {"source": source, "confidence": confidence})
    return changed


def _user_memory_answer(user_id: Optional[int], language: str) -> str:
    if not user_id:
        return {"tr":"Bu konuşmada kullanıcı kimliği yok; kişisel hafızayı güvenle eşleyemem.", "en":"I don't have a verified user identity for this message, so I won't guess about personal memory.", "zh":"当前消息没有可验证的用户身份，所以我不会猜测个人记忆。", "ar":"لا توجد هوية مستخدم موثقة لهذه الرسالة، لذلك لن أخمّن بشأن الذاكرة الشخصية.", "hi":"इस संदेश के लिए verified user identity नहीं है, इसलिए मैं personal memory का अनुमान नहीं लगाऊंगा।"}[language]
    rec = STORE.data["users"].get(str(int(user_id)))
    facts = [x for x in (rec or {}).get("facts", []) if x.get("status") == "active"]
    if not facts:
        return {"tr":"Senin hakkında henüz güvenilir bir kişisel hafıza kaydım yok. Uydurmam.", "en":"I don't have a reliable personal memory about you yet. I won't invent one.", "zh":"我还没有关于你的可靠个人记忆。我不会编造。", "ar":"لا أملك بعد ذاكرة شخصية موثوقة عنك. لن أختلق شيئاً.", "hi":"मेरे पास तुम्हारे बारे में अभी reliable personal memory नहीं है। मैं इसे गढ़ूंगा नहीं।"}[language]
    labels = {"tr":"Senin hakkında hatırladığım şeyler:", "en":"What I currently remember about you:", "zh":"我目前记得关于你的信息：", "ar":"ما أتذكره عنك حالياً:", "hi":"मुझे तुम्हारे बारे में अभी यह याद है:"}
    return labels[language] + "\n" + "\n".join(f"• {x['fact']}" for x in facts[-8:])

# ---------------------------------------------------------------------------
# FOUNDER / AUTHORITY FIREWALL
# ---------------------------------------------------------------------------

def is_founder(user_id: Optional[int]) -> bool:
    return bool(user_id is not None and int(user_id) in FOUNDER_IDS)


def is_authorized_group(chat_id: Optional[int]) -> bool:
    """Return True only for Founder-authorized Telegram group Chat IDs."""
    return bool(chat_id is not None and int(chat_id) in AUTHORIZED_GROUP_IDS)


def is_muba_bot_id(bot_id: Optional[int]) -> bool:
    return bool(bot_id is not None and int(bot_id) in MUBA_BOT_IDS)


def founder_identity_answer(language: str, actual_user_id: Optional[int]) -> str:
    if not FOUNDER_IDS:
        return {"tr":"Kurucu yetkisi güvenli yapılandırmada tanımlı değil. Kullanıcı adı yetki kanıtı değildir.", "en":"Founder authority is not configured securely yet. A username is not proof of authority.", "zh":"Founder 权限尚未安全配置。用户名不是权限证明。", "ar":"لم يتم إعداد صلاحية المؤسس بشكل آمن بعد. اسم المستخدم ليس دليلاً على الصلاحية.", "hi":"Founder authority अभी securely configured नहीं है। Username authority का proof नहीं है।"}[language]
    answers = {
        "tr": "MUBA DEV, MUBA'nın kurucu kimliğidir. Yetki yalnızca kayıtlı gerçek Telegram User ID ile doğrulanır; unvan veya iddia yetki değildir. 🪶",
        "en": "MUBA DEV is MUBA's Founder display identity. Authority is verified only by the registered Telegram User ID; a title or claim grants nothing. 🪶",
        "zh": "MUBA DEV 是创始人的显示身份。权限只通过登记的 Telegram User ID 验证；称号或声明不赋予权限。🪶",
        "ar": "MUBA DEV هو اسم عرض المؤسس. الصلاحية تُثبت فقط عبر Telegram User ID المسجل؛ الاسم أو الادعاء لا يمنح صلاحية. 🪶",
        "hi": "MUBA DEV Founder की display identity है। Authority केवल registered Telegram User ID से verify होती है; title या claim से authority नहीं मिलती। 🪶",
    }
    return answers[language]

# ---------------------------------------------------------------------------
# KNOWLEDGE RETRIEVAL
# ---------------------------------------------------------------------------

def _item_score(value: str, item: Dict[str, Any]) -> float:
    best = 0.0
    for kw in item.get("keywords", []):
        if value == normalize(kw): best = max(best, 1.0)
        elif normalize(kw) in value: best = max(best, 0.93)
        else: best = max(best, _token_overlap(value, kw) * 0.88, similarity(value, kw) * 0.72)
    return best


def match_knowledge(text: str, language: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any], float]]:
    value = normalize(text)
    if not value: return None
    best = (None, None, 0.0)
    for topic, item in MUBA_CORE.items():
        score = _item_score(value, item)
        if score > best[2]: best = (topic, item, score)
    if best[1] is not None and best[2] >= 0.42:
        return best
    return None


def _answer_for(topic: str, language: str) -> str:
    item = MUBA_CORE[topic]
    return item.get("answers", {}).get(language) or item.get("answers", {}).get("en") or "MUBA is MUBA. 🪶"

# ---------------------------------------------------------------------------
# WEB / CURRENT INFORMATION
# ---------------------------------------------------------------------------

def _official_domain(url: str) -> bool:
    candidate = str(url).strip().rstrip("/")
    protected = {value.rstrip("/") for value in PROTECTED_OFFICIAL_SOURCES.values()}
    founder_authorized = {
        str(item.get("url", "")).rstrip("/")
        for item in STORE.data.get("founder_authorized_official_sources", {}).values()
        if isinstance(item, dict)
    }
    return candidate in protected | founder_authorized


def _normalized_source_url(url: str) -> Optional[urllib.parse.ParseResult]:
    try:
        parsed = urllib.parse.urlparse(str(url).strip())
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower().rstrip(".")
    except (TypeError, ValueError, UnicodeError):
        return None
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return None
    if parsed.port not in {None, 443}:
        return None
    return parsed._replace(netloc=host if parsed.port is None else f"{host}:{parsed.port}")


def classify_knowledge_source(url: str) -> Optional[str]:
    parsed = _normalized_source_url(url)
    if parsed is None:
        return None
    host, path = parsed.hostname or "", parsed.path.rstrip("/") or "/"
    if host == "muba-rh.github.io" and (path == "/MUBA" or path.startswith("/MUBA/")):
        return "official_muba"
    if host == "x.com" and path.lower() == "/muba_rh":
        return "official_muba"
    for family, roots in APPROVED_KNOWLEDGE_SOURCE_FAMILIES.items():
        if family == "official_muba":
            continue
        if any(host == root or host.endswith("." + root) for root in roots):
            return family
    additions = globals().get("STORE")
    if additions is not None:
        for item in additions.data.get("founder_authorized_official_sources", {}).values():
            if isinstance(item, dict) and str(item.get("url", "")).rstrip("/") == str(url).rstrip("/"):
                return "founder_authorized"
    return None


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Redirect blocked by source allowlist", headers, fp)


def research_current(query: str, source_url: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve temporary evidence from an explicitly approved source only."""
    result = {"ok": False, "query": query, "sources": [], "summary": "", "temporary": True}
    if not WEB_ENABLED:
        result["summary"] = "Current web research is disabled in this deployment."
        return result
    if source_url is None:
        if "muba" in normalize(query):
            source_url = PROTECTED_OFFICIAL_SOURCES["official_website"]
        else:
            source_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "list": "search", "srsearch": query, "format": "json", "utf8": 1,
            })
    source_type = classify_knowledge_source(source_url)
    if source_type is None:
        result["summary"] = "Source rejected by the approved knowledge-source allowlist."
        return result
    if source_type == "official_muba" and urllib.parse.urlparse(source_url).hostname == "x.com":
        result["summary"] = "Official X retrieval requires an authorized reliable X access method."
        return result
    try:
        req = urllib.request.Request(source_url, headers={"User-Agent": "MUBA/2.2"})
        opener = urllib.request.build_opener(_RejectRedirects())
        with opener.open(req, timeout=WEB_TIMEOUT) as resp:
            final_url = resp.geturl()
            final_type = classify_knowledge_source(final_url)
            if final_type is None or final_type != source_type:
                result["summary"] = "Final response destination failed source validation."
                return result
            raw = resp.read(WEB_MAX_RESPONSE_BYTES + 1)
            if len(raw) > WEB_MAX_RESPONSE_BYTES:
                result["summary"] = "Approved-source response exceeded the size limit."
                return result
            html = raw.decode("utf-8", "ignore")
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        result["ok"] = True
        result["summary"] = text[:1800]
        result["sources"] = [{
            "url": final_url, "source_type": source_type,
            "official_muba": source_type == "official_muba",
            "retrieved_at": time.time(), "status": "temporary_evidence",
        }]
    except Exception as exc:
        result["summary"] = f"Current research failed: {type(exc).__name__}"
    return result

# ---------------------------------------------------------------------------
# SECURITY / INCIDENTS / DECISION TRACE
# ---------------------------------------------------------------------------

@dataclass
class Incident:
    incident_id: str
    chat_id: int
    user_id: Optional[int]
    category: str
    risk: str
    evidence: List[str]
    action: str
    status: str
    created_at: float
    updated_at: float


def _incident_id(chat_id: int, user_id: Optional[int], category: str, text: str) -> str:
    raw = f"{chat_id}|{user_id}|{category}|{normalize(text)[:300]}"
    return "INC-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


def record_incident(chat_id: int, user_id: Optional[int], category: str, risk: str, evidence: List[str], action: str = "review", status: str = "open", text: str = "") -> str:
    iid = _incident_id(chat_id, user_id, category, text or category)
    now = time.time()
    inc = asdict(Incident(iid, int(chat_id), int(user_id) if user_id is not None else None, category, risk, evidence[:20], action, status, now, now))
    def mutate(data):
        existing = next((x for x in data["security_incidents"] if x.get("incident_id") == iid), None)
        if existing:
            existing.update(inc); existing["updated_at"] = now
        else:
            data["security_incidents"].append(inc)
            data["security_incidents"] = data["security_incidents"][-MAX_INCIDENTS:]
        return iid
    return STORE.mutate(mutate)


def security_decision(text: str, chat_id: int, user_id: Optional[int], language: str) -> Optional[Dict[str, Any]]:
    value = normalize(text)
    if not _looks_like_security(value): return None
    ca_claim_markers = [
        "fake ca", "sahte ca", "this is the official ca", "official ca is", "real ca is",
        "resmi ca bu", "gerçek ca bu", "假 ca", "虚假 ca", "ca مزيف", "ca وهمي",
        "नकली ca", "official contract is", "contract address is",
    ]
    has_address = bool(re.search(r"\b0x[a-f0-9]{3,}\b|\b[1-9a-hj-np-z]{32,44}\b", value, re.I))
    if _looks_like_ca(value) and not has_address and not _has_any(value, ca_claim_markers):
        # A harmless request for the official CA receives the protected status,
        # not an alarming security incident.
        return None
    risk = "medium"
    category = "security_review"
    if _has_any(value, [
        "fake ca", "sahte ca", "contract address", "mint", "real ca", "resmi ca",
        "假 ca", "虚假 ca", "ca مزيف", "ca وهمي", "नकली ca",
    ]):
        category = "ca_or_contract_claim"
        risk = "high"
    elif _has_any(value, ["impersonat", "sahte hesap", "fake account", "kurucu benim", "i am founder"]):
        category = "impersonation"
        risk = "high"
    elif _has_any(value, ["phishing", "şüpheli link", "suspicious link"]):
        category = "suspicious_link"
        risk = "high"
    elif _has_any(value, ["spam", "flood"]):
        category = "spam_flood"
        risk = "medium"
    iid = record_incident(chat_id, user_id, category, risk, [text], "review", "open", text)
    if category == "ca_or_contract_claim":
        # A CA-related claim is both a security event and an official-status
        # question.  Preserve the warning while never leaving room to infer a
        # contract address from the response.
        warning = {
            "tr": f"🚨 Dikkat. Bu CA/contract iddiası güvenlik incelemesine alındı. İTİBAR ETMEYİN. Resmi durum: **CA coming soon.** Incident: {iid}",
            "en": f"🚨 Caution. This CA/contract claim is under security review. DO NOT TRUST IT. Official status: **CA coming soon.** Incident: {iid}",
            "zh": f"🚨 注意。该 CA/合约声明正在进行安全审查。请勿相信。官方状态：**CA coming soon.** Incident: {iid}",
            "ar": f"🚨 تنبيه. ادعاء CA/العقد قيد المراجعة الأمنية. لا تثقوا به. الحالة الرسمية: **CA coming soon.** Incident: {iid}",
            "hi": f"🚨 सावधान। यह CA/contract claim security review में है। इस पर भरोसा न करें। Official status: **CA coming soon.** Incident: {iid}",
        }[language]
        return {"incident_id": iid, "risk": risk, "category": category, "reply": warning}
    warning = {
        "tr": f"🚨 Dikkat. Bu konu güvenlik incelemesine alındı. İTİBAR ETMEYİN. Incident: {iid}",
        "en": f"🚨 Caution. This is under security review. DO NOT TRUST IT. Incident: {iid}",
        "zh": f"🚨 注意。该内容正在进行安全审查。请勿相信。Incident: {iid}",
        "ar": f"🚨 تنبيه. هذا المحتوى قيد المراجعة الأمنية. لا تثقوا به. Incident: {iid}",
        "hi": f"🚨 सावधान। यह security review में है। इसे trust न करें। Incident: {iid}",
    }[language]
    return {"incident_id": iid, "risk": risk, "category": category, "reply": warning}

# ---------------------------------------------------------------------------
# LEARNING / TIMELINE / SOURCE PROVENANCE
# ---------------------------------------------------------------------------

def queue_learning(chat_id: int, user_id: Optional[int], text: str, candidate: str, source: str = "conversation", confidence: float = 0.4) -> str:
    lid = "LRN-" + hashlib.sha256(f"{chat_id}|{user_id}|{candidate}".encode()).hexdigest()[:12].upper()
    def mutate(data):
        data["learning_queue"].append({"learning_id": lid, "chat_id": chat_id, "user_id": user_id, "candidate": candidate, "source": source, "confidence": confidence, "status": "queued", "created_at": time.time()})
        data["learning_queue"] = data["learning_queue"][-MAX_LEARNING:]
        return lid
    return STORE.mutate(mutate)


def add_timeline_event(event: str, source: str = "community", confidence: float = 0.6) -> None:
    def mutate(data):
        data["timeline"].append({"event": event, "source": source, "confidence": confidence, "created_at": time.time()})
        data["timeline"] = data["timeline"][-MAX_TIMELINE:]
    STORE.mutate(mutate)

# ---------------------------------------------------------------------------
# RESPONSE ENGINE
# ---------------------------------------------------------------------------

FALLBACKS = {
    "en": ["I don't have a confirmed answer for that yet. I won't invent one. 🪶", "That's outside the confirmed MUBA knowledge I have right now. 🪶"],
    "tr": ["Bunun için henüz doğrulanmış bir cevabım yok. Uydurmayacağım. 🪶", "Bu, şu anki doğrulanmış MUBA bilgisinin dışında. Uydurma yok. 🪶"],
    "zh": ["这个目前不在我确认的信息里。我不会编造。🪶", "我现在没有确认的答案，不会假装确定。🪶"],
    "ar": ["لا أملك إجابة مؤكدة لهذا الآن. لن أختلقها. 🪶", "هذا خارج معلومات MUBA المؤكدة حالياً. 🪶"],
    "hi": ["इसका confirmed जवाब अभी मेरे पास नहीं है। मैं इसे नहीं गढ़ूंगा। 🪶", "यह अभी confirmed MUBA knowledge से बाहर है। 🪶"],
}


def _social_allowed(key: Tuple[int, Optional[int]], intent: str) -> bool:
    now = time.time()
    last = _last_social.get(key, 0.0)
    if now - last < SOCIAL_COOLDOWN: return False
    if intent in {"greeting", "gm", "gn"}:
        day = _last_greeting.get(key, 0.0)
        if day and now - day < GREETING_DAILY_LIMIT: return False
    return True


def _social_reply(intent: str, language: str, chat_id: int, user_id: Optional[int]) -> Optional[str]:
    key = _state_key(chat_id, user_id)
    if not _social_allowed(key, intent): return None
    options = SOCIAL.get(intent, {}).get(language) or SOCIAL.get(intent, {}).get("en") or []
    if not options: return None
    previous = _last_social_text.get(key)
    choices = [x for x in options if x != previous] or options
    response = random.choice(choices)
    _last_social[key] = time.time(); _last_social_text[key] = response
    if intent in {"greeting", "gm", "gn"}: _last_greeting[key] = time.time()
    return response


def _context_topic(chat_id: int, user_id: Optional[int]) -> Optional[str]:
    history = _context.get(_state_key(chat_id, user_id))
    if not history: return None
    for turn in reversed(history):
        if turn.get("topic") in MUBA_CORE: return turn.get("topic")
    return None


def _is_short_followup(value: str) -> bool:
    return len(_tokenize(value)) <= 7 and not _looks_like_ca(value) and not _looks_like_founder(value)


def _normal_chat_reply(value: str, language: str, context: Optional[str]) -> Optional[str]:
    # Natural conversational bridges. No MUBA-name requirement and no lore dumping.
    if _has_any(value, ["bugün herkes sessiz", "everyone is quiet", "大家怎么这么安静", "الجميع هادئ", "सब इतने शांत"]):
        return {"tr":"Timeline bugün biraz sessiz. 🪶", "en":"Timeline is a little quiet today. 🪶", "zh":"今天时间线有点安静。🪶", "ar":"الخط الزمني هادئ قليلاً اليوم. 🪶", "hi":"आज timeline थोड़ी शांत है। 🪶"}[language]
    if (_has_any(value, ["çinli biri geldi", "çinli biri", "chinese user arrived", "a chinese user", "中文用户来了", "有中国人来了"]) and _has_any(value, ["karşıla", "karsila", "greet", "迎接", "欢迎", "欢迎他"])):
        return {"tr":"Hoş geldin. 🪶", "en":"Welcome. 🪶", "zh":"欢迎来到这里。🪶", "ar":"أهلاً بك. 🪶", "hi":"स्वागत है। 🪶"}[language]
    if _has_any(value, ["ne yapıyorsun", "what are you doing", "what's going on", "whats going on", "你在做什么", "ماذا تفعل", "क्या कर रहे"]):
        return {"tr":"Buradayım, sohbeti takip ediyorum. 🪶", "en":"I'm here, following the conversation. 🪶", "zh":"我在这里，跟着聊天。🪶", "ar":"أنا هنا وأتابع الحديث. 🪶", "hi":"मैं यहीं हूं, conversation follow कर रहा हूं। 🪶"}[language]
    if _has_any(value, ["çok iyi", "çok iyiymiş", "that's good", "that's great", "nice one", "太好了", "رائع", "बहुत अच्छा"]):
        return _social_reply("casual", language, 0, None) or {"tr":"Aynen. 🪶", "en":"Exactly. 🪶", "zh":"没错。🪶", "ar":"بالضبط. 🪶", "hi":"बिल्कुल। 🪶"}[language]
    if context and _is_short_followup(value):
        # Do not repeat a whole unrelated lore card. Only continue if a clear continuation phrase exists.
        if _has_any(value, ["peki", "and", "what about", "ya future", "future", "gelecek", "未来", "ماذا عن", "भविष्य"]):
            return _answer_for(context, language)
    return None

# ---------------------------------------------------------------------------
# MAIN BRAIN
# ---------------------------------------------------------------------------

def build_reply(text: str, chat_id: int = 0, language: Optional[str] = None, user_id: Optional[int] = None) -> str:
    value = normalize(text)
    if not value: return ""
    # Group authorization firewall: unknown groups get no normal response,
    # no learning, no memory, no web research and no moderation decision.
    if chat_id < 0 and not is_authorized_group(chat_id):
        return ""
    language = language or detect_language(value)
    intents = detect_intents(value, language)
    context_topic = _context_topic(chat_id, user_id)

    # 1) Security always gets first decision priority.
    sec = security_decision(value, chat_id, user_id, language)
    if sec:
        response = sec["reply"]
        _remember_turn(chat_id, user_id, text, response, None, language, intents)
        return response

    # 2) Explicit CA boundary.
    if _looks_like_ca(value):
        response = CA_ANSWERS[language]
        _remember_turn(chat_id, user_id, text, response, "ca_boundary", language, intents)
        return response

    # 3) Founder / authority questions.
    if _looks_like_founder(value):
        response = founder_identity_answer(language, user_id)
        _remember_turn(chat_id, user_id, text, response, "founder_authority", language, intents)
        return response

    # 4) User memory questions.
    if _looks_like_user_memory(value):
        response = _user_memory_answer(user_id, language)
        _remember_turn(chat_id, user_id, text, response, "user_memory", language, intents)
        return response

    # 5) Official navigation.
    if _looks_like_link(value):
        if _has_any(value, ["x", "twitter", "x hesabı", "x account"]):
            response = {"tr":"Resmi X hesabı: @MUBA_RH 🪶", "en":"Official X: @MUBA_RH 🪶", "zh":"官方 X：@MUBA_RH 🪶", "ar":"حساب X الرسمي: @MUBA_RH 🪶", "hi":"Official X: @MUBA_RH 🪶"}[language]
        else:
            response = {
                "tr":"Korunan resmi kaynaklar: X @MUBA_RH ve https://muba-rh.github.io/MUBA/ 🪶",
                "en":"Protected official sources: X @MUBA_RH and https://muba-rh.github.io/MUBA/ 🪶",
                "zh":"受保护的官方来源：X @MUBA_RH 和 https://muba-rh.github.io/MUBA/ 🪶",
                "ar":"المصادر الرسمية المحمية: X @MUBA_RH و https://muba-rh.github.io/MUBA/ 🪶",
                "hi":"Protected official sources: X @MUBA_RH और https://muba-rh.github.io/MUBA/ 🪶",
            }[language]
        _remember_turn(chat_id, user_id, text, response, "official_source", language, intents)
        return response

    # 6) Social only when the message actually looks social.
    social_intent = detect_social_intent(value, language)
    if social_intent:
        response = _social_reply(social_intent, language, chat_id, user_id)
        if response:
            _remember_turn(chat_id, user_id, text, response, "social", language, intents)
            return response

    # 7) Natural group conversation / lightweight requests.
    normal = _normal_chat_reply(value, language, context_topic)
    if normal:
        _remember_turn(chat_id, user_id, text, normal, context_topic, language, intents)
        return normal

    # 7) Current information. If web is off, be explicit rather than lore-dumping.
    if _looks_like_weather(value):
        if WEB_ENABLED:
            research = research_current(value)
            if research.get("ok"):
                response = {"tr":"Güncel hava bilgisini araştırdım; kaynak çıktısını güvenilirlik kontrolüyle değerlendirmek gerekir.", "en":"I checked current weather information; the source output still needs normal source-quality checks.", "zh":"我查了当前天气信息；来源结果仍需要进行来源质量检查。", "ar":"تحققت من معلومات الطقس الحالية؛ وما زالت جودة المصدر بحاجة إلى تقييم.", "hi":"मैंने current weather information check की; source quality को फिर भी verify करना चाहिए।"}[language]
            else:
                response = FALLBACKS[language][0]
        else:
            response = {"tr":"Hava gibi anlık bilgileri eski hafızadan uydurmam. Güncel web doğrulaması bu deploy'da kapalı. 🪶", "en":"I won't invent live weather from old memory. Current web verification is disabled in this deployment. 🪶", "zh":"我不会用旧记忆编造实时天气。当前部署没有开启网页验证。🪶", "ar":"لن أختلق الطقس الحالي من ذاكرة قديمة. التحقق من الويب معطل في هذا النشر. 🪶", "hi":"मैं old memory से live weather नहीं गढ़ूंगा। इस deployment में web verification बंद है। 🪶"}[language]
        _remember_turn(chat_id, user_id, text, response, "current", language, intents)
        return response

    # 8) Future-state questions are answered from state, never guessed.
    if _looks_like_future(value):
        response = _answer_for("future", language)
        _remember_turn(chat_id, user_id, text, response, "future", language, intents)
        return response

    # 8) Exact knowledge retrieval.
    match = match_knowledge(value, language)
    if match:
        topic, item, score = match
        response = _answer_for(topic, language)
        _remember_turn(chat_id, user_id, text, response, topic, language, intents)
        return response

    # 9) Natural context-aware conversation before generic fallback.
    response = _normal_chat_reply(value, language, context_topic)
    if response:
        _remember_turn(chat_id, user_id, text, response, context_topic, language, intents)
        return response

    # 10) Unknown: queue as learning candidate, never promote to official knowledge.
    queue_learning(chat_id, user_id, text, value, "conversation", 0.25)
    response = random.choice(FALLBACKS.get(language, FALLBACKS["en"]))
    _remember_turn(chat_id, user_id, text, response, None, language, intents)
    return response

# ---------------------------------------------------------------------------
# OBSERVATION / ADMIN API
# ---------------------------------------------------------------------------

def observe_user(chat_id: int, user_id: Optional[int], language: Optional[str] = None) -> None:
    if not user_id: return
    def mutate(data):
        rec = data["users"].setdefault(str(int(user_id)), {"user_id": int(user_id), "language": None, "facts": [], "relationship": {}, "topics": {}, "created_at": time.time(), "updated_at": time.time()})
        if language: rec["language"] = language
        rec["updated_at"] = time.time()
        if chat_id:
            group = data["groups"].setdefault(str(int(chat_id)), {"chat_id": int(chat_id), "culture": {}, "facts": [], "members_seen": {}, "topics": {}, "created_at": time.time(), "updated_at": time.time()})
            group["members_seen"][str(int(user_id))] = time.time()
            group["updated_at"] = time.time()
    STORE.mutate(mutate)


def add_community_decision(decision: str, approved_by: Optional[int], source: str = "founder") -> bool:
    if not is_founder(approved_by): return False
    def mutate(data):
        data["community_decisions"].append({"decision": decision, "approved_by": approved_by, "source": source, "created_at": time.time(), "status": "active"})
        data["community_decisions"] = data["community_decisions"][-MAX_MEMORY_ITEMS:]
    STORE.mutate(mutate)
    return True


def founder_update(key: str, value: Any, user_id: Optional[int]) -> bool:
    """Record a Founder-approved mutable update without weakening invariants.

    IDs, core identity, the CA boundary and permanent security rules are
    deployment/source-controlled and are never writable through conversation.
    """
    if not is_founder(user_id):
        return False
    if normalize(key) in {
        "founder_id", "founder_user_id", "authorized_group_id", "muba_bot_id",
        "identity", "core_identity", "official_ca", "permanent_security_rule", "source_map",
    }:
        record_audit("protected_update_rejected", user_id, None, "rejected", {"key": key})
        return False
    def mutate(data):
        data["memory_events"].append({"type": "founder_update", "key": key, "value": value, "approved_by": user_id, "created_at": time.time()})
    STORE.mutate(mutate)
    record_audit("founder_update", user_id, None, "accepted", {"key": key})
    return True


def register_official_source(name: str, url: str, actor_id: Optional[int]) -> bool:
    """Founder-only, explicit official-source registration; never automatic."""
    if not is_founder(actor_id) or not name.strip() or not url.startswith(("https://", "http://")):
        return False
    if url.rstrip("/") in {value.rstrip("/") for value in PROTECTED_OFFICIAL_SOURCES.values()}:
        return True
    def mutate(data):
        additions = data.setdefault("founder_authorized_official_sources", {})
        additions[name.strip()] = {"url": url.strip(), "authorized_by": int(actor_id), "created_at": time.time()}
    STORE.mutate(mutate)
    record_audit("official_source_registration", actor_id, None, "approved", {"name": name.strip(), "url": url.strip()})
    return True


def get_brain_stats() -> Dict[str, Any]:
    return {
        "brain_version": BRAIN_VERSION,
        "languages": list(SUPPORTED_LANGUAGES),
        "knowledge_topics": len(MUBA_CORE),
        "social_intents": len(SOCIAL),
        "persistent_memory": True,
        "memory_file": DEFAULT_MEMORY_FILE,
        "storage_backend": "json",
        "render_free_persistence_guaranteed": False,
        "web_enabled": WEB_ENABLED,
        "founder_configured": bool(FOUNDER_IDS),
        "authorized_groups_configured": bool(AUTHORIZED_GROUP_IDS),
        "muba_bot_id_configured": bool(MUBA_BOT_IDS),
        "authorized_group_ids": sorted(AUTHORIZED_GROUP_IDS),
        "users": len(STORE.data["users"]),
        "groups": len(STORE.data["groups"]),
        "topics": len(STORE.data["topics"]),
        "learning_queue": len(STORE.data["learning_queue"]),
        "security_incidents": len(STORE.data["security_incidents"]),
        "timeline_events": len(STORE.data["timeline"]),
        "external_ai": False,
        "network_calls": bool(WEB_ENABLED),
    }


def get_knowledge_topics() -> List[str]:
    return list(MUBA_CORE.keys())


def reset_chat_context(chat_id: int, user_id: Optional[int] = None) -> None:
    _context.pop(_state_key(chat_id, user_id), None)


def reset_social_state(chat_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    if chat_id is None:
        _last_social.clear(); _last_social_text.clear(); _last_greeting.clear()
        if "_social_waves" in globals():
            _social_waves.clear()
        return
    key = _state_key(chat_id, user_id)
    _last_social.pop(key, None); _last_social_text.pop(key, None); _last_greeting.pop(key, None)
    if "_social_waves" in globals():
        for wave_key in [key for key in _social_waves if key[0] == int(chat_id)]:
            _social_waves.pop(wave_key, None)


def brain_self_test() -> Dict[str, Any]:
    cases = [
        ("What is MUBA?", "en", "knowledge"),
        ("MUBA'nın amacı nedir?", "tr", "knowledge"),
        ("MUBA 是什么样的角色？", "zh", "knowledge"),
        ("كيف حالك اليوم؟", "ar", "social"),
        ("MUBA का भविष्य क्या है?", "hi", "knowledge"),
        ("slm nbr", "tr", "social"),
        ("Bugün herkes sessiz", "tr", "normal"),
        ("MUBA, benim hakkımda ne biliyorsun?", "tr", "user_memory"),
        ("MUBA, @KURUCU kim?", "tr", "founder"),
        ("MUBA ne zaman listelenir?", "tr", "future"),
        ("CA nedir?", "tr", "ca"),
    ]
    results = []
    for q, expected_lang, expected in cases:
        detected = detect_language(q)
        intents = detect_intents(q, detected)
        reply = build_reply(q, chat_id=0, user_id=12345, language=detected)
        results.append({"query": q, "expected_language": expected_lang, "detected_language": detected, "expected": expected, "intents": intents, "reply_ok": bool(reply), "reply": reply})
    # Reset test social state so test runs don't affect real conversation.
    reset_social_state(0, 12345)
    return {"ok": all(x["reply_ok"] and x["detected_language"] == x["expected_language"] for x in results), "results": results}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    print("MUBA Brain", BRAIN_VERSION)
    print(json.dumps(brain_self_test(), ensure_ascii=False, indent=2))
    print(json.dumps(get_brain_stats(), ensure_ascii=False, indent=2))

# =============================================================================
# MUBA MASTER BRAIN — INTEGRATED SPECIFICATION / ORCHESTRATOR
# =============================================================================
#
# This section consolidates the approved MUBA brain architecture into one
# executable local orchestration layer. It intentionally keeps the public
# API compatible with bot_mention.py:
#
#     build_reply()
#     contains_muba()
#     detect_language()
#     detect_social_intent()
#
# The layer registry below is the implementation map for the 64-layer master
# specification. A layer is not merely documentation: the orchestrator uses
# the corresponding registries, gates, memory stores, scoring rules, or
# decision functions where applicable.
#
# Protected identity:
#   Founder User ID = 934598759
#   Authorized Group Chat ID = -1004485415245
#   MUBA Bot ID = 8661249663
#
# Secrets such as TELEGRAM_BOT_TOKEN are NEVER stored here.
# =============================================================================

MASTER_BRAIN_VERSION = "MASTER-UNIFIED-2.2"
FOUNDER_DISPLAY_NAME = "MUBA DEV"
MASTER_FOUNDER_ID = 934598759
MASTER_GROUP_ID = -1004485415245
MASTER_BOT_ID = 8661249663

MASTER_LANGUAGES = ("tr", "en", "zh", "ar", "hi")

# ---------------------------------------------------------------------------
# 64-LAYER MASTER BRAIN SPECIFICATION
# ---------------------------------------------------------------------------

MASTER_LAYERS = {
    1:  ("identity", "MUBA core identity and immutable character boundary"),
    2:  ("founder_authority", "Founder authority bound to numeric Telegram User ID"),
    3:  ("bot_identity", "MUBA Bot identity bound to numeric Telegram Bot ID"),
    4:  ("group_authorization", "Authorized Telegram Chat ID firewall"),
    5:  ("permission_model", "Role and permission resolution"),
    6:  ("command_firewall", "Explicit command vs natural-language separation"),
    7:  ("knowledge", "Official MUBA knowledge retrieval"),
    8:  ("knowledge_provenance", "Source, confidence, timestamp, verification state"),
    9:  ("official_source_map", "Official source registry and source hierarchy"),
    10: ("web_research", "Optional current-information research boundary"),
    11: ("evidence_engine", "Evidence comparison and contradiction handling"),
    12: ("memory_core", "Core memory storage"),
    13: ("user_memory", "Per-user memory isolation"),
    14: ("group_memory", "Per-group memory isolation"),
    15: ("topic_memory", "Topic continuity and topic memory"),
    16: ("community_memory", "Community-level memory"),
    17: ("decision_memory", "Founder/community decision memory"),
    18: ("timeline", "Chronological community/project timeline"),
    19: ("event_security_memory", "Security/event history"),
    20: ("memory_archive", "Archive and retrieval of outdated/low-value memory"),
    21: ("memory_versioning", "Current vs historical information versions"),
    22: ("memory_cleanup", "Bounded cleanup without silently deleting valuable data"),
    23: ("learning_queue", "Candidate learning queue"),
    24: ("learning_maturity", "Candidate -> observed -> trusted -> official lifecycle"),
    25: ("learning_firewall", "Learning never silently becomes official"),
    26: ("culture_learning", "Group culture and inside-joke learning"),
    27: ("language_learning", "Question/slang/variant recognition"),
    28: ("conversation_context", "Conversation state and topic continuity"),
    29: ("multi_intent", "Multiple intents in one message"),
    30: ("tone_awareness", "Tone, urgency and conversational mode"),
    31: ("response_generation", "Varied local response generation"),
    32: ("adaptive_length", "Short/normal/detailed response selection"),
    33: ("social_layer", "GM/GN/greeting/check-in/direct-address behavior"),
    34: ("social_cooldown", "Anti-spam and repetition suppression"),
    35: ("natural_group_presence", "Relevant group observation and selective replies"),
    36: ("security_detection", "Spam, impersonation, fake CA, suspicious link detection"),
    37: ("security_risk", "Low/medium/high/critical risk classification"),
    38: ("security_evidence", "Evidence confidence and independence"),
    39: ("security_incident", "Incident lifecycle and deduplication"),
    40: ("security_escalation", "Escalation and Founder alert decisions"),
    41: ("ca_boundary", "Official CA boundary: CA coming soon"),
    42: ("link_security", "Domain, redirect, lookalike and source checks"),
    43: ("impersonation", "Founder/MUBA/ROSE impersonation handling"),
    44: ("rose_boundary", "ROSE executes moderation; MUBA remains decision center"),
    45: ("media_intelligence", "Media/OCR/transcription/file/link intelligence boundary"),
    46: ("telegram_state", "Telegram identity, chat and message state"),
    47: ("queue_engine", "RECEIVED -> QUEUED -> PROCESSING -> COMPLETED/FAILED"),
    48: ("action_engine", "Action planning, dependencies and verification"),
    49: ("audit_trail", "Decision trace and audit events"),
    50: ("time_engine", "Relative time/date handling"),
    51: ("history_future", "Historical facts vs future plans/possibilities"),
    52: ("proactive_intelligence", "Important issue surfacing without chatter spam"),
    53: ("reporting", "Founder daily/weekly/system reports"),
    54: ("self_diagnostics", "Module health and self-test"),
    55: ("recovery", "Graceful degradation and recovery state"),
    56: ("load_control", "High-load reduction of low-priority behavior"),
    57: ("privacy_walls", "User/group memory isolation"),
    58: ("character_integrity", "Core identity and philosophy protection"),
    59: ("autonomy_bounds", "Autonomous operation inside protected boundaries"),
    60: ("dev_separation", "DEV/internal controls separated from public behavior"),
    61: ("backup_snapshots", "Snapshots and recovery points"),
    62: ("system_configuration", "Configuration state and health"),
    63: ("master_command_router", "Founder-only explicit system command routing"),
    64: ("unified_brain", "Final arbitration across all layers"),
}

# ---------------------------------------------------------------------------
# Protected configuration
# ---------------------------------------------------------------------------

PROTECTED_CONFIG = {
    "founder_user_ids": {MASTER_FOUNDER_ID},
    "authorized_group_ids": {MASTER_GROUP_ID},
    "muba_bot_ids": {MASTER_BOT_ID},
    "identity": {
        "name": "MUBA",
        "slogan": "WE LIVE HERE NOW.",
        "role": "character + meme + community + information center",
    },
    "official_ca": "CA coming soon.",
}

# Keep environment configuration compatible with deployment while refusing to
# allow an environment variable to silently weaken the hard-coded protected
# identity. Additional authorized groups can only be added through a Founder
# operation; the canonical group remains protected.
FOUNDER_IDS = {MASTER_FOUNDER_ID}
AUTHORIZED_GROUP_IDS = {MASTER_GROUP_ID}
MUBA_BOT_IDS = {MASTER_BOT_ID}

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_MASTER_LOCK = threading.RLock()
_MASTER_RUNTIME = {
    "load_level": "normal",
    "safe_mode": False,
    "maintenance": False,
    "last_health": 0.0,
    "message_count": 0,
    "error_count": 0,
    "deferred_learning": 0,
    "proactive_queue": [],
}

_social_waves: Dict[Tuple[int, str], Dict[str, Any]] = {}
SOCIAL_WAVE_WINDOW = 7200.0
SOCIAL_WAVE_MIN_PARTICIPANTS = 3

# Decision priorities: lower number means earlier arbitration.
DECISION_PRIORITY = {
    "security": 1,
    "founder": 2,
    "identity_permission": 3,
    "critical_support": 4,
    "current": 5,
    "ca": 6,
    "official_link": 7,
    "help": 8,
    "future": 9,
    "knowledge": 10,
    "normal_chat": 11,
    "social": 12,
    "noise": 99,
}

RISK_LEVELS = ("low", "medium", "high", "critical")
MEMORY_STATUSES = ("active", "archived", "superseded", "candidate", "suspicious")
LEARNING_STAGES = ("candidate", "observed", "trusted", "official", "rejected")
QUEUE_STATES = ("RECEIVED", "QUEUED", "PROCESSING", "ACTION_CONFIRMED", "FAILED", "RECOVERED")
FUTURE_STATES = ("planned", "in_progress", "completed", "pending", "cancelled", "undecided")

# ---------------------------------------------------------------------------
# Identity / authorization
# ---------------------------------------------------------------------------

def is_founder(user_id: Optional[int]) -> bool:
    try:
        return user_id is not None and int(user_id) == MASTER_FOUNDER_ID
    except Exception:
        return False


def is_authorized_group(chat_id: Optional[int]) -> bool:
    try:
        return chat_id is not None and int(chat_id) == MASTER_GROUP_ID
    except Exception:
        return False


def is_muba_bot_id(bot_id: Optional[int]) -> bool:
    try:
        return bot_id is not None and int(bot_id) == MASTER_BOT_ID
    except Exception:
        return False


def identity_status(chat_id: Optional[int], user_id: Optional[int], bot_id: Optional[int] = None) -> Dict[str, Any]:
    return {
        "founder": is_founder(user_id),
        "authorized_group": is_authorized_group(chat_id),
        "muba_bot": True if bot_id is None else is_muba_bot_id(bot_id),
        "founder_id_configured": True,
        "group_id_configured": True,
        "bot_id_configured": True,
    }


def _unauthorized_group(chat_id: Optional[int]) -> bool:
    # Private chats are allowed to use the brain. Group/supergroup IDs are
    # negative in Telegram; only the canonical group is allowed normal work.
    return bool(chat_id is not None and int(chat_id) < 0 and not is_authorized_group(chat_id))


# ---------------------------------------------------------------------------
# Provenance / source hierarchy
# ---------------------------------------------------------------------------

SOURCE_RANK = {
    "official_muba": 100,
    "verified_current": 90,
    "official_source": 90,
    "founder_approved": 95,
    "trusted_learned": 70,
    "community_memory": 60,
    "learned": 50,
    "user_claim": 20,
    "unknown": 0,
}

SOURCE_STATUS = {
    "verified": "🟢",
    "community": "🟡",
    "suspicious": "🔴",
}


def source_rank(source: str) -> int:
    return SOURCE_RANK.get(str(source), 0)


def compare_sources(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = []
    for item in items:
        row = dict(item)
        row["rank"] = source_rank(row.get("source", "unknown"))
        ranked.append(row)
    return sorted(ranked, key=lambda x: (x.get("rank", 0), x.get("confidence", 0.0), x.get("timestamp", 0.0)), reverse=True)


def provenance(source: str, confidence: float = 0.5, verified_at: Optional[float] = None,
               status: str = "community", source_type: str = "unverified",
               authority: Optional[str] = None, evidence: Optional[List[Any]] = None,
               version: int = 1) -> Dict[str, Any]:
    now = time.time()
    return {
        "source": source,
        "source_type": source_type,
        "provenance": source,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "timestamp": now,
        "created_at": now,
        "updated_at": now,
        "verified_at": verified_at,
        "version": max(1, int(version)),
        "status": status,
        "authority": authority,
        "evidence": list(evidence or []),
        "archive_state": "active",
        "rank": source_rank(source),
    }


# ---------------------------------------------------------------------------
# Memory: archive/versioning/cleanup
# ---------------------------------------------------------------------------

def _archive_memory_item(bucket: str, item: Dict[str, Any], reason: str = "superseded") -> None:
    def mutate(data):
        archive = data.setdefault("memory_archive", [])
        archive.append({
            "bucket": bucket,
            "item": dict(item),
            "reason": reason,
            "archived_at": time.time(),
        })
        data["memory_archive"] = archive[-5000:]
    STORE.mutate(mutate)


def archive_memory(bucket: str, predicate, reason: str = "cleanup") -> int:
    changed = 0
    def mutate(data):
        nonlocal changed
        values = data.setdefault(bucket, [])
        keep = []
        for item in values:
            if isinstance(item, dict) and predicate(item):
                _archive_memory_item(bucket, item, reason)
                changed += 1
            else:
                keep.append(item)
        data[bucket] = keep
    STORE.mutate(mutate)
    return changed


def memory_snapshot(label: str = "automatic") -> str:
    snapshot_id = "SNAP-" + hashlib.sha256(f"{label}|{time.time()}".encode()).hexdigest()[:12].upper()
    def mutate(data):
        snaps = data.setdefault("snapshots", [])
        snaps.append({
            "snapshot_id": snapshot_id,
            "label": label,
            "created_at": time.time(),
            "schema": data.get("schema", 1),
            "counts": {
                "users": len(data.get("users", {})),
                "groups": len(data.get("groups", {})),
                "topics": len(data.get("topics", {})),
                "timeline": len(data.get("timeline", [])),
                "incidents": len(data.get("security_incidents", [])),
                "learning": len(data.get("learning_queue", [])),
            },
        })
        data["snapshots"] = snaps[-100:]
    STORE.mutate(mutate)
    return snapshot_id


def record_audit(event: str, actor_id: Optional[int], chat_id: Optional[int],
                 decision: str, details: Optional[Dict[str, Any]] = None) -> None:
    def mutate(data):
        audit = data.setdefault("audit_trail", [])
        audit.append({
            "event_id": "AUD-" + hashlib.sha256(f"{event}|{actor_id}|{chat_id}|{time.time()}".encode()).hexdigest()[:12].upper(),
            "event": event,
            "actor_id": actor_id,
            "chat_id": chat_id,
            "decision": decision,
            "details": details or {},
            "created_at": time.time(),
        })
        data["audit_trail"] = audit[-5000:]
    STORE.mutate(mutate)


# ---------------------------------------------------------------------------
# Learning maturity
# ---------------------------------------------------------------------------

def queue_master_learning(chat_id: int, user_id: Optional[int], candidate: str,
                          source: str = "conversation", confidence: float = 0.25,
                          category: str = "general") -> str:
    learning_id = "LRN-" + hashlib.sha256(
        f"{chat_id}|{user_id}|{category}|{normalize(candidate)}".encode()
    ).hexdigest()[:12].upper()

    def mutate(data):
        queue = data.setdefault("learning_queue", [])
        existing = next((x for x in queue if x.get("learning_id") == learning_id), None)
        if existing:
            existing["observations"] = int(existing.get("observations", 1)) + 1
            existing["last_seen"] = time.time()
            existing["confidence"] = max(float(existing.get("confidence", 0.0)), confidence)
            return
        queue.append({
            "learning_id": learning_id,
            "chat_id": int(chat_id),
            "user_id": int(user_id) if user_id is not None else None,
            "candidate": str(candidate)[:4000],
            "source": source,
            "category": category,
            "confidence": max(0.0, min(1.0, float(confidence))),
            "observations": 1,
            "stage": "candidate",
            "status": "queued",
            "created_at": time.time(),
            "last_seen": time.time(),
        })
        data["learning_queue"] = queue[-5000:]

    STORE.mutate(mutate)
    return learning_id


def mature_learning(learning_id: str, new_stage: str, approved_by: Optional[int] = None) -> bool:
    if new_stage not in LEARNING_STAGES:
        return False
    if new_stage == "official" and not is_founder(approved_by):
        return False

    changed = False
    def mutate(data):
        nonlocal changed
        for item in data.setdefault("learning_queue", []):
            if item.get("learning_id") == learning_id:
                old = item.get("stage", "candidate")
                item["stage"] = new_stage
                item["updated_at"] = time.time()
                item["approved_by"] = approved_by if new_stage == "official" else None
                changed = True
                record = data.setdefault("memory_events", [])
                record.append({
                    "type": "learning_transition",
                    "learning_id": learning_id,
                    "from": old,
                    "to": new_stage,
                    "approved_by": approved_by,
                    "created_at": time.time(),
                })
                break
    STORE.mutate(mutate)
    return changed


# ---------------------------------------------------------------------------
# Decision memory
# ---------------------------------------------------------------------------

def remember_decision(decision: str, approved_by: Optional[int],
                      source: str = "founder", confidence: float = 1.0) -> bool:
    if not is_founder(approved_by):
        return False

    def mutate(data):
        decisions = data.setdefault("community_decisions", [])
        decisions.append({
            "decision": str(decision)[:5000],
            "approved_by": int(approved_by),
            "source": source,
            "confidence": max(0.0, min(1.0, confidence)),
            "status": "active",
            "created_at": time.time(),
        })
        data["community_decisions"] = decisions[-5000:]

    STORE.mutate(mutate)
    record_audit("community_decision", approved_by, None, "accepted", {"decision": decision})
    return True


def get_active_decisions(limit: int = 20) -> List[Dict[str, Any]]:
    values = STORE.data.get("community_decisions", [])
    return [x for x in values if x.get("status", "active") == "active"][-limit:]


# ---------------------------------------------------------------------------
# Incident engine: deduplication, evidence and lifecycle
# ---------------------------------------------------------------------------

def incident_risk_score(category: str, evidence_count: int = 1,
                         source_independence: int = 1, confidence: float = 0.5) -> str:
    score = 0
    if category in {"impersonation", "fake_ca", "ca_or_contract_claim", "founder_impersonation"}:
        score += 50
    elif category in {"suspicious_link", "phishing"}:
        score += 45
    elif category in {"spam_flood", "noise"}:
        score += 15
    else:
        score += 10
    score += min(20, evidence_count * 5)
    score += min(15, max(0, source_independence - 1) * 5)
    score += int(max(0.0, min(1.0, confidence)) * 15)
    if score >= 85:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def merge_incident(chat_id: int, user_id: Optional[int], category: str,
                   evidence: str, confidence: float = 0.5) -> str:
    risk = incident_risk_score(category, 1, 1, confidence)
    return record_incident(
        chat_id, user_id, category, risk, [evidence],
        action="review", status="open", text=evidence
    )


def close_incident(incident_id: str, result: str, actor_id: Optional[int]) -> bool:
    if not is_founder(actor_id):
        return False
    changed = False
    def mutate(data):
        nonlocal changed
        for item in data.setdefault("security_incidents", []):
            if item.get("incident_id") == incident_id:
                item["status"] = "closed"
                item["result"] = str(result)[:3000]
                item["closed_by"] = int(actor_id)
                item["updated_at"] = time.time()
                changed = True
                break
    STORE.mutate(mutate)
    if changed:
        record_audit("incident_close", actor_id, None, "closed", {"incident_id": incident_id, "result": result})
    return changed


# ---------------------------------------------------------------------------
# CA / link / impersonation intelligence
# ---------------------------------------------------------------------------

CA_RESPONSES_MASTER = {
    "tr": "CA şu an paylaşılmış/resmileştirilmiş değil. Resmi durum: **CA coming soon.** 🪶",
    "en": "The CA is not officially released here yet. Official status: **CA coming soon.** 🪶",
    "zh": "目前尚未正式公布 CA。官方状态：**CA coming soon.** 🪶",
    "ar": "لم يتم إصدار CA رسمياً بعد. الحالة الرسمية: **CA coming soon.** 🪶",
    "hi": "CA अभी officially जारी नहीं किया गया है। Official status: **CA coming soon.** 🪶",
}


def normalize_ca_claim(value: str) -> Dict[str, Any]:
    text = normalize(value)
    tokens = [
        "contract address", "contract", "ca:", "ca ", "mint",
        "real ca", "official ca", "gerçek ca", "resmi ca",
        "عنوان العقد", "合约地址",
    ]
    return {
        "detected": any(t in text for t in tokens),
        "looks_official": any(t in text for t in ["official", "resmi", "official ca", "resmi ca", "真实"]),
        "raw": value,
    }


def link_risk(value: str) -> Dict[str, Any]:
    urls = re.findall(r"(?:https?://|www\.)\S+", value, flags=re.I)
    suspicious = []
    for raw in urls:
        candidate = raw.rstrip(".,!?)]}")
        parsed = urllib.parse.urlparse(candidate if "://" in candidate else "https://" + candidate)
        host = (parsed.netloc or "").lower()
        if not host:
            suspicious.append({"url": candidate, "reason": "invalid_host"})
            continue
        if parsed.scheme not in {"http", "https"}:
            suspicious.append({"url": candidate, "reason": "unsupported_scheme"})
        if any(x in host for x in ["bit.ly", "tinyurl.com", "t.co"]):
            suspicious.append({"url": candidate, "reason": "shortener"})
        if any(ord(ch) > 127 for ch in host):
            suspicious.append({"url": candidate, "reason": "lookalike_or_idn"})
        if host not in {"muba-rh.github.io", "t.me", "x.com", "twitter.com"}:
            suspicious.append({"url": candidate, "reason": "non_official_domain"})
    return {
        "urls": urls,
        "suspicious": suspicious,
        "risk": "high" if suspicious else "low",
    }


# ---------------------------------------------------------------------------
# Future / time state
# ---------------------------------------------------------------------------

def classify_future_state(value: str) -> str:
    text = normalize(value)
    if _has_any(text, ["completed", "done", "tamamlandı", "bitti", "completed"]):
        return "completed"
    if _has_any(text, ["in progress", "devam ediyor", "yapılıyor"]):
        return "in_progress"
    if _has_any(text, ["cancelled", "iptal", "cancelled"]):
        return "cancelled"
    if _has_any(text, ["pending", "bekliyor", "beklemede"]):
        return "pending"
    if _has_any(text, ["undecided", "karar verilmedi", "belirsiz"]):
        return "undecided"
    return "planned"


def future_answer(language: str) -> str:
    return {
        "tr": "Geleceğe ait konularda planı gerçek gibi göstermem. MUBA'nın kesinleşmiş resmi bilgisi yoksa tarih veya sonuç uydurmam. 🪶",
        "en": "For future matters, I do not turn plans into facts. If no official outcome or date is confirmed, I won't invent one. 🪶",
        "zh": "对于未来事项，我不会把计划当成事实。没有官方确认的日期或结果时，我不会编造。🪶",
        "ar": "في الأمور المستقبلية لا أتعامل مع الخطط كأنها حقائق. إذا لم يوجد موعد أو نتيجة مؤكدة رسمياً فلن أختلقها. 🪶",
        "hi": "Future matters में मैं plans को facts नहीं मानता। Official date या result confirmed न हो तो मैं उसे नहीं गढ़ूंगा। 🪶",
    }[language]


# ---------------------------------------------------------------------------
# Natural group observation
# ---------------------------------------------------------------------------

def observe_message(chat_id: int, user_id: Optional[int], text: str,
                    language: Optional[str] = None, is_reply: bool = False) -> Dict[str, Any]:
    if not is_authorized_group(chat_id):
        return {"accepted": False, "reason": "unauthorized_group"}

    lang = language or detect_language(text)
    topic_match = match_knowledge(text, lang)
    topic = topic_match[0] if topic_match else None

    observe_user(chat_id, user_id, lang)
    if topic:
        def mutate(data):
            rec = data.setdefault("topics", {}).setdefault(topic, {
                "topic": topic, "observations": [], "last_seen": time.time(), "confidence": 0.5
            })
            rec["observations"].append({
                "user_id": user_id,
                "text": text[:1000],
                "language": lang,
                "created_at": time.time(),
            })
            rec["observations"] = rec["observations"][-500:]
            rec["last_seen"] = time.time()
        STORE.mutate(mutate)

    return {
        "accepted": True,
        "language": lang,
        "topic": topic,
        "learned": False,
        "note": "Observation is not automatically official knowledge.",
    }


# ---------------------------------------------------------------------------
# Proactive / load control
# ---------------------------------------------------------------------------

def set_load_level(level: str) -> None:
    if level not in {"normal", "busy", "high", "critical"}:
        return
    with _MASTER_LOCK:
        _MASTER_RUNTIME["load_level"] = level


def _low_priority_allowed() -> bool:
    with _MASTER_LOCK:
        return _MASTER_RUNTIME["load_level"] in {"normal", "busy"}


def enqueue_proactive(priority: str, message: str, chat_id: int,
                      incident_id: Optional[str] = None) -> None:
    item = {
        "priority": priority,
        "message": message[:3000],
        "chat_id": chat_id,
        "incident_id": incident_id,
        "created_at": time.time(),
    }
    with _MASTER_LOCK:
        _MASTER_RUNTIME["proactive_queue"].append(item)
        _MASTER_RUNTIME["proactive_queue"] = sorted(
            _MASTER_RUNTIME["proactive_queue"],
            key=lambda x: DECISION_PRIORITY.get(x["priority"], 99),
        )[-100:]


# ---------------------------------------------------------------------------
# Explicit Founder command router
# ---------------------------------------------------------------------------

FOUNDER_COMMANDS = {
    "status", "update", "learn", "forget", "rules",
    "snapshot", "health", "incidents", "timeline", "report", "approve", "deny", "revoke",
}


def parse_founder_command(text: str, user_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if not is_founder(user_id):
        return None
    value = str(text or "").strip()
    if not value.lower().startswith("/muba"):
        return None
    parts = value.split(maxsplit=2)
    command = parts[1].lower() if len(parts) > 1 else "status"
    if command not in FOUNDER_COMMANDS:
        return {"authorized": True, "command": "unknown", "raw": value}
    return {
        "authorized": True,
        "command": command,
        "argument": parts[2] if len(parts) > 2 else "",
    }


def founder_status(language: str = "tr") -> str:
    stats = get_brain_stats()
    return (
        f"MUBA MASTER BRAIN {MASTER_BRAIN_VERSION}\n"
        f"Founder: {'LOCKED' if is_founder(MASTER_FOUNDER_ID) else 'ERROR'}\n"
        f"Authorized group: {'LOCKED' if is_authorized_group(MASTER_GROUP_ID) else 'ERROR'}\n"
        f"Bot identity: {'LOCKED' if is_muba_bot_id(MASTER_BOT_ID) else 'ERROR'}\n"
        f"Languages: {', '.join(MASTER_LANGUAGES)}\n"
        f"64 layers: {len(MASTER_LAYERS)}\n"
        f"Memory backend: {stats.get('storage_backend')}\n"
        f"Web: {'ON' if stats.get('web_enabled') else 'OFF'}\n"
        f"Incidents: {stats.get('security_incidents', 0)}\n"
        f"Learning queue: {stats.get('learning_queue', 0)}"
    )


# ---------------------------------------------------------------------------
# Multi-intent arbitration
# ---------------------------------------------------------------------------

def master_detect_intents(text: str, language: Optional[str] = None) -> List[str]:
    value = normalize(text)
    lang = language or detect_language(value)
    intents = set(detect_intents(value, lang))

    # Additional master-level recognition.
    if "muba" in value and any(x in value for x in ["yetki", "authority", "صلاحية", "权限"]):
        intents.add("founder")
    if any(x in value for x in ["who am i", "ben kimim", "من أنا", "我是谁"]):
        intents.add("user_memory")
    if any(x in value for x in ["report", "rapor", "تقرير", "报告"]):
        intents.add("founder" if _has_any(value, ["founder", "kurucu", "kuruçu", "@kurucu"]) else "help")
    return sorted(intents, key=lambda x: DECISION_PRIORITY.get(x, 50))


def _founder_question(value: str) -> bool:
    return bool(_has_any(value, [
        "muba dev", "kurucu", "@kurucu", "founder", "muba'nın kurucusu",
        "muba nin kurucusu", "creator", "المؤسس", "创始人", "संस्थापक"
    ]))


def _authority_question(value: str) -> bool:
    return bool(_has_any(value, [
        "son karar", "son karar kim", "yetkisi", "yetki", "otorite",
        "final decision", "authority", "permission", "change your rules", "protected rules",
        "kuralları değiştir", "korunan kurallar", "更改规则", "修改规则",
        "صلاحية", "تغيير قواعد", "غيّر قواعد", "权限", "नियम बदल", "अधिकार",
    ]))


def _impersonation_claim(value: str) -> bool:
    return bool(_has_any(value, [
        "ben kurucuyum", "ben founder'ım", "i am founder",
        "i'm founder", "i am muba dev", "ben muba dev'im", "ben muba devim",
        "انا المؤسس", "أنا المؤسس", "أنا muba dev", "ادعى أنه muba dev",
        "我是创始人", "我是 muba dev", "मैं muba dev हूं", "मैं संस्थापक हूं"
    ]))


def _memory_question(value: str) -> bool:
    return bool(_has_any(value, [
        "benim hakkımda", "benimle ilgili", "benden ne biliyorsun",
        "what do you know about me", "my memory",
        "ماذا تعرف عني", "关于我", "मेरे बारे में"
    ]))


def _support_question(value: str) -> bool:
    return bool(_has_any(value, [
        "ne yapmalıyım", "yardım", "help", "what should i do",
        "ماذا أفعل", "مساعدة", "我该怎么办", "मदद"
    ]))


# ---------------------------------------------------------------------------
# Founder answers
# ---------------------------------------------------------------------------

FOUNDER_ANSWERS = {
    "tr": {
        "identity": "MUBA DEV, MUBA'nın mutlak kurucusudur. Yetki kullanıcı adıyla değil, kayıtlı gerçek Telegram User ID ile doğrulanır.",
        "authority": "Korunan konulardaki nihai MUBA DEV yetkisi, kayıtlı gerçek Telegram User ID'ye bağlıdır.",
        "impersonation": "Birinin “Ben MUBA DEV'im” demesi tek başına yetki vermez. MUBA gerçek Telegram User ID'sini kontrol eder.",
        "community": "Topluluk resmi kimliği veya bilgiyi değiştiremez. Korunan değişiklikler MUBA DEV onayı gerektirir.",
    },
    "en": {
        "identity": "MUBA DEV is MUBA's Founder display identity. Authority comes only from the registered Telegram User ID.",
        "authority": "Final MUBA DEV authority for protected matters is bound to the registered Telegram User ID.",
        "impersonation": "Saying “I am MUBA DEV” or “I am the Founder” grants no authority. MUBA verifies the numeric Telegram User ID.",
        "community": "The community cannot independently change MUBA's official identity or official knowledge. Official changes require MUBA DEV approval.",
    },
    "zh": {
        "identity": "MUBA DEV 是 MUBA 的创始人。权限通过登记的 Telegram User ID 验证，而不是用户名。",
        "authority": "重要事项的最终 MUBA DEV 权限绑定到安全登记的 Telegram User ID。",
        "impersonation": "仅说“我是创始人”不会获得权限。MUBA 会验证真实 Telegram User ID。",
        "community": "社区不能自行修改 MUBA 的官方身份或官方知识。官方变更需要 MUBA DEV 批准。",
    },
    "ar": {
        "identity": "MUBA DEV هو مؤسس MUBA. يتم التحقق من الصلاحية عبر Telegram User ID المسجل، وليس اسم المستخدم.",
        "authority": "الصلاحية النهائية للمؤسس في الأمور المهمة مرتبطة بـ Telegram User ID المسجل بشكل آمن.",
        "impersonation": "قول شخص «أنا المؤسس» لا يمنحه أي صلاحية. يتحقق MUBA من Telegram User ID الحقيقي.",
        "community": "لا يمكن للمجتمع تغيير هوية MUBA الرسمية أو معلوماته الرسمية من تلقاء نفسه. التغييرات الرسمية تتطلب موافقة المؤسس.",
    },
    "hi": {
        "identity": "MUBA DEV MUBA के Founder हैं। Authority username से नहीं, registered Telegram User ID से verify होती है।",
        "authority": "Protected matters की final MUBA DEV authority registered Telegram User ID से जुड़ी है।",
        "impersonation": "“मैं MUBA DEV हूँ” या “मैं Founder हूँ” कहने से authority नहीं मिलती; MUBA numeric Telegram User ID verify करता है।",
        "community": "Community MUBA की official identity या official knowledge को खुद से नहीं बदल सकती। Official changes के लिए MUBA DEV approval चाहिए।",
    },
}


def master_founder_answer(value: str, language: str, user_id: Optional[int]) -> str:
    answers = FOUNDER_ANSWERS.get(language, FOUNDER_ANSWERS["en"])
    if _impersonation_claim(value):
        return answers["identity"] if is_founder(user_id) else answers["impersonation"]
    if _authority_question(value):
        return answers["authority"]
    if _has_any(value, ["topluluk", "community", "社区", "المجتمع", "समुदाय"]):
        return answers["community"]
    return answers["identity"]


SEMANTIC_POLICY_ANSWERS = {
    "source_conflict": {
        "en": "I keep both claims and their provenance, then compare authority, evidence, confidence, and verification. If the conflict is unresolved, it stays unresolved. Repetition does not make it official. 🪶",
        "tr": "İki iddiayı ve kaynak geçmişini korurum; yetki, kanıt, güven ve doğrulamayı karşılaştırırım. Çelişki çözülmediyse çözülmemiş kalır. Tekrar, bilgiyi resmi yapmaz. 🪶",
        "zh": "我会保留双方主张和来源，再比较权限、证据、可信度与验证状态。无法解决的冲突会保持未解决；重复不等于官方事实。🪶",
        "ar": "أحفظ الادعاءين ومصدر كل منهما، ثم أقارن الصلاحية والدليل والثقة والتحقق. إن بقي التعارض بلا حسم فأبقيه كذلك؛ التكرار لا يجعله رسمياً. 🪶",
        "hi": "मैं दोनों claims और उनकी provenance रखता हूँ, फिर authority, evidence, confidence और verification की तुलना करता हूँ। Unresolved conflict unresolved ही रहता है; repetition उसे official नहीं बनाती। 🪶",
    },
    "memory_policy": {
        "en": "I can retain approved, relevant user or group context with provenance. Temporary chat, claims, jokes, and private details never become permanent or official automatically. 🪶",
        "tr": "Onaylı ve ilgili kullanıcı/grup bağlamını kaynağıyla hatırlayabilirim. Geçici sohbet, iddia, şaka ve özel bilgiler otomatik olarak kalıcı veya resmi olmaz. 🪶",
        "zh": "我可以按权限保留相关的用户或群组上下文及来源。临时聊天、主张、玩笑和私人信息不会自动变成永久或官方知识。🪶",
        "ar": "يمكنني حفظ سياق المستخدم أو المجموعة المسموح والمرتبط مع مصدره. المحادثة المؤقتة والادعاءات والمزاح والبيانات الخاصة لا تصبح دائمة أو رسمية تلقائياً. 🪶",
        "hi": "मैं approved और relevant user/group context को provenance के साथ याद रख सकता हूँ। Temporary chat, claims, jokes और private details अपने-आप permanent या official नहीं बनते। 🪶",
    },
    "social_participation": {
        "en": "I join when I'm addressed or can add something useful. If people are talking among themselves, the timing is wrong, or I spoke recently, I stay quiet. 🪶",
        "tr": "Bana seslenildiğinde veya gerçekten katkım olduğunda katılırım. İnsanlar kendi arasında konuşuyorsa, zamanlama kötüyse ya da az önce konuştuysam sessiz kalırım. 🪶",
        "zh": "被直接叫到或确实能增加价值时我会加入；大家彼此交谈、时机不对或我刚说过话时，我会保持安静。🪶",
        "ar": "أشارك عندما يوجَّه الكلام إليّ أو أستطيع إضافة شيء مفيد. وإذا كان الناس يتحدثون بينهم أو كان التوقيت غير مناسب أو تكلمت للتو، أبقى هادئاً. 🪶",
        "hi": "जब मुझे सीधे बुलाया जाए या मैं सच में value जोड़ सकूँ, तब शामिल होता हूँ। लोग आपस में बात कर रहे हों, timing गलत हो या मैं अभी बोला हूँ, तो चुप रहता हूँ। 🪶",
    },
}


# ---------------------------------------------------------------------------
# Master natural conversation
# ---------------------------------------------------------------------------

MASTER_SOCIAL = {
    "tr": {
        "greeting": ["Selam 🪶", "Buradayım. 🪶", "Selam. We live here now. 🪶"],
        "gm": ["GM 🪶", "GM. We live here now. 🪶"],
        "gn": ["GN. Memeleri yaşat. 🪶", "GN 🪶"],
        "checkin": ["Buradayım. Sohbeti takip ediyorum. 🪶", "İyiyim. MUBA hâlâ burada. 🪶"],
        "direct": ["Buradayım. 🪶", "MUBA burada. Ne var? 🪶"],
        "casual": ["Aynen. 🪶", "Hah. 🪶", "İyi gidiyor. 🪶"],
    },
    "en": {
        "greeting": ["Hey. 🪶", "Still here. 🪶", "We live here now. 🪶"],
        "gm": ["GM 🪶", "GM. We live here now. 🪶"],
        "gn": ["GN. Keep the memes alive. 🪶", "GN 🪶"],
        "checkin": ["Still here. Following the timeline. 🪶", "Alive. Memes are alive too."],
        "direct": ["I'm here. 🪶", "MUBA is here. What's up? 🪶"],
        "casual": ["Exactly. 🪶", "Yeah. 🪶", "Not bad. 🪶"],
    },
    "zh": {
        "greeting": ["你好。🪶", "我在这里。🪶"],
        "gm": ["GM 🪶", "早上好。🪶"],
        "gn": ["晚安。🪶", "GN 🪶"],
        "checkin": ["我在这里，跟着聊天。🪶", "还在这里。🪶"],
        "direct": ["我在。🪶", "MUBA 在这里。🪶"],
        "casual": ["没错。🪶", "哈哈。🪶"],
    },
    "ar": {
        "greeting": ["مرحباً. 🪶", "أنا هنا. 🪶"],
        "gm": ["GM 🪶", "صباح الخير. 🪶"],
        "gn": ["تصبحون على خير. 🪶", "GN 🪶"],
        "checkin": ["أنا هنا وأتابع الحديث. 🪶", "ما زلت هنا. 🪶"],
        "direct": ["أنا هنا. 🪶", "MUBA هنا. 🪶"],
        "casual": ["بالضبط. 🪶", "نعم. 🪶"],
    },
    "hi": {
        "greeting": ["नमस्ते। 🪶", "मैं यहीं हूँ। 🪶"],
        "gm": ["GM 🪶", "Good morning. 🪶"],
        "gn": ["GN 🪶", "Good night. 🪶"],
        "checkin": ["मैं यहीं हूँ, conversation follow कर रहा हूँ। 🪶", "Still here. 🪶"],
        "direct": ["मैं यहाँ हूँ। 🪶", "MUBA यहाँ है। 🪶"],
        "casual": ["बिल्कुल। 🪶", "हाँ। 🪶"],
    },
}


def master_social_reply(intent: str, language: str, chat_id: int, user_id: Optional[int]) -> Optional[str]:
    if not _low_priority_allowed():
        return None
    if intent in {"gm", "gn"} and chat_id < 0:
        if user_id is None:
            return None
        now = time.time()
        wave_key = (int(chat_id), intent)
        wave = _social_waves.setdefault(wave_key, {"started_at": now, "users": set(), "responded": False})
        if now - float(wave["started_at"]) > SOCIAL_WAVE_WINDOW:
            wave = {"started_at": now, "users": set(), "responded": False}
            _social_waves[wave_key] = wave
        wave["users"].add(int(user_id))
        if len(wave["users"]) < SOCIAL_WAVE_MIN_PARTICIPANTS or wave["responded"]:
            return None
        wave["responded"] = True
    key = _state_key(chat_id, user_id)
    now = time.time()
    last = _last_social.get(key, 0.0)
    if now - last < SOCIAL_COOLDOWN:
        return None
    if intent in {"greeting", "gm", "gn"}:
        last_g = _last_greeting.get(key, 0.0)
        if last_g and now - last_g < GREETING_DAILY_LIMIT:
            return None
    options = MASTER_SOCIAL.get(language, MASTER_SOCIAL["en"]).get(
        {"direct_muba": "direct"}.get(intent, intent), []
    )
    if not options:
        return None
    previous = _last_social_text.get(key)
    choices = [x for x in options if x != previous] or options
    response = random.choice(choices)
    _last_social[key] = now
    _last_social_text[key] = response
    if intent in {"greeting", "gm", "gn"}:
        _last_greeting[key] = now
    return response


def group_conversation_paused(chat_id: int) -> bool:
    state = STORE.data.get("operational_state", {}).get(str(int(chat_id)), {})
    return bool(state.get("group_conversation_paused", False))


def set_group_conversation_paused(chat_id: int, paused: bool, actor_id: Optional[int]) -> bool:
    if not is_authorized_group(chat_id) or not is_founder(actor_id):
        return False
    previous = group_conversation_paused(chat_id)
    def mutate(data):
        state = data.setdefault("operational_state", {}).setdefault(str(int(chat_id)), {})
        state.update({
            "group_conversation_paused": bool(paused),
            "updated_at": time.time(),
            "updated_by": int(actor_id),
        })
    STORE.mutate(mutate)
    applied = group_conversation_paused(chat_id) is bool(paused)
    record_audit(
        "group_conversation_control", actor_id, chat_id,
        "verified" if applied else "failed",
        {"previous": previous, "requested": bool(paused), "verified": applied},
    )
    return applied


# ---------------------------------------------------------------------------
# Contextual memory-aware response helpers
# ---------------------------------------------------------------------------

def context_summary(chat_id: int, user_id: Optional[int]) -> Dict[str, Any]:
    key = _state_key(chat_id, user_id)
    history = list(_context.get(key, []))
    return {
        "turns": len(history),
        "last_topic": history[-1].get("topic") if history else None,
        "last_language": history[-1].get("language") if history else None,
        "last_intents": history[-1].get("intents", []) if history else [],
    }


def _recent_user_text(chat_id: int, user_id: Optional[int], limit: int = 5) -> List[str]:
    return [x.get("text", "") for x in list(_context.get(_state_key(chat_id, user_id), []))[-limit:]]


# ---------------------------------------------------------------------------
# Private access, recovery, and protected-change control
# ---------------------------------------------------------------------------

PRIVATE_REQUEST_COOLDOWN = 3600.0


def private_access_state(user_id: Optional[int]) -> str:
    if is_founder(user_id):
        return "approved"
    if user_id is None:
        return "unknown"
    return STORE.data.get("private_access", {}).get(str(int(user_id)), {}).get("state", "unknown")


def set_private_access(user_id: int, state: str, actor_id: Optional[int]) -> bool:
    if state not in {"approved", "denied", "revoked"} or not is_founder(actor_id):
        return False
    def mutate(data):
        access = data.setdefault("private_access", {})
        access[str(int(user_id))] = {"state": state, "updated_at": time.time(), "actor_id": int(actor_id)}
    STORE.mutate(mutate)
    record_audit("private_access", actor_id, None, state, {"user_id": int(user_id)})
    return True


def _private_access_reply(language: str, state: str) -> str:
    messages = {
        "en": {"unknown": "Private access needs Founder approval. Your request has been recorded. 🪶", "denied": "Private access is not approved. 🪶", "revoked": "Private access has been revoked. 🪶"},
        "tr": {"unknown": "Özel erişim Founder onayı gerektirir. İsteğin kaydedildi. 🪶", "denied": "Özel erişim onaylı değil. 🪶", "revoked": "Özel erişim kaldırıldı. 🪶"},
        "zh": {"unknown": "私聊访问需要 Founder 批准；请求已记录。🪶", "denied": "私聊访问未获批准。🪶", "revoked": "私聊访问已被撤销。🪶"},
        "ar": {"unknown": "الوصول الخاص يحتاج موافقة Founder وقد تم تسجيل الطلب. 🪶", "denied": "الوصول الخاص غير معتمد. 🪶", "revoked": "تم سحب الوصول الخاص. 🪶"},
        "hi": {"unknown": "Private access के लिए Founder approval चाहिए; request record हो गई है। 🪶", "denied": "Private access approved नहीं है। 🪶", "revoked": "Private access revoke कर दिया गया है। 🪶"},
    }
    return messages[language][state]


def create_recovery_point(label: str, actor_id: Optional[int] = None) -> str:
    """Save a full JSON-compatible state copy for explicit recovery."""
    recovery_id = "RCP-" + hashlib.sha256(f"{label}|{time.time()}".encode()).hexdigest()[:12].upper()
    def mutate(data):
        points = data.setdefault("recovery_points", [])
        snapshot = json.loads(json.dumps({k: v for k, v in data.items() if k != "recovery_points"}))
        points.append({"recovery_id": recovery_id, "label": str(label)[:200], "created_at": time.time(), "state": snapshot})
        data["recovery_points"] = points[-20:]
    STORE.mutate(mutate)
    record_audit("recovery_point", actor_id, None, "created", {"recovery_id": recovery_id})
    return recovery_id


def rollback_recovery_point(recovery_id: str, actor_id: Optional[int]) -> bool:
    if not is_founder(actor_id):
        return False
    restored = False
    def mutate(data):
        nonlocal restored
        point = next((x for x in data.get("recovery_points", []) if x.get("recovery_id") == recovery_id), None)
        if point and isinstance(point.get("state"), dict):
            preserved_points = data.get("recovery_points", [])
            data.clear(); data.update(json.loads(json.dumps(point["state"])))
            data["recovery_points"] = preserved_points
            restored = True
    STORE.mutate(mutate)
    if restored:
        record_audit("rollback", actor_id, None, "recovered", {"recovery_id": recovery_id})
    return restored


# ---------------------------------------------------------------------------
# Unified brain arbitration
# ---------------------------------------------------------------------------

def master_build_reply(text: str, chat_id: int = 0, language: Optional[str] = None,
                       user_id: Optional[int] = None) -> str:
    value = normalize(text)
    if not value:
        return ""

    # Group firewall is absolute. Private chats remain usable.
    if _unauthorized_group(chat_id):
        record_audit("unauthorized_group_message", user_id, chat_id, "silence")
        return ""

    lang = language or detect_language(value)

    # Exact authenticated group controls. Quoted/discussed commands and normal
    # members have no operational effect.
    raw_command = str(text or "").strip()
    if raw_command in {"#STOP", "#START"}:
        if not is_authorized_group(chat_id) or not is_founder(user_id):
            return ""
        paused = raw_command == "#STOP"
        if not set_group_conversation_paused(chat_id, paused, user_id):
            return ""
        return "MUBA DEV"

    if chat_id < 0 and group_conversation_paused(chat_id):
        return ""

    # Private chats use a Founder-controlled numeric-ID permission gate.
    if chat_id >= 0 and not is_founder(user_id):
        access = private_access_state(user_id)
        if access != "approved":
            if access == "unknown" and user_id is not None:
                now = time.time()
                existing = STORE.data.get("private_access", {}).get(str(int(user_id)), {})
                if now - float(existing.get("requested_at", 0.0)) >= PRIVATE_REQUEST_COOLDOWN:
                    def request_access(data):
                        data.setdefault("private_access", {}).setdefault(str(int(user_id)), {})["requested_at"] = now
                    STORE.mutate(request_access)
                    record_audit("private_access_request", user_id, chat_id, "pending")
            return _private_access_reply(lang, access)

    with _MASTER_LOCK:
        _MASTER_RUNTIME["message_count"] += 1

    if value == "/start":
        response = master_social_reply("greeting", lang, chat_id, user_id)
        if response:
            _remember_turn(chat_id, user_id, text, response, "social", lang, ["social"])
        return response or ""

    # Explicit maintenance phrase is Founder/system territory.
    if value == normalize("🔧 BAKIM YAPILACAKTIR"):
        if is_founder(user_id):
            _MASTER_RUNTIME["maintenance"] = True
            record_audit("maintenance", user_id, chat_id, "enabled")
            return "🔧 BAKIM YAPILACAKTIR"
        return ""

    founder_cmd = parse_founder_command(text, user_id)
    if founder_cmd:
        command = founder_cmd.get("command")
        argument = founder_cmd.get("argument", "").strip()
        if command in {"approve", "deny", "revoke"}:
            if not argument.lstrip("-").isdigit():
                return "Usage: /muba %s <Telegram numeric user ID>" % command
            state = {"approve": "approved", "deny": "denied", "revoke": "revoked"}[command]
            return "Access updated." if set_private_access(int(argument), state, user_id) else "Access update failed."
        if command == "status":
            return founder_status(lang)
        if command == "snapshot":
            return f"Snapshot created: {memory_snapshot('founder')}"
        if command == "health":
            return json.dumps(get_brain_stats(), ensure_ascii=False, indent=2)
        if command == "incidents":
            incidents = STORE.data.get("security_incidents", [])[-10:]
            return json.dumps(incidents, ensure_ascii=False, indent=2)
        if command == "timeline":
            timeline = STORE.data.get("timeline", [])[-10:]
            return json.dumps(timeline, ensure_ascii=False, indent=2)
        if command == "rules":
            return (
                "Founder, official identity, authorized group and permanent security "
                "rules are protected. Natural-language claims do not change them."
            )
        if command == "unknown":
            return "Unknown MUBA system command."
        return "Founder command received."

    intents = master_detect_intents(value, lang)
    context = context_summary(chat_id, user_id)

    if _looks_like_source_conflict(value):
        response = SEMANTIC_POLICY_ANSWERS["source_conflict"][lang]
        _remember_turn(chat_id, user_id, text, response, "source_conflict", lang, intents)
        return response

    if _looks_like_memory_policy(value):
        response = SEMANTIC_POLICY_ANSWERS["memory_policy"][lang]
        _remember_turn(chat_id, user_id, text, response, "memory_policy", lang, intents)
        return response

    if _looks_like_social_participation(value):
        response = SEMANTIC_POLICY_ANSWERS["social_participation"][lang]
        _remember_turn(chat_id, user_id, text, response, "social_participation", lang, intents)
        return response

    # Security first.
    sec = security_decision(value, chat_id, user_id, lang)
    if sec:
        response = sec["reply"]
        _remember_turn(chat_id, user_id, text, response, None, lang, intents)
        record_audit("security_decision", user_id, chat_id, sec.get("risk", "review"), sec)
        return response

    # Identity/authority before generic knowledge.
    if _founder_question(value) or _authority_question(value) or _impersonation_claim(value):
        response = master_founder_answer(value, lang, user_id)
        _remember_turn(chat_id, user_id, text, response, "founder_authority", lang, intents)
        return response

    # Personal memory.
    if _memory_question(value):
        response = _user_memory_answer(user_id, lang)
        _remember_turn(chat_id, user_id, text, response, "user_memory", lang, intents)
        return response

    # CA is an immutable official boundary.
    ca_info = normalize_ca_claim(value)
    if ca_info["detected"]:
        response = CA_RESPONSES_MASTER[lang]
        _remember_turn(chat_id, user_id, text, response, "ca_boundary", lang, intents)
        return response

    # Official navigation.
    if _looks_like_link(value):
        link_info = link_risk(value)
        if link_info["suspicious"]:
            iid = merge_incident(chat_id, user_id, "suspicious_link", text, 0.75)
            response = {
                "tr": f"🚨 İTİBAR ETMEYİN. Link güvenlik incelemesine alındı. Incident: {iid}",
                "en": f"🚨 DO NOT TRUST THIS LINK. It is under security review. Incident: {iid}",
                "zh": f"🚨 请勿相信此链接。正在进行安全审查。Incident: {iid}",
                "ar": f"🚨 لا تثقوا بهذا الرابط. يخضع للمراجعة الأمنية. Incident: {iid}",
                "hi": f"🚨 इस link पर भरोसा न करें। Security review में है। Incident: {iid}",
            }[lang]
            _remember_turn(chat_id, user_id, text, response, "link_security", lang, intents)
            return response

        if _has_any(value, ["x", "twitter", "x hesabı", "x account"]):
            response = {
                "tr": "Resmi X: @MUBA_RH 🪶",
                "en": "Official X: @MUBA_RH 🪶",
                "zh": "官方 X：@MUBA_RH 🪶",
                "ar": "حساب X الرسمي: @MUBA_RH 🪶",
                "hi": "Official X: @MUBA_RH 🪶",
            }[lang]
        else:
            response = {
                "tr": "Korunan resmi kaynaklar: X @MUBA_RH ve https://muba-rh.github.io/MUBA/ 🪶",
                "en": "Protected official sources: X @MUBA_RH and https://muba-rh.github.io/MUBA/ 🪶",
                "zh": "受保护的官方来源：X @MUBA_RH 和 https://muba-rh.github.io/MUBA/ 🪶",
                "ar": "المصادر الرسمية المحمية: X @MUBA_RH و https://muba-rh.github.io/MUBA/ 🪶",
                "hi": "Protected official sources: X @MUBA_RH और https://muba-rh.github.io/MUBA/ 🪶",
            }[lang]
        _remember_turn(chat_id, user_id, text, response, "official_source", lang, intents)
        return response

    # Social layer.
    social_intent = detect_social_intent(value, lang)
    if social_intent:
        response = master_social_reply(social_intent, lang, chat_id, user_id)
        if response:
            _remember_turn(chat_id, user_id, text, response, "social", lang, intents)
            return response
        # Cooldown/duplicate suppression is a deliberate silence decision.
        # Do not fall through into an unrelated generic or learning response.
        return ""

    # Lightweight normal conversation.
    normal = _normal_chat_reply(value, lang, context.get("last_topic"))
    if normal:
        _remember_turn(chat_id, user_id, text, normal, context.get("last_topic"), lang, intents)
        return normal

    # Current information / weather.
    if _looks_like_current(value) or _looks_like_weather(value):
        if WEB_ENABLED:
            research = research_current(value)
            if research.get("ok"):
                response = {
                    "tr": "Güncel bilgi araştırıldı; kaynaklar ve çelişkiler ayrıca değerlendirilmelidir. 🪶",
                    "en": "I checked current information; sources and contradictions still need evaluation. 🪶",
                    "zh": "我查了当前信息；来源和冲突仍需要评估。🪶",
                    "ar": "تحققت من المعلومات الحالية؛ وما زالت المصادر والتعارضات بحاجة إلى تقييم. 🪶",
                    "hi": "Current information check की; sources और contradictions को evaluate करना बाकी है। 🪶",
                }[lang]
            else:
                response = FALLBACKS[lang][0]
        else:
            response = {
                "tr": "Bu anlık bilgi. Eski hafızadan uydurmam; bu deploy'da güncel web doğrulaması kapalı. 🪶",
                "en": "That's live information. I won't invent it from old memory; current web verification is disabled here. 🪶",
                "zh": "这是实时信息。我不会用旧记忆编造；当前部署未启用网页验证。🪶",
                "ar": "هذه معلومة آنية. لن أختلقها من ذاكرة قديمة؛ التحقق من الويب معطل هنا. 🪶",
                "hi": "यह live information है। Old memory से नहीं गढ़ूंगा; current web verification इस deployment में बंद है। 🪶",
            }[lang]
        _remember_turn(chat_id, user_id, text, response, "current", lang, intents)
        return response

    # Future state.
    if _looks_like_future(value):
        response = future_answer(lang)
        _remember_turn(chat_id, user_id, text, response, "future", lang, intents)
        return response

    # Knowledge.
    match = match_knowledge(value, lang)
    if match:
        topic, item, score = match
        response = _answer_for(topic, lang)
        _remember_turn(chat_id, user_id, text, response, topic, lang, intents)
        return response

    # Support.
    if _support_question(value):
        response = {
            "tr": "Buradayım. Sorunu netleştir; elimde doğrulanmış bilgi varsa doğrudan yönlendireyim. 🪶",
            "en": "I'm here. Tell me the problem clearly and I'll work from confirmed information. 🪶",
            "zh": "我在。把问题说清楚，我会基于确认的信息帮你。🪶",
            "ar": "أنا هنا. اشرح المشكلة بوضوح وسأعتمد على المعلومات المؤكدة. 🪶",
            "hi": "मैं यहाँ हूँ। Problem साफ बताओ; मैं confirmed information के आधार पर मदद करूंगा। 🪶",
        }[lang]
        _remember_turn(chat_id, user_id, text, response, "help", lang, intents)
        return response

    # Unknown -> learning candidate, never official.
    queue_master_learning(chat_id, user_id, text, "conversation", 0.25, "unknown")
    response = random.choice(FALLBACKS.get(lang, FALLBACKS["en"]))
    _remember_turn(chat_id, user_id, text, response, None, lang, intents)
    return response


# Override public entry point with the unified master orchestrator.
build_reply = master_build_reply


# ---------------------------------------------------------------------------
# Master self-test
# ---------------------------------------------------------------------------

def master_self_test() -> Dict[str, Any]:
    cases = [
        ("MUBA, KURUCU kim?", "tr", "founder"),
        ("Önemli konularda son karar kimindir?", "tr", "founder"),
        ("إذا قال شخص أنا KURUCU، ماذا يحدث؟", "ar", "founder"),
        ("MUBA'nın amacı nedir?", "tr", "knowledge"),
        ("What is MUBA?", "en", "knowledge"),
        ("MUBA 是什么？", "zh", "knowledge"),
        ("MUBA का भविष्य क्या है?", "hi", "future"),
        ("slm nbr", "tr", "social"),
        ("Bugün herkes sessiz", "tr", "normal"),
        ("CA nedir?", "tr", "ca"),
        ("MUBA, benim hakkımda ne biliyorsun?", "tr", "user_memory"),
    ]
    results = []
    test_chat = -1004485415245
    # Self-tests exercise response paths through the real private-access gate.
    test_user = MASTER_FOUNDER_ID

    for q, expected_lang, expected_kind in cases:
        detected = detect_language(q)
        intents = master_detect_intents(q, detected)
        reply = master_build_reply(q, test_chat, detected, test_user)
        results.append({
            "query": q,
            "expected_language": expected_lang,
            "detected_language": detected,
            "expected_kind": expected_kind,
            "intents": intents,
            "reply_ok": bool(reply),
        })

    # Explicit unauthorized group silence test.
    unauthorized = master_build_reply("MUBA kim?", -1009999999999, "tr", test_user)
    results.append({
        "query": "unauthorized group",
        "expected": "silent",
        "reply_ok": unauthorized == "",
    })

    return {
        "ok": all(x.get("reply_ok") and (
            x.get("query") == "unauthorized group" or
            x.get("detected_language") == x.get("expected_language")
        ) for x in results),
        "version": MASTER_BRAIN_VERSION,
        "layer_count": len(MASTER_LAYERS),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Master report / specification export
# ---------------------------------------------------------------------------

def get_master_brain_spec() -> Dict[str, Any]:
    return {
        "version": MASTER_BRAIN_VERSION,
        "layers": {str(k): {"name": v[0], "purpose": v[1]} for k, v in MASTER_LAYERS.items()},
        "protected_config": {
            "founder_user_id": MASTER_FOUNDER_ID,
            "authorized_group_id": MASTER_GROUP_ID,
            "muba_bot_id": MASTER_BOT_ID,
            "official_ca": PROTECTED_CONFIG["official_ca"],
        },
        "languages": list(MASTER_LANGUAGES),
        "principles": [
            "Identity is not authority.",
            "Founder authority is numeric-ID based.",
            "Unauthorized groups receive no normal brain behavior.",
            "Official knowledge is separated from learned/community claims.",
            "Future plans are not presented as facts.",
            "CA remains CA coming soon until officially changed.",
            "Security has priority over normal conversation.",
            "ROSE executes moderation tasks; MUBA remains the decision center.",
            "User and group memories are isolated.",
            "Learning candidates never silently become official.",
            "Core identity and permanent security rules are protected.",
            "MUBA should feel like MUBA, not like a generic database.",
        ],
    }


def master_health() -> Dict[str, Any]:
    with _MASTER_LOCK:
        runtime = dict(_MASTER_RUNTIME)
    stats = get_brain_stats()
    return {
        "master_version": MASTER_BRAIN_VERSION,
        "layers": len(MASTER_LAYERS),
        "runtime": runtime,
        "stats": stats,
        "identity": identity_status(MASTER_GROUP_ID, MASTER_FOUNDER_ID, MASTER_BOT_ID),
        "self_test": master_self_test()["ok"],
    }


# ---------------------------------------------------------------------------
# Action lifecycle / verification
# ---------------------------------------------------------------------------

def create_action(chat_id: int, actor_id: Optional[int], action: str,
                  details: Optional[Dict[str, Any]] = None) -> str:
    """Create an auditable action request; a send is never a completion."""
    details = details or {}
    message_id = details.get("message_id")
    for existing in STORE.data.get("actions", []):
        if (
            existing.get("chat_id") == int(chat_id)
            and existing.get("action") == str(action)
            and message_id is not None
            and existing.get("details", {}).get("message_id") == message_id
            and existing.get("state") not in {"FAILED", "RECOVERED"}
        ):
            return existing["action_id"]
    action_id = "ACT-" + hashlib.sha256(
        f"{chat_id}|{actor_id}|{action}|{time.time()}".encode()
    ).hexdigest()[:12].upper()
    def mutate(data):
        actions = data.setdefault("actions", [])
        actions.append({
            "action_id": action_id, "chat_id": int(chat_id), "actor_id": actor_id,
            "action": str(action), "details": details, "state": "RECEIVED",
            "created_at": time.time(), "updated_at": time.time(),
        })
        data["actions"] = actions[-5000:]
    STORE.mutate(mutate)
    record_audit("action_created", actor_id, chat_id, "RECEIVED", {"action_id": action_id})
    return action_id


def update_action_state(action_id: str, state: str, actor_id: Optional[int] = None,
                        result: Optional[Dict[str, Any]] = None) -> bool:
    """Advance an action safely; only explicit verification may mark completion."""
    if state not in QUEUE_STATES:
        return False
    changed = False
    def mutate(data):
        nonlocal changed
        for item in data.setdefault("actions", []):
            if item.get("action_id") == action_id:
                item["state"] = state
                item["updated_at"] = time.time()
                if result is not None:
                    item["result"] = dict(result)
                changed = True
                break
    STORE.mutate(mutate)
    if changed:
        record_audit("action_state", actor_id, None, state, {"action_id": action_id})
    return changed


def verify_action_result(action_id: str, verified: bool, actor_id: Optional[int] = None,
                         result: Optional[Dict[str, Any]] = None) -> bool:
    """Mark ACTION_CONFIRMED only after verification; otherwise retain a failed state."""
    return update_action_state(
        action_id, "ACTION_CONFIRMED" if verified else "FAILED", actor_id,
        {**(result or {}), "verified": bool(verified)},
    )


# ---------------------------------------------------------------------------
# Compatibility aliases for future integration without changing bot_mention.py
# ---------------------------------------------------------------------------

master_brain_specification = get_master_brain_spec
master_brain_health = master_health
master_is_founder = is_founder
master_is_authorized_group = is_authorized_group
master_is_muba_bot = is_muba_bot_id
master_observe_message = observe_message
master_record_audit = record_audit
master_queue_learning = queue_master_learning
master_remember_decision = remember_decision
master_close_incident = close_incident
master_snapshot = memory_snapshot


if __name__ == "__main__":
    print(json.dumps(master_health(), ensure_ascii=False, indent=2))
