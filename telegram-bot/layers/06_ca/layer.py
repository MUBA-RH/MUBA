import re

from layers.common import SpecialistLayer, signal

def match(message, context):
 v=message.text.lower()
 if re.search(r'(?<!\w)ca(?!\w)',v) or any(x in v for x in ('contract address','contract adres','kontrat adres','合约地址','عنوان العقد','कॉन्ट्रैक्ट')):
  return signal('ca','ca',.98,'contract-address semantics')
 return None
LAYER=SpecialistLayer('ca',930,match)
