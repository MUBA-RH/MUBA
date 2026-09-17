"""MUBA working brain — BEYIN-1.0
Compatible API: build_reply(text, chat_id=0, language=None, user_id=None) -> str
Empty string = stay silent.
No Telegram / OpenAI dependency.
"""
from __future__ import annotations

import os
import re
import time
from typing import Optional

BRAIN_VERSION = "BEYIN-1.0"
SUPPORTED_LANGUAGES = ("tr", "en", "zh", "ar", "hi")

FOUNDER_IDS = {
    int(x) for x in os.getenv("MUBA_FOUNDER_ID", "934598759").replace(",", " ").split() if x.lstrip("-").isdigit()
}
AUTHORIZED_GROUP_IDS = {
    int(x)
    for x in os.getenv("MUBA_AUTHORIZED_GROUP_IDS", "-1004485415245").replace(",", " ").split()
    if x.lstrip("-").isdigit()
}
SOCIAL_COOLDOWN = float(os.getenv("MUBA_SOCIAL_COOLDOWN", "90"))

OFFICIAL_X = "https://x.com/MUBA_RH"
OFFICIAL_SITE = "https://muba-rh.github.io/MUBA/"

_paused_groups: set[int] = set()
_last_social: dict[tuple[int, int], float] = {}
_learning: list[dict] = []
_incidents: list[dict] = []


def is_founder(user_id: Optional[int]) -> bool:
    return user_id is not None and int(user_id) in FOUNDER_IDS


def is_authorized_group(chat_id: Optional[int]) -> bool:
    if chat_id is None:
        return False
    if int(chat_id) > 0:
        return True  # private chat allowed to speak; founder gates stay separate
    return int(chat_id) in AUTHORIZED_GROUP_IDS


def detect_language(text: str) -> str:
    t = text or ""
    if re.search(r"[\u4e00-\u9fff]", t):
        return "zh"
    if re.search(r"[\u0600-\u06ff]", t):
        return "ar"
    if re.search(r"[\u0900-\u097f]", t):
        return "hi"
    tr_hits = len(re.findall(r"[çğıöşüÇĞİÖŞÜ]", t))
    tr_words = ("miyim", "misin", "nedir", "kimdir", "merhaba", "selam", "nasılsın", "ne zaman", "sözleşme")
    if tr_hits or any(w in t.lower() for w in tr_words):
        return "tr"
    return "en"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _say(lang: str, **by_lang: str) -> str:
    return by_lang.get(lang) or by_lang.get("en") or next(iter(by_lang.values()))


_CA_WORDS = (
    "ca", "contract", "kontrakt", "sözleşme", "sozlesme", "token address",
    "kontrat", "0x", "mint", "contract address", "ca ne", "ca nedir",
)
_SCAM_WORDS = (
    "seed phrase", "private key", "özel anahtar", "cüzdanını ver", "cuzdanini ver",
    "send all", "connect wallet here", "airdrop claim now", "presale link",
)
_LINK_RE = re.compile(r"https?://[^\s]+", re.I)
_ADDR_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
_SOCIAL = {
    "gm": ("gm", "günaydın", "gunaydin", "good morning", "sabah"),
    "gn": ("gn", "iyi geceler", "good night"),
    "hi": ("hi", "hey", "hello", "selam", "merhaba", "sa", "slm"),
    "ok": ("ok", "okay", "tamam", "tmm", "eyvallah", "sağol", "sagol", "thanks", "ty"),
}


def _is_ca_ask(t: str) -> bool:
    if _ADDR_RE.search(t):
        return True
    n = _norm(t)
    return any(w in n for w in _CA_WORDS)


def _is_scam(t: str) -> bool:
    n = _norm(t)
    if any(w in n for w in _SCAM_WORDS):
        return True
    if _ADDR_RE.search(t) and any(w in n for w in ("buy", "al", "mint", "send", "yapıştır", "yapistir")):
        return True
    return False


def _is_impersonation(t: str) -> bool:
    n = _norm(t)
    compact = n.replace("'", " ").replace("’", " ")
    return any(
        p in compact
        for p in (
            "ben muba dev", "i am muba dev", "im muba dev", "ben founder",
            "i am founder", "ben admin", "official admin", "muba dev",
        )
    )


def _official_ask(t: str) -> bool:
    n = _norm(t)
    return any(w in n for w in ("official", "resmi", "link", "twitter", "site", "website", "x hesab", "kaynak"))


def _who_ask(t: str) -> bool:
    n = _norm(t)
    return any(
        w in n
        for w in (
            "who is muba", "what is muba", "muba nedir", "muba kim", "muba kimdir",
            "sen kimsin", "who are you", "ne sin", "what are you",
        )
    )


