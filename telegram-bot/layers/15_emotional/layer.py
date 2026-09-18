from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 tired=('tired','exhausted','yoruldum','yorgunum','累','متعب','थक')
 disengage=('never mind','neyse boşver','算了','لا بأس','छोड़ो')
 if any(x in v for x in tired): return signal('emotional','fatigue',.9,'explicit fatigue cue, no diagnosis')
 if any(x in v for x in disengage): return signal('emotional','space',.88,'explicit request to disengage')
 if any(x in v for x in ('coffee','kahve','咖啡','قهوة','कॉफी')): return signal('emotional','casual',.7,'low-risk casual invitation')
 return None
LAYER=SpecialistLayer('emotional',580,match)
