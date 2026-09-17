from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('group memory','community knowledge','group knowledge','grup hafız','topluluk bilg','群体记忆','ذاكرة المجموعة','समूह स्मृति')
 if any(x in v for x in keys): return signal('group_memory','group_memory',.9,'group-scoped memory semantics')
 return None
LAYER=SpecialistLayer('group_memory',710,match)