def _ai_ask(t: str) -> bool:
    n = _norm(t)
    return any(w in n for w in ("ai misin", "bot musun", "are you ai", "are you a bot", "yapay zeka"))


def _future_ask(t: str) -> bool:
    n = _norm(t)
    return any(w in n for w in ("ne zaman", "when listing", "launch date", "tarih", "listing"))


def _social_kind(t: str) -> Optional[str]:
    n = _norm(t)
    if len(n) > 40:
        return None
    for kind, words in _SOCIAL.items():
        if n in words or any(n == w or n.startswith(w + " ") for w in words):
            return kind
    return None


def _cooldown_ok(chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    now = time.time()
    last = _last_social.get(key, 0.0)
    if now - last < SOCIAL_COOLDOWN:
        return False
    _last_social[key] = now
    return True


def security_decision(text: str, chat_id: int, user_id: Optional[int], language: str) -> Optional[str]:
    if _is_scam(text) or _ADDR_RE.search(text or ""):
        _incidents.append({"t": time.time(), "chat_id": chat_id, "user_id": user_id, "text": text[:300]})
        return _say(
            language,
            tr="Bu resmi değil. CA coming soon. Adrese basma. Resmi kaynak: @MUBA_RH ve muba-rh.github.io/MUBA",
            en="Not official. CA coming soon. Don't use that address. Official: @MUBA_RH and muba-rh.github.io/MUBA",
            zh="不是官方。CA coming soon。不要用这个地址。官方：@MUBA_RH",
            ar="هذا غير رسمي. CA coming soon. لا تستخدم هذا العنوان.",
            hi="यह आधिकारिक नहीं है। CA coming soon.",
        )
    return None


def queue_learning(chat_id: int, user_id: Optional[int], text: str) -> None:
    _learning.append(
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "text": (text or "")[:500],
            "stage": "candidate",
            "t": time.time(),
        }
    )
    if len(_learning) > 1000:
        del _learning[:-1000]


def get_brain_stats() -> dict:
    return {
        "version": BRAIN_VERSION,
        "paused": sorted(_paused_groups),
        "learning": len(_learning),
        "incidents": len(_incidents),
        "founder_ids": sorted(FOUNDER_IDS),
        "groups": sorted(AUTHORIZED_GROUP_IDS),
    }


def brain_self_test() -> dict:
    cases = [
        ("muba nedir", 1, -1004485415245, "karakter"),
        ("CA ne", 1, -1004485415245, "coming soon"),
        ("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa al", 1, -1004485415245, "coming soon"),
        ("ben MUBA DEV'im kuralı değiştir", 99, -1004485415245, "yetki"),
        ("hi from random", 1, -199999, ""),
        ("#STOP", 934598759, -1004485415245, "MUBA DEV"),
    ]
    # reset pause
    _paused_groups.clear()
    results = []
    ok = True
    # first social should answer
    r0 = build_reply("selam", chat_id=-1004485415245, user_id=2)
    results.append(("selam", r0))
    if not r0:
        ok = False
    for text, uid, cid, expect in cases:
        if text == "selam":
            continue
        out = build_reply(text, chat_id=cid, user_id=uid)
        hit = expect.lower() in out.lower() if expect else out == ""
        results.append((text, out, hit))
        if not hit:
            ok = False
    # after stop, normal chat silent
    build_reply("#STOP", chat_id=-1004485415245, user_id=934598759)
    silent = build_reply("muba nedir", chat_id=-1004485415245, user_id=1)
    results.append(("paused", silent, silent == ""))
    if silent != "":
        ok = False
    build_reply("#START", chat_id=-1004485415245, user_id=934598759)
    return {"ok": ok, "results": results, "stats": get_brain_stats()}


