import re

from layers.common import SpecialistLayer, signal

TURKISH_WORDS={
    "selam","merhaba","günaydın","nasılsın","bugün","nasıl","nedir",
    "neden","hafıza","kim","ne","zaman","nerede","hangi","mı","mi","mu",
    "mü","ben","bana","biz","siz","bu","şu","için","hakkında","amaç",
    "plan","ekip","kurucu","yakında","öğren","hatırla","kaynak","kanıt",
}
ENGLISH_WORDS={
    "hello","hi","hey","what","who","when","where","why","how","is","are",
    "the","you","your","about","source","memory","founder","soon",
}
# Project/technical tokens such as MUBA, CA and dev are intentionally neutral.
# They are commonly embedded in non-English sentences and must not bias the
# language detector toward English.

def detect(text):
    value=(text or "").casefold()
    if any("\u4e00" <= c <= "\u9fff" for c in value): return "zh"
    if any("\u0600" <= c <= "\u06ff" for c in value): return "ar"
    if any("\u0900" <= c <= "\u097f" for c in value): return "hi"
    tokens=set(re.findall(r"[^\W\d_]+",value,flags=re.UNICODE))
    if any(c in value for c in "çğıöşü"): return "tr"
    tr_score=len(tokens & TURKISH_WORDS)
    en_score=len(tokens & ENGLISH_WORDS)
    if tr_score > en_score: return "tr"
    return "en"

def match(message, context):
    lang=message.language or detect(message.text)
    return signal("language","language",1.0,"script and scored lexical language detection",language=lang)

LAYER=SpecialistLayer("language",1000,match)
