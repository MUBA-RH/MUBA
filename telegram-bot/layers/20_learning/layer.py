from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('what can you learn','permanent knowledge','remember tomorrow','what can you remember','ne öğren','kalıcı bilgi','yarın neyi hatırla','记住明天','永久知识','ماذا تتذكر','ذاكرة دائمة','معرفة دائمة','कल याद','स्थायी ज्ञान','क्या याद')
 if any(x in v for x in keys): return signal('learning','memory_policy',.93,'learning and permanence boundary semantics')
 return None
LAYER=SpecialistLayer('learning',740,match)
