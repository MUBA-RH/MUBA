from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('serious incident','security incident','breach','attack','güvenlik olayı','saldırı','安全事件','攻击','حادث أمني','هجوم','सुरक्षा घटना','हमला')):
        return signal('incident','incident',.86,'serious incident semantics',risk='HIGH')
    return None

LAYER = SpecialistLayer('incident', 100, match)
