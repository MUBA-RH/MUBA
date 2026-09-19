"""Short-lived private-chat continuity for MUBA Assistant.

This layer handles conversational acknowledgements that depend on the
Assistant's immediately preceding turn. It is intentionally ephemeral,
language-locked, and separate from official MUBA knowledge and Guardian.
"""
from __future__ import annotations
import re, time
from collections import OrderedDict

_TTL=900
_MAX_USERS=2048
_STATE=OrderedDict()

def _norm(text):
    return re.sub(r"[^\w\s\u0600-\u06ff\u0900-\u097f\u4e00-\u9fff]"," ",(text or "").casefold()).strip()

def clear(user_id):
    _STATE.pop(user_id,None)

def remember_assistant_turn(user_id,lang,text):
    if user_id is None: return
    now=time.monotonic()
    _STATE[user_id]={"lang":lang,"assistant":text or "","at":now}
    _STATE.move_to_end(user_id)
    while len(_STATE)>_MAX_USERS: _STATE.popitem(last=False)

_WELLBEING_ASK={
"en":("how are you","how are you doing","how s it going","your mood"),
"tr":("keyfin nasıl","nasılsın","nasıl gidiyor"),
"zh":("你好吗","怎么样","心情怎么样"),
"ar":("كيف حالك","كيفك"),
"hi":("कैसे हो","आप कैसे हैं","तुम कैसे हो"),
}
_POSITIVE={
"en":("i m good","im good","i am good","doing great","pretty good","fine thanks","good thanks","great thanks"),
"tr":("iyiyim","iyi gidiyor","keyfim yerinde","gayet iyiyim","çok iyiyim","şükür iyi","fena değil","sağ ol","teşekkür"),
"zh":("我很好","挺好的","很好 谢谢","不错","还不错","谢谢"),
"ar":("أنا بخير","بخير","تمام","الحمد لله","شكرا","شكرًا"),
"hi":("मैं ठीक हूँ","मैं अच्छा हूँ","बढ़िया","ठीक हूँ","धन्यवाद","शुक्रिया"),
}
_NEGATIVE={
"en":("not good","bad","rough","tired","not great"),
"tr":("kötüyüm","iyi değilim","moralim bozuk","yorgunum","keyfim yok"),
"zh":("不太好","不好","很累","累了"),
"ar":("لست بخير","مو بخير","متعب","تعبان"),
"hi":("ठीक नहीं","अच्छा नहीं","थका हूँ","थक गया"),
}
_REPLY_POS={
"en":"Good to hear. Sounds like the energy is in place. 🪶",
"tr":"Güzel. Demek enerji yerinde. 🪶",
"zh":"很好。看来状态不错。🪶",
"ar":"جميل. يبدو أن الطاقة في مكانها. 🪶",
"hi":"अच्छा है। लगता है ऊर्जा सही जगह पर है। 🪶",
}
_REPLY_NEG={
"en":"Got it. We can keep it easy for a bit. 🪶",
"tr":"Anladım. Biraz sakin takılabiliriz. 🪶",
"zh":"明白了。那我们先轻松一点。🪶",
"ar":"فهمت. يمكننا أن نأخذها بهدوء قليلاً. 🪶",
"hi":"समझ गया। थोड़ी देर आराम से चलते हैं। 🪶",
}

def _contains_any(value,phrases):
    return any(_norm(p) in value for p in phrases)

def reply(user_id,lang,text):
    state=_STATE.get(user_id)
    if not state or state.get("lang")!=lang: return None
    if time.monotonic()-state.get("at",0)>_TTL:
        clear(user_id); return None
    previous=_norm(state.get("assistant",""))
    current=_norm(text)
    if not previous or not current: return None
    if _contains_any(previous,_WELLBEING_ASK.get(lang,())):
        if _contains_any(current,_NEGATIVE.get(lang,())): return _REPLY_NEG[lang]
        if _contains_any(current,_POSITIVE.get(lang,())): return _REPLY_POS[lang]
    return None
