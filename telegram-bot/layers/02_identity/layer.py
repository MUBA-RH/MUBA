from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 patterns=('who are you','what is muba','sen kimsin','muba nedir','你是谁','ما هو muba','من أنت','तुम कौन','muba क्या')
 if any(x in v for x in patterns): return signal('identity','identity',.95,'explicit identity question')
 return None
LAYER=SpecialistLayer('identity',700,match)
