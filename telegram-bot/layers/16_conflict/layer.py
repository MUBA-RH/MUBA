from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 keys=('argument','disagree','conflict','kavga','anlaşam','争论','خلاف','बहस')
 if any(x in v for x in keys): return signal('conflict','conflict',.82,'temporary conflict structure requested',level=1)
 return None
LAYER=SpecialistLayer('conflict',820,match)
