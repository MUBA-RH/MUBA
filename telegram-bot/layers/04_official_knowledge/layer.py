from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('official knowledge','resmi bilgi','官方知识','المعرفة الرسمية','आधिकारिक ज्ञान')
 if any(x in v for x in keys): return signal('official_knowledge','official_knowledge',.9,'explicit protected knowledge question')
 return None
LAYER=SpecialistLayer('official_knowledge',760,match)
