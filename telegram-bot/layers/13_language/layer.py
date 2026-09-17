from layers.common import SpecialistLayer, signal


def detect(text):
    value=text.lower()
    if any('\u4e00' <= c <= '\u9fff' for c in text): return 'zh'
    if any('\u0600' <= c <= '\u06ff' for c in text): return 'ar'
    if any('\u0900' <= c <= '\u097f' for c in text): return 'hi'
    if any(c in value for c in 'çğıöşü') or any(w in value.split() for w in ('bugün','nasıl','nedir','neden','hafıza')): return 'tr'
    return 'en'


def match(message, context):
    lang=message.language or detect(message.text)
    return signal('language','language',1.0,'script and lexical language detection',language=lang)

LAYER=SpecialistLayer('language',1000,match)
