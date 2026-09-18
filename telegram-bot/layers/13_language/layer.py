import re

from layers.common import SpecialistLayer, signal


def detect(text):
    value=text.lower()
    if any('\u4e00' <= c <= '\u9fff' for c in text): return 'zh'
    if any('\u0600' <= c <= '\u06ff' for c in text): return 'ar'
    if any('\u0900' <= c <= '\u097f' for c in text): return 'hi'
    tokens=set(re.findall(r'[^\\W\\d_]+',value,re.UNICODE))
    turkish={
        'selam','merhaba','günaydın','nasılsın','bugün','nasıl','nedir',
        'neden','hafıza','kim','ne','zaman','nerede','hangi','mı','mi','mu',
        'mü','ben','bana','biz','siz','bu','şu','için','hakkında','amaç',
        'plan','ekip','kurucu','yakında','öğren','hatırla','kaynak','kanıt',
    }
    if any(c in value for c in 'çğıöşü') or tokens & turkish: return 'tr'
    return 'en'


def match(message, context):
    lang=message.language or detect(message.text)
    return signal('language','language',1.0,'script and lexical language detection',language=lang)

LAYER=SpecialistLayer('language',1000,match)
