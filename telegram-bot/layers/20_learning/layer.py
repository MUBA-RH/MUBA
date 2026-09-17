from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('what can you learn','permanent knowledge','remember tomorrow','ne öğren','kalıcı bilgi','记住明天','ذاكرة دائمة','कल याद','स्थायी ज्ञान','क्या याद')
 if any(x in v for x in keys): return signal('learning','memory_policy',.93,'learning and permanence boundary semantics')
 return None
LAYER=SpecialistLayer('learning',740,match)
