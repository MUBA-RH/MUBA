from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 if any(x in v for x in ('😂','🤣','lol','haha','şaka','joke')):
  return signal('humor','humor',.58,'humor cue supported by conversational context')
 return None
LAYER=SpecialistLayer('humor',420,match)
