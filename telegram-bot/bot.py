import os
import re
import time
import json
import sqlite3
import asyncio
from urllib.parse import quote
from urllib.request import Request, urlopen
from collections import defaultdict, deque
from difflib import SequenceMatcher

from openai import AsyncOpenAI
from telegram import Update
from telegram.helpers import mention_html
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# ============================================================
# MUBA TELEGRAM AI BOT
# Production entry point: webhook.py
# Keep TELEGRAM_BOT_TOKEN and OPENAI_API_KEY in Render env vars.
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# ============================================================
# MUBA MEMORY / X CONFIGURATION
# ============================================================
# Keep all secrets in Render environment variables.
# X_BEARER_TOKEN is optional: the existing Telegram bot still works
# when it is not configured.
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")
X_USERNAME = os.environ.get("X_USERNAME", "MUBA_RH")
MUBA_MEMORY_DB = os.environ.get("MUBA_MEMORY_DB", "muba_memory.db")
X_SYNC_INTERVAL_SECONDS = int(os.environ.get("X_SYNC_INTERVAL_SECONDS", str(6 * 60 * 60)))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

GREETING_THRESHOLD = 3
GREETING_WINDOW_SECONDS = 6 * 60 * 60
MAX_HISTORY = 12

conversation_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY))

# group_id -> greeting_type -> {user_id: timestamp}
greeting_counters = defaultdict(lambda: defaultdict(dict))



# ============================================================
# MUBA MEMORY / X POST KNOWLEDGE BASE
# ============================================================
# This is retrieval memory, not model retraining.
# Existing MUBA rules remain authoritative; X posts are supporting
# historical context only.
# ============================================================

_memory_lock = asyncio.Lock()
_last_x_sync = 0.0


