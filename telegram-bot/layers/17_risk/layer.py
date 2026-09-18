from layers.common import SpecialistLayer, signal

def match(message, context):
    v=message.text.lower()
    if any(x in v for x in ('impersonat','fake dev','sahte dev','انتحال','مزيف','冒充','假冒','नकली dev')):
        return signal('risk','impersonation',.91,'possible identity impersonation',risk='HIGH')
    return None

LAYER = SpecialistLayer('risk', 100, match)