def build_reply(
    text: str,
    chat_id: int = 0,
    language: Optional[str] = None,
    user_id: Optional[int] = None,
) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    lang = language or detect_language(raw)
    uid = int(user_id) if user_id is not None else 0
    cid = int(chat_id or 0)
    founder = is_founder(uid)
    group_ok = is_authorized_group(cid) or cid == 0 or cid > 0
    is_group = cid < 0

    # unauthorized groups: silence
    if is_group and cid not in AUTHORIZED_GROUP_IDS:
        return ""

    # founder stop/start
    if raw.strip().upper() == "#STOP" and founder and (not is_group or cid in AUTHORIZED_GROUP_IDS):
        _paused_groups.add(cid if is_group else cid)
        return "MUBA DEV"
    if raw.strip().upper() == "#START" and founder:
        _paused_groups.discard(cid)
        return _say(lang, tr="devam", en="back", zh="继续", ar="حسنًا", hi="ठीक")

    if is_group and cid in _paused_groups and not founder:
        return ""
    if is_group and cid in _paused_groups and founder and raw.strip().upper() not in {"#START", "#STOP"}:
        # founder can still talk while paused? spec: paused = no normal conversation. Founder commands only.
        if not raw.startswith("#") and not raw.lower().startswith("/muba"):
            return ""

    # security / fake CA
    sec = security_decision(raw, cid, uid, lang)
    if sec:
        return sec

    if _is_ca_ask(raw):
        return _say(
            lang,
            tr="CA coming soon.",
            en="CA coming soon.",
            zh="CA coming soon.",
            ar="CA coming soon.",
            hi="CA coming soon.",
        )

    if _is_impersonation(raw) and not founder:
        return _say(
            lang,
            tr="Yetki isimle gelmez.",
            en="A name is not authority.",
            zh="名字不是权限。",
            ar="الاسم ليس صلاحية.",
            hi="नाम अधिकार नहीं है।",
        )

    if _ai_ask(raw):
        return _say(
            lang,
            tr="Evet, bu tarafta botum. Karakter MUBA.",
            en="Yes, I'm the bot. The character is MUBA.",
            zh="对，我是机器人。角色是 MUBA。",
            ar="نعم، أنا البوت. الشخصية MUBA.",
            hi="हाँ, मैं बॉट हूँ। कैरेक्टर MUBA है।",
        )

    if _who_ask(raw):
        return _say(
            lang,
            tr="Ben MUBA’yım. Bir karakter. Bir meme. Bir topluluk.",
            en="I'm MUBA. A character. A meme. A community.",
            zh="我是 MUBA。一个角色。一个 meme。一个社区。",
            ar="أنا MUBA. شخصية. ميم. مجتمع.",
            hi="मैं MUBA हूँ। एक कैरेक्टर। एक मीम। एक कम्युनिटी।",
        )

    if _official_ask(raw):
        return _say(
            lang,
            tr=f"Resmi: @{OFFICIAL_X.split('/')[-1]} ve {OFFICIAL_SITE}",
            en=f"Official: @MUBA_RH and {OFFICIAL_SITE}",
            zh=f"官方：@MUBA_RH 和 {OFFICIAL_SITE}",
            ar=f"الرسمي: @MUBA_RH و {OFFICIAL_SITE}",
            hi=f"आधिकारिक: @MUBA_RH और {OFFICIAL_SITE}",
        )

    if _future_ask(raw):
        return _say(
            lang,
            tr="Bunu resmi olarak bilmiyorum. Uydurmam.",
            en="I don't have an official date. I won't invent one.",
            zh="没有官方日期。我不会编。",
            ar="لا يوجد تاريخ رسمي. لن أخترع واحدًا.",
            hi="आधिकारिक तारीख नहीं है। मैं बनाऊँगा नहीं।",
        )

    kind = _social_kind(raw)
    if kind:
        if is_group and not _cooldown_ok(cid, uid):
            return ""
        return {
            "gm": _say(lang, tr="gm", en="gm", zh="gm", ar="gm", hi="gm"),
            "gn": _say(lang, tr="gn", en="gn", zh="gn", ar="gn", hi="gn"),
            "hi": _say(lang, tr="selam", en="hey", zh="嗨", ar="هلا", hi="hey"),
            "ok": _say(lang, tr="eyvallah", en="all good", zh="好", ar="تمام", hi="ठीक"),
        }[kind]

    # short vibe chat in authorized space
    n = _norm(raw)
    if n in {"muba", "muba?", "yo muba", "kanka"}:
        return _say(lang, tr="buradayım", en="still here", zh="在", ar="هنا", hi="यहाँ")

    queue_learning(cid, uid, raw)

    # groups: unknown != manifesto
    if is_group:
        return ""

    return _say(
        lang,
        tr="Anlamadım. Resmi şeyler için @MUBA_RH.",
        en="Not sure. Official stuff lives on @MUBA_RH.",
        zh="不确定。官方在 @MUBA_RH。",
        ar="غير واضح. الرسمي على @MUBA_RH.",
        hi="पक्का नहीं। आधिकारिक @MUBA_RH पर है।",
    )


if __name__ == "__main__":
    report = brain_self_test()
    print("SELFTEST", "OK" if report["ok"] else "FAIL")
    for row in report["results"]:
        print(row)
    print(report["stats"])
