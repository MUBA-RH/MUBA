from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('remember about me','what do you remember','remember that i','beni hatırla','hakkımda','记得我','记住我','تتذكر عني','تذكر أنني','मेरे बारे में याद','याद रखो कि मैं')
 if any(x in v for x in keys): return signal('user_memory','user_memory',.9,'user-scoped memory semantics')
 return None
LAYER=SpecialistLayer('user_memory',720,match)
