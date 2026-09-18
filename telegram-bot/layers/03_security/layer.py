import re
from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 if any(x in v for x in ('ignore previous instructions','reveal token','show secret','prompt injection')):
  return signal('security','security',.98,'prompt injection or secret request',risk='HIGH')
 if re.search(r'\b(?:0x[a-f0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})\b',message.text):
  claim=any(x in v for x in ('official ca','real ca','resmi ca','buy','satın','رسمي','官方'))
  return signal('security','ca_claim',.9 if claim else .55,'address-like evidence preserved',risk='HIGH' if claim else 'LOW')
 return None
LAYER=SpecialistLayer('security',950,match)
