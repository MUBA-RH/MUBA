from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('remember about me','what do you remember','beni hatırla','hakkımda','记得我','تتذكر عني','मेरे बारे में याद')
 if any(x in v for x in keys): return signal('user_memory','user_memory',.9,'user-scoped memory semantics')
 return None
LAYER=SpecialistLayer('user_memory',720,match)
