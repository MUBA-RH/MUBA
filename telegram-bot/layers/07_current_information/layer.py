from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 subjects=('weather','price','news','score','hava','fiyat','haber','天气','价格','الطقس','السعر','मौसम','कीमत')
 freshness=('today','now','latest','current','bugün','şimdi','güncel','今天','现在','最新','اليوم','الآن','आज','अभी')
 if any(x in v for x in subjects) and (any(x in v for x in freshness) or any(x in v for x in subjects)):
  subject='weather' if any(x in v for x in ('weather','hava','天气','الطقس','मौसम')) else 'general'
  return signal('current_information','current_information',.92,'freshness plus external subject evidence',subject=subject)
 return None
LAYER=SpecialistLayer('current_information',650,match)
