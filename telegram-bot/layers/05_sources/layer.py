from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 if any(x in v for x in ('official source','resmi kaynak','官方来源','المصدر الرسمي','आधिकारिक स्रोत')):
  return signal('sources','official_sources',.96,'explicit official-source question')
 keys=('source','evidence','provenance','trust','conflicting information','kaynak','kanıt','çelişkili','来源','冲突','مصدر','متعارضة','स्रोत','परस्पर विरोधी')
 if any(x in v for x in keys): return signal('sources','source_conflict',.9,'source, provenance, or conflict semantics')
 return None
LAYER=SpecialistLayer('sources',800,match)
