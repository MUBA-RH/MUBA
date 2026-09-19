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
    value=(text or "").casefold().replace("İ".casefold(),"i")
    return re.sub(r"[^\w\s\u0600-\u06ff\u0900-\u097f\u4e00-\u9fff]"," ",value).strip()

def clear(user_id):
    _STATE.pop(user_id,None)

def remember_assistant_turn(user_id,lang,text):
    if user_id is None: return
    now=time.monotonic()
    old=_STATE.get(user_id,{})
    turns=list(old.get("turns",[]))
    turns.append(("assistant",text or ""))
    _STATE[user_id]={"lang":lang,"assistant":text or "","at":now,"turns":turns[-8:],"expected_reply":_expected_reply(lang,text)}
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
"en":("good","i m good","im good","i am good","doing great","pretty good","fine","fine thanks","good thanks","great","great thanks"),
"tr":("iyi","iyiyim","iyi gidiyor","keyfim yerinde","gayet iyiyim","çok iyiyim","şükür iyi","fena değil","sağ ol","teşekkür"),
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


_EXPECTED_WELLBEING={
"en":("how about you","how are you","how are things with you","how s your day going","what about you"),
"tr":("senin tarafta nasıl","sen nasılsın","senin keyfin nasıl","sende nasıl gidiyor","sende durumlar nasıl","senden haberler nasıl"),
"zh":("你呢","你怎么样","你好吗","你最近怎么样"),
"ar":("وأنت","كيف حالك","كيف الأمور عندك","ماذا عنك"),
"hi":("तुम कैसे हो","आप कैसे हैं","तुम्हारा क्या हाल","तुम्हारे यहाँ कैसा"),
}
def _expected_reply(lang,text):
    value=_norm(text)
    return "wellbeing" if any(_norm(p) in value for p in _EXPECTED_WELLBEING.get(lang,())) else None

_MUBA_TOPICS={
"en":{"identity":("who is muba","what is muba"),"origin":("how did muba emerge","where did muba come from"),"difference":("what makes muba different",),"purpose":("why muba","why does muba exist"),"community":("community role",),"plan":("what comes next for muba",)},
"tr":{"identity":("muba kim","muba nedir","muba ne"),"origin":("muba nasıl ortaya çıktı","muba nereden çıktı"),"difference":("muba farkı","muba'yı farklı"),"purpose":("neden muba","muba neden var"),"community":("muba topluluk","topluluğun rolü"),"plan":("muba sırada","muba gelecek")},
"zh":{"identity":("muba 是什么","muba是谁"),"origin":("muba 如何出现","muba 起源"),"difference":("muba 有什么不同",),"purpose":("muba 为什么","muba 目标"),"community":("muba 社区",),"plan":("muba 接下来","muba 未来")},
"ar":{"identity":("ما هو muba","من هو muba"),"origin":("كيف ظهر muba","نشأة muba"),"difference":("ما الذي يجعل muba مختلف",),"purpose":("لماذا muba","هدف muba"),"community":("مجتمع muba",),"plan":("مستقبل muba",)},
"hi":{"identity":("muba क्या है","muba कौन है"),"origin":("muba कैसे शुरू","muba शुरुआत"),"difference":("muba को अलग",),"purpose":("muba क्यों","muba उद्देश्य"),"community":("muba समुदाय",),"plan":("muba आगे","muba भविष्य")},
}
def _muba_answer(lang,topic):
    from assistant_mode import QUESTIONS,answer_for_question
    for i,(t,_) in enumerate(QUESTIONS[lang]):
        if t==topic:return answer_for_question(lang,i)
    return None
def _contains_any(value,phrases):
    return any(_norm(p) in value for p in phrases)

def reply(user_id,lang,text):
    state=_STATE.get(user_id)
    if not state or state.get("lang")!=lang: return None
    if time.monotonic()-state.get("at",0)>_TTL:
        clear(user_id); return None
    previous=_norm(state.get("assistant",""))
    current=_norm(text)
    turns=list(state.get("turns",[])); turns.append(("user",text or "")); state["turns"]=turns[-8:]
    if not previous or not current: return None
    for topic,phrases in _MUBA_TOPICS.get(lang,{}).items():
        if _contains_any(current,phrases): return _muba_answer(lang,topic)
    if state.get("expected_reply")=="wellbeing" or _contains_any(previous,_WELLBEING_ASK.get(lang,())):
        if _contains_any(current,_NEGATIVE.get(lang,())): return _REPLY_NEG[lang]
        if _contains_any(current,_POSITIVE.get(lang,())): return _REPLY_POS[lang]
    return None
