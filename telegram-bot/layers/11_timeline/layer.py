from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('timeline','history','when did','zaman çizelgesi','ne zaman oldu','时间线','历史','الجدول الزمني','متى حدث','समयरेखा','कब हुआ')):
        return signal('timeline','timeline',.78,'timeline/history semantics')
    return None

LAYER = SpecialistLayer('timeline', 100, match)