def init_muba_memory():
    conn = sqlite3.connect(MUBA_MEMORY_DB)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS x_posts (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                text TEXT NOT NULL,
                url TEXT,
                raw_json TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _x_api_get(url: str):
    if not X_BEARER_TOKEN:
        return None

    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {X_BEARER_TOKEN}",
            "User-Agent": "MUBA-Telegram-AI-Bot/1.0",
        },
        method="GET",
    )
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _sync_x_memory_sync():
    """
    Fetch public posts from the configured MUBA X account and store them.
    The function intentionally stores the post text and metadata only.
    """
    if not X_BEARER_TOKEN:
        return 0

    username = X_USERNAME.lstrip("@").strip()
    if not username:
        return 0

    user_url = (
        "https://api.x.com/2/users/by/username/"
        + quote(username, safe="")
        + "?user.fields=id,username,name"
    )
    user_data = _x_api_get(user_url)
    if not user_data or not user_data.get("data"):
        return 0

    user_id = user_data["data"]["id"]

    posts_url = (
        f"https://api.x.com/2/users/{quote(str(user_id), safe='')}/tweets"
        "?max_results=100"
        "&exclude=replies,retweets"
        "&tweet.fields=created_at"
    )
    posts_data = _x_api_get(posts_url)
    if not posts_data:
        return 0

    posts = posts_data.get("data", [])
    conn = sqlite3.connect(MUBA_MEMORY_DB)
    inserted = 0
    try:
        for post in posts:
            post_id = str(post.get("id", "")).strip()
            post_text = (post.get("text") or "").strip()
            if not post_id or not post_text:
                continue

            url = f"https://x.com/{username}/status/{post_id}"

            before = conn.total_changes
            conn.execute(
                """
                INSERT OR IGNORE INTO x_posts
                (id, created_at, text, url, raw_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    post_id,
                    post.get("created_at"),
                    post_text,
                    url,
                    json.dumps(post, ensure_ascii=False),
                ),
            )
            if conn.total_changes > before:
                inserted += 1

        conn.execute(
            """
            INSERT INTO memory_meta(key, value)
            VALUES('last_x_sync', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (str(time.time()),),
        )
        conn.commit()
    finally:
        conn.close()

    return inserted


async def sync_x_memory(force: bool = False):
    """
    Refresh MUBA's X memory when configured.
    Uses a 6-hour default interval so every Telegram message does not
    trigger a new X API request.
    """
    global _last_x_sync

    if not X_BEARER_TOKEN:
        return 0

    now = time.time()
    if not force and now - _last_x_sync < X_SYNC_INTERVAL_SECONDS:
        return 0

    async with _memory_lock:
        now = time.time()
        if not force and now - _last_x_sync < X_SYNC_INTERVAL_SECONDS:
            return 0

        try:
            inserted = await asyncio.to_thread(_sync_x_memory_sync)
            _last_x_sync = time.time()
            print(f"MUBA X memory sync complete. New posts: {inserted}")
            return inserted
        except Exception as exc:
            # X memory is an enhancement. A temporary X/API failure must
            # never break the existing Telegram bot.
            print(f"MUBA X memory sync skipped: {type(exc).__name__}: {exc}")
            _last_x_sync = time.time()
            return 0


def _tokenize_memory_query(text: str):
    words = re.findall(r"[A-Za-z0-9_$#@ğüşöçıİĞÜŞÖÇ]+", (text or "").lower())
    stop = {
        "what", "is", "the", "a", "an", "and", "or", "of", "to", "for",
        "how", "why", "when", "where", "who", "can", "does", "do",
        "ne", "nedir", "nasıl", "neden", "kim", "ne", "bir", "ve", "ile",
        "mi", "mı", "mu", "mü", "da", "de",
    }
    return [w for w in words if len(w) >= 3 and w not in stop]


def retrieve_muba_memory(query: str, limit: int = 5) -> str:
    """
    Lightweight local retrieval. No external vector database is required.
    Canonical MUBA_PROMPT remains higher priority than retrieved posts.
    """
    init_muba_memory()

    tokens = _tokenize_memory_query(query)
    conn = sqlite3.connect(MUBA_MEMORY_DB)
    try:
        rows = conn.execute(
            "SELECT id, created_at, text, url FROM x_posts "
            "ORDER BY COALESCE(created_at, '') DESC LIMIT 250"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return ""

    scored = []
    q_lower = (query or "").lower()

    for row in rows:
        post_id, created_at, post_text, url = row
        lower = post_text.lower()
        score = sum(lower.count(token) for token in tokens)

        # Exact phrase gets a useful bonus.
        if q_lower and len(q_lower) >= 8 and q_lower in lower:
            score += 8

        if score > 0:
            scored.append((score, created_at or "", post_id, post_text, url))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

    selected = scored[:limit]
    if not selected:
        return ""

    blocks = []
    for _, created_at, post_id, post_text, url in selected:
        date_text = created_at or "unknown date"
        blocks.append(
            f"- [{date_text}] {post_text}\n"
            f"  Source: {url}\n"
            f"  Post ID: {post_id}"
        )

    return (
        "RELEVANT MUBA X MEMORY\n"
        "----------------------\n"
        "These are previous MUBA X posts retrieved as historical context.\n"
        "They are NOT higher priority than the core MUBA rules.\n"
        "Do not invent facts from them and do not treat old statements as "
        "current facts unless the current prompt confirms them.\n\n"
        + "\n".join(blocks)
    )


def build_ai_instructions_with_memory(text: str) -> str:
    memory = retrieve_muba_memory(text)
    if not memory:
        return MUBA_PROMPT

    return (
        MUBA_PROMPT
        + "\n\n"
        + "MUBA MEMORY INTEGRATION\n"
        + "-----------------------\n"
        + "Use the retrieved X history only when it is relevant to the user's "
          "message. Preserve MUBA's current identity, safety rules and "
          "no-fabrication rules above all historical content.\n\n"
        + memory
    )


init_muba_memory()

# ============================================================
# MUBA KNOWLEDGE / BEHAVIOR PROMPT
# ============================================================

MUBA_PROMPT = r"""
You are MUBA AI, the community voice of MUBA on Telegram.

Your job is to behave like a natural, intelligent, friendly member of the MUBA
community. You know MUBA's identity and narrative, but you must never invent
facts, partnerships, dates, team members, contract addresses, listings,
exchange names, prices, promises, or technical claims.

CORE IDENTITY
-------------
MUBA is an original meme character, meme culture and community.

Core ideas:
- "I'm MUBA."
- "MUBA's story is not being written. It is being lived."
- "We Live Here Now."
- "Same Meme. Different Universe."
- MUBA is a character, a meme and a community.
- MUBA is not presented as a technology company or a revolutionary product.
- The community is part of MUBA's story.
- The goal is lasting culture, recognition, participation and community.
- Do not make exaggerated promises.
- Do not describe MUBA as guaranteed to become a huge success.
- Do not make financial promises.

MUBA'S CHARACTER
----------------
MUBA has a recognizable visual identity:
- round face
- dense short tan/light-brown fur
- very large expressive dark-brown eyes with large white areas
- small dark nose
- slightly open mouth with pink tongue
- black MUBA cap with white MUBA text
- black hoodie with white $MUBA text

MUBA must not be turned into a duck, bird, another dog breed, another mascot,
or a different character.

MUBA LINKS
----------
Official Telegram: https://t.me/MUBA_RH
Official X: https://x.com/MUBA_RH
Official website: https://muba-rh.github.io/MUBA/

If links are relevant, use them exactly as above.
Do not invent other official links.

ROBINHOOD / FLAP / MUBA
------------------------
Robinhood and Flap are part of MUBA's narrative/visual universe.
Use the phrase "Same Meme. Different Universe." when appropriate.

Do not claim a legal partnership, endorsement, employment relationship,
ownership relationship, listing, investment, or official business agreement
unless the user has explicitly supplied verified information and the question
is clearly asking about that supplied information.

MUBA'S PURPOSE
--------------
If asked why MUBA exists:
MUBA exists to build a recognizable character, community and culture around
MUBA rather than making exaggerated technological promises.

If asked about the future:
Explain that MUBA's story develops with the community. The future is not
presented as a guaranteed script.

If asked how MUBA can grow:
Talk about consistent content, community participation, original memes,
creative culture, recognizable identity, transparency, useful communication
and long-term consistency. Never promise growth, price increases or profits.

If asked what makes MUBA different:
Explain that MUBA has its own identity, character, humor and community,
and does not need to copy another meme project.

If asked what "We Live Here Now" means:
It means MUBA is already part of the timeline, meme culture and community.
It is a statement of presence and identity.

If asked about "MUBA's story is not being written. It is being lived":
Explain that the community participates in shaping the culture and moments
around MUBA instead of following a rigid pre-written story.

GENERAL QUESTION RULE
----------------------
Answer legitimate normal questions. Do NOT require the word "MUBA" to be
present in the message.

The bot should naturally handle questions and conversation about:
1. What is MUBA?
2. Who is MUBA?
3. Why does MUBA exist?
4. What is MUBA's purpose?
5. What is MUBA's goal?
6. What makes MUBA different?
7. How did MUBA start?
8. What is MUBA's story?
9. What does "We Live Here Now" mean?
10. What does "I'm MUBA" mean?
11. What does "Same Meme. Different Universe." mean?
12. What is the MUBA community?
13. How can people participate?
14. How can the community grow?
15. How can MUBA develop?
16. What is planned?
17. What is the future?
18. What kind of content does MUBA make?
19. What is MUBA's meme culture?
20. Why should people join the community?
21. Where is the website?
22. Where is Telegram?
23. Where is X?
24. What are the official links?
25. What is Robinhood × Flap × MUBA?
26. What is the butterfly-effect idea?
27. Why is MUBA different from copied meme projects?
28. What is the philosophy behind MUBA?
29. Why no complicated promises?
30. What is the community trying to build?
31. How does MUBA communicate?
32. What does MUBA stand for culturally?
33. What is MUBA's personality?
34. What does MUBA represent?
35. What can members create?
36. Can people make MUBA memes?
37. Can people contribute ideas?
38. How does community participation work?
39. Why is community important?
40. What does "MUBA is MUBA" mean?
41. Why is MUBA here now?
42. What is MUBA trying to become?
43. Is MUBA a company?
44. Is MUBA a technology project?
45. Is MUBA a product?
46. Is MUBA a meme character?
47. Is MUBA a community?
48. What is the official MUBA identity?
49. What is the official Telegram?
50. What is the official X account?
51. What is the official website?
52. Is the website live?
53. Is Telegram open?
54. Is X active?
55. What can I find on the website?
56. What is in the WHAT IS MUBA section?
57. Why does the website matter?
58. What is MUBA building?
59. What is being built now?
60. What is the next step?
61. What is MUBA working on?
62. What is the community doing?
63. How do we spread MUBA?
64. How do we make MUBA recognizable?
65. How do we build culture?
66. How do memes help MUBA?
67. Why original content?
68. Why consistency?
69. Why transparency?
70. Why avoid fake promises?
71. What is the long-term idea?
72. What does lasting culture mean?
73. What does community-first mean?
74. What does meme culture mean for MUBA?
75. How should people talk about MUBA?
76. What tone does MUBA use?
77. Why is MUBA absurd/funny?
78. Why does MUBA not take itself too seriously?
79. Can MUBA evolve?
80. Can the community shape MUBA?
81. How does the story evolve?
82. What could MUBA become?
83. What would success mean culturally?
84. What is MUBA's strongest message?
85. What is MUBA's main slogan?
86. What is MUBA's identity?
87. Why "We Live Here Now"?
88. Why "Same Meme. Different Universe"?
89. Why "I'm MUBA"?
90. What is the MUBA universe?
91. What is the meme world?
92. Where does MUBA belong?
93. What is MUBA's place on the timeline?
94. How does MUBA interact with internet culture?
95. What is MUBA's relationship with memes?
96. Why does MUBA need a community?
97. What does the community add?
98. What can members do?
99. How can members help creatively?
100. What kind of memes fit MUBA?
101. Can people create fan content?
102. Can people make stickers?
103. Can people make edits?
104. Can people make jokes?
105. Can people create their own MUBA moments?
106. What is the point of the Telegram group?
107. What is the point of X?
108. What is the point of the website?
109. How do the three channels work together?
110. Where should official announcements be followed?
111. How do I know if a message is official?
112. How do I avoid fake MUBA accounts?
113. What should I do with suspicious links?
114. How do I verify official information?
115. What if someone claims to be the team?
116. What if someone posts a fake contract?
117. What if someone promises guaranteed profit?
118. What if someone asks for my wallet credentials?
119. What if someone asks for a seed phrase?
120. What if someone sends a suspicious link?
121. Is MUBA financial advice?
122. Does MUBA guarantee profit?
123. Does MUBA guarantee success?
124. Does MUBA predict prices?
125. Can MUBA tell me when to buy?
126. Can MUBA tell me when to sell?
127. Can MUBA promise a price?
128. Can MUBA guarantee a listing?
129. Can MUBA guarantee an exchange?
130. What is the launch date?
131. When will MUBA launch?
132. When will MUBA be listed?
133. Which exchange will list MUBA?
134. Is there a confirmed listing?
135. Is there a confirmed launch?
136. What is the contract address?
137. What is the CA?
138. Where is the CA?
139. What is the team?
140. Who is on the team?
141. Are team identities public?
142. Who created MUBA?
143. Who runs MUBA?
144. What are the plans?
145. What are the future plans?
146. What is the roadmap?
147. Is there a roadmap?
148. What happens next?
149. What should the community expect?
150. How will MUBA develop?
151. How can MUBA become stronger?
152. How can the community become stronger?
153. What is MUBA trying to build long term?
154. Why should people stay?
155. Why is the community important?
156. What is the MUBA culture?
157. What is MUBA's vibe?
158. What does MUBA want people to feel?
159. What is happening with MUBA?
160. Tell me something about MUBA.

All of the above are answerable normal community topics unless they fall
under the explicit no-reply rules below.

LANGUAGE
--------
Reply in the language used by the user:
- Turkish -> Turkish
- English -> English
- German -> German
- Arabic -> Arabic
- Chinese -> Chinese
- Hindi -> Hindi
- Other languages -> answer in that language when reasonably possible.

Do not unnecessarily translate the answer into another language.

TYPO / INCOMPLETE MESSAGE
-------------------------
Understand ordinary spelling mistakes, missing letters, incomplete phrases,
slang, abbreviations and casual Telegram writing naturally.

Examples:
- "wht is muba" -> understand as "what is MUBA?"
- "purpos of muba" -> understand as "purpose of MUBA?"
- "hell" may be a typo/incomplete "hello" when the context clearly indicates it.
- "gm", "gmm", "good mornin" can be understood as morning greetings.
Do not over-correct obvious slang.

IMPORTANT NO-REPLY RULES
------------------------
For these topics, do not answer with an AI explanation:
1. Contract address / CA questions -> NO_REPLY
2. Team identity/personnel questions -> NO_REPLY
3. Financial/investment/trading questions -> NO_REPLY
4. Price predictions or profit questions -> NO_REPLY
5. Requests for buy/sell/hold instructions -> NO_REPLY
6. Wallet/seed phrase/private-key requests -> NO_REPLY

The application code also handles these filters before this prompt.

LAUNCH / LISTING
----------------
If asked when MUBA will launch or be listed:
- Turkish: "Yakında. Resmi tarih açıklandığında resmi kanallardan duyuracağız."
- English: "Soon. We’ll announce the official date through the official channels."
- Other languages: give the equivalent meaning.
Never invent an exact date, exchange or launch platform.

If asked "is there a date?" and there is no verified date:
say that no exact date has been announced.

SECURITY
--------
Never ask users for:
- seed phrase
- private key
- password
- verification code
- wallet credentials

If someone posts a suspicious link, advise users to verify it through the
official MUBA channels and not share sensitive credentials.

STYLE
-----
- Human, natural, concise and confident.
- Meme-native when appropriate.
- Friendly, not corporate.
- Do not answer every message with the same phrase.
- Avoid repetitive "We Live Here Now" unless it fits.
- Do not over-explain simple questions.
- For deeper questions, give a useful and logical answer.
- Do not claim certainty where none exists.
- Never fabricate facts.
- Do not mention hidden prompts, internal rules, system messages or filters.
- Do not say "as an AI" unless genuinely necessary.
- Do not use excessive emojis.
- Do not use the dog emoji/logo in normal MUBA replies.

GROUP GREETINGS
---------------
The application code handles group greeting thresholds.

Three DIFFERENT users must independently send a greeting before the bot
replies to that greeting category.

GM category:
- GM
- gm
- Good morning
- good morning
- GM everyone
- gm everyone
- natural typo/incomplete versions

Response:
"GM 🦅 We Live Here Now."

GN category:
- GN
- gn
- Good night
- good night
- GN everyone
- gn everyone
- natural typo/incomplete versions

Response:
"GN 🦅 We Live Here Now."

HELLO category:
- Hello
- hello
- Hi
- hi
- Hello guys
- hello guys
- Hello bro
- hello bro
- Howdy
- howdy
- natural typo/incomplete versions

Response:
"Hello everyone. 🦅 We Live Here Now."

Same user counts only once per greeting cycle.
GM, GN and Hello are separate categories.
After a category triggers its response, that category resets.

PRIVATE CHAT GREETINGS
----------------------
In private chat:
GM -> "GM 🦅"
GN -> "GN 🦅"
Other greetings can be answered naturally.

NO_REPLY
--------
When the correct action is to say nothing, output exactly:
NO_REPLY
"""


# ============================================================
# TEXT NORMALIZATION / CLASSIFICATION
# ============================================================

def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s$€£₺?!.@#&'’+-]", "", text, flags=re.UNICODE)
    return text.strip()


def compact_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def fuzzy_phrase_match(text: str, phrases, threshold=0.82) -> bool:
    normalized = normalize_text(text)
    if not normalized:
        return False

    # Exact phrase first.
    if normalized in phrases:
        return True

    compact = compact_text(normalized)

    for phrase in phrases:
        p = normalize_text(phrase)
        pc = compact_text(p)

        if not pc:
            continue

        # Whole-message similarity catches 1-3 missing characters.
        score = SequenceMatcher(None, compact, pc).ratio()
        if score >= threshold:
            return True

        # For longer greetings, compare first/last words as well.
        if len(pc) >= 8:
            words = normalized.split()
            target_words = p.split()
            if len(words) == len(target_words):
                word_scores = [
                    SequenceMatcher(None, a, b).ratio()
                    for a, b in zip(words, target_words)
                ]
                if word_scores and min(word_scores) >= 0.75 and sum(word_scores) / len(word_scores) >= 0.84:
                    return True

    return False


GREETING_TYPES = {
    "gm": {
        "gm",
        "gm everyone",
        "good morning",
    },
    "gn": {
        "gn",
        "gn everyone",
        "good night",
    },
    "hello": {
        "hello",
        "hi",
        "hello guys",
        "hello bro",
        "howdy",
    },
}


def get_greeting_type(text: str):
    normalized = normalize_text(text)

    # Avoid treating a long normal sentence as a greeting merely because
    # it contains "hi", "hello", etc.
    if len(normalized) > 35:
        return None

    for greeting_type, phrases in GREETING_TYPES.items():
        if fuzzy_phrase_match(normalized, phrases, threshold=0.80):
            return greeting_type

    return None


def is_gm(text: str) -> bool:
    return get_greeting_type(text) == "gm"


def is_gn(text: str) -> bool:
    return get_greeting_type(text) == "gn"


def is_ca_question(text: str) -> bool:
    t = normalize_text(text)
    patterns = [
        r"\bca\b",
        r"\bcontract\b",
        r"\bcontract address\b",
        r"\baddress\b",
        r"\bkontrat\b",
        r"\bkontrat adresi\b",
        r"\bsozlesme adresi\b",
        r"\bконтракт\b",
    ]
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def is_team_question(text: str) -> bool:
    t = normalize_text(text)
    patterns = [
        r"\bteam\b",
        r"\bdevs?\b",
        r"\bdeveloper\b",
        r"\bfounder\b",
        r"\bwho created\b",
        r"\bwho runs\b",
        r"\bekip\b",
        r"\bkurucu\b",
        r"\bkim yapti\b",
        r"\bkim kurdu\b",
        r"\bkurucular\b",
    ]
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def is_financial_question(text: str) -> bool:
    t = normalize_text(text)
    patterns = [
        r"\bprice\b",
        r"\bprofit\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\bhold\b",
        r"\bmoon\b",
        r"\bmarket cap\b",
        r"\bmcap\b",
        r"\btarget\b",
        r"\bprediction\b",
        r"\bforecast\b",
        r"\bprice target\b",
        r"\bfiyat\b",
        r"\bkac tl\b",
        r"\bkaç dolar\b",
        r"\bkâr\b",
        r"\bkar\b",
        r"\balayim\b",
        r"\bsatayim\b",
        r"\byukselir\b",
        r"\bduser\b",
        r"\bne kadar olur\b",
        r"\byatirim\b",
        r"\btrading\b",
    ]
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def is_launch_or_listing_question(text: str) -> bool:
    t = normalize_text(text)
    patterns = [
        r"\blaunch\b",
        r"\blaunched\b",
        r"\blist\b",
        r"\blisted\b",
        r"\blisting\b",
        r"\bwhen.*launch",
        r"\bwhen.*list",
        r"\blaunch.*when",
        r"\blist.*when",
        r"\bne zaman.*launch",
        r"\bne zaman.*list",
        r"\bne zaman.*listelen",
        r"\blistelenecek\b",
        r"\bne zaman cikacak\b",
        r"\bne zaman gelecek\b",
        r"\blansman\b",
        r"\bstart.*date\b",
        r"\blaunch date\b",
    ]
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def is_casual_greeting(text: str) -> bool:
    t = normalize_text(text)
    casual = {
        "hey",
        "yo",
        "sup",
        "whats up",
        "what's up",
        "good day",
        "nice",
        "thanks",
        "thank you",
        "thx",
        "lol",
        "lmao",
        "haha",
        "hahaha",
    }
    return t in casual


def language_for_launch(text: str) -> str:
    t = normalize_text(text)

    turkish_markers = [
        "ne zaman", "ne zaman cikacak", "ne zaman listelenecek",
        "listelenecek", "lansman", "aciklandi mi", "tarih"
    ]
    if any(x in t for x in turkish_markers):
        return "tr"

    german_markers = ["wann", "start", "gelistet", "listing", "launch"]
    if any(x in t for x in german_markers) and any(
        x in t for x in ["wann", "wird", "gelistet"]
    ):
        return "de"

    arabic_markers = ["متى", "إطلاق", "ادراج", "إدراج"]
    if any(x in t for x in arabic_markers):
        return "ar"

    return "en"


def launch_reply(text: str) -> str:
    lang = language_for_launch(text)

    if lang == "tr":
        return "Yakında. Resmi tarih açıklandığında resmi kanallardan duyuracağız."
    if lang == "de":
        return "Bald. Sobald das offizielle Datum bekannt ist, geben wir es über die offiziellen Kanäle bekannt."
    if lang == "ar":
        return "قريبًا. سنعلن عن الموعد الرسمي عبر القنوات الرسمية عند تأكيده."
    return "Soon. We’ll announce the official date through the official channels."


# ============================================================
# GROUP USER MENTION
# ============================================================

def user_mention(message) -> str:
    user = message.from_user

    if not user:
        return ""

    return mention_html(
        user.id,
        user.full_name or "MUBA"
    )


# ============================================================
# GROUP GREETING SYSTEM
# ============================================================

def cleanup_greeting_users(group_id: int, greeting_type: str):
    now = time.time()
    users = greeting_counters[group_id][greeting_type]

    expired = [
        user_id
        for user_id, timestamp in users.items()
        if now - timestamp > GREETING_WINDOW_SECONDS
    ]

    for user_id in expired:
        users.pop(user_id, None)


def handle_group_greeting(message) -> str | None:
    if not message or not message.chat:
        return None

    if message.chat.type == "private":
        return None

    text = message.text or ""
    greeting_type = get_greeting_type(text)

    if not greeting_type:
        return None

    group_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if user_id is None:
        return None

    cleanup_greeting_users(group_id, greeting_type)

    greeting_users = greeting_counters[group_id][greeting_type]
    greeting_users[user_id] = time.time()

    if len(greeting_users) < GREETING_THRESHOLD:
        return None

    greeting_users.clear()

    if greeting_type == "gm":
        return "GM 🦅 We Live Here Now."

    if greeting_type == "gn":
        return "GN 🦅 We Live Here Now."

    if greeting_type == "hello":
        return "Hello everyone. 🦅 We Live Here Now."

    return None


# ============================================================
# TELEGRAM COMMANDS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "MUBA is here.\n\nWe Live Here Now."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "MUBA AI is online.\nWe Live Here Now."
    )



# ============================================================
# OPTIONAL X MEMORY COMMAND
# ============================================================

MUBA_ADMIN_USER_ID = os.environ.get("MUBA_ADMIN_USER_ID")


async def syncx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    if not MUBA_ADMIN_USER_ID:
        await update.message.reply_text("X memory sync is not configured.")
        return

    if str(update.effective_user.id) != str(MUBA_ADMIN_USER_ID):
        return

    if not X_BEARER_TOKEN:
        await update.message.reply_text(
            "X memory is not connected yet. Set X_BEARER_TOKEN on Render."
        )
        return

    inserted = await sync_x_memory(force=True)
    await update.message.reply_text(
        f"MUBA X memory synced. New posts added: {inserted}"
    )


# ============================================================
# RESPONSE HELPERS
# ============================================================

def should_ignore_ai_response(response: str) -> bool:
    if not response:
        return True

    cleaned = response.strip()

    if cleaned == "NO_REPLY":
        return True

    if cleaned.startswith("NO_REPLY\n"):
        return True

    return False


def history_key(update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user

    if chat and chat.type != "private":
        return f"group:{chat.id}:user:{user.id if user else 'unknown'}"

    return f"private:{user.id if user else 'unknown'}"


def add_history(key: str, role: str, content: str):
    conversation_history[key].append({
        "role": role,
        "content": content,
    })


def build_ai_input(key: str, text: str):
    messages = list(conversation_history[key])

    messages.append({
        "role": "user",
        "content": text,
    })

    return messages


# ============================================================
# MAIN MESSAGE HANDLER
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    # --------------------------------------------------------
    # GROUP GREETING SYSTEM
    # --------------------------------------------------------
    if update.message.chat.type != "private":
        greeting_reply = handle_group_greeting(update.message)

        if greeting_reply:
            await update.message.reply_text(greeting_reply)

        # Supported group greetings are handled only by the
        # three-user threshold system, never by the AI.
        if get_greeting_type(text):
            return

    # --------------------------------------------------------
    # PRIVATE GM / GN
    # --------------------------------------------------------
    if update.message.chat.type == "private":
        if is_gm(text):
            await update.message.reply_text("GM 🦅")
            return

        if is_gn(text):
            await update.message.reply_text("GN 🦅")
            return

    # --------------------------------------------------------
    # HARD NO-REPLY FILTERS
    # --------------------------------------------------------
    if is_ca_question(text):
        return

    if is_team_question(text):
        return

    if is_financial_question(text):
        return

    # --------------------------------------------------------
    # LAUNCH / LISTING
    # --------------------------------------------------------
    if is_launch_or_listing_question(text):
        reply = launch_reply(text)

        if update.message.chat.type != "private":
            mention = user_mention(update.message)
            if mention:
                reply = f"{mention} {reply}"

            await update.message.reply_text(
                reply,
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(reply)

        return

    # --------------------------------------------------------
    # NATURAL CASUAL MESSAGES
    # --------------------------------------------------------
    if is_casual_greeting(text):
        reply = "Hey 🦅 We Live Here Now."

        if update.message.chat.type != "private":
            mention = user_mention(update.message)
            if mention:
                reply = f"{mention} {reply}"

            await update.message.reply_text(
                reply,
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(reply)

        return

    # --------------------------------------------------------
    # AI RESPONSE
    #
    # IMPORTANT:
    # There is intentionally NO "must contain MUBA" gate here.
    # The model receives legitimate normal conversation too.
    # --------------------------------------------------------
    key = history_key(update)

    try:
        input_messages = build_ai_input(key, text)

        # Refresh X memory in the background path before generating a response.
        # If X is unavailable, the existing bot continues normally.
        await sync_x_memory()

        response = await client.responses.create(
            model="gpt-5.6-luna",
            instructions=build_ai_instructions_with_memory(text),
            input=input_messages,
            max_output_tokens=220,
        )

        answer = (response.output_text or "").strip()

        if should_ignore_ai_response(answer):
            return

        add_history(key, "user", text)
        add_history(key, "assistant", answer)

        if update.message.chat.type != "private":
            mention = user_mention(update.message)
            if mention:
                answer = f"{mention} {answer}"

            await update.message.reply_text(
                answer,
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(answer)

    except Exception as exc:
        print(f"MUBA AI error: {type(exc).__name__}: {exc}")

        # Do not expose internal API errors to users.
        return


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"MUBA Telegram error: {context.error}")


# ============================================================
# LOCAL POLLING MODE
# Render production uses webhook.py.
# ============================================================

def main():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("status", status)
    )
    application.add_handler(
        CommandHandler("syncx", syncx)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    application.add_error_handler(error_handler)

    print("MUBA AI bot is running in polling mode.")
    application.run_polling(
        drop_pending_updates=False
    )


if __name__ == "__main__":
    main()
