from layers.common import SpecialistLayer, signal

def match(message, context):
 previous=context.get('recent',[])
 if previous: return signal('context','context',.65,'relevant recent turns available',recent=previous[-4:])
 return None
LAYER=SpecialistLayer('context',980,match)
