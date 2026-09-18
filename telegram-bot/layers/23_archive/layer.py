from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('archive','version history','arşiv','sürüm geçmiş','存档','版本历史','أرشيف','سجل الإصدارات','संग्रह','संस्करण इतिहास')):
        return signal('archive','archive',.8,'archive/version semantics')
    return None

LAYER = SpecialistLayer('archive', 100, match)
