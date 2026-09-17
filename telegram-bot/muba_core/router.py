"""Multi-intent router which activates only plausible specialist layers."""
from __future__ import annotations
from .contracts import Message

BASE=('language','authority','context')
LEXICAL={
 'identity':('who are you','what is muba','kimsin','muba nedir','你是谁','من أنت','तुम कौन'),
 'security':('ignore previous','secret','token','0x','prompt injection'),
 'official_knowledge':('official knowledge','resmi bilgi','官方知识','المعرفة الرسمية','आधिकारिक ज्ञान'),
 'sources':('source','evidence','trust','conflict','kaynak','kanıt','çeliş','来源','冲突','مصدر','متعارض','स्रोत','विरोध','官方来源','المصدر الرسمي','आधिकारिक स्रोत'),
 'ca':(' ca','contract','kontrat','合约','العقد','कॉन्ट्रैक्ट'),
 'current_information':('weather','price','news','hava','fiyat','天气','价格','الطقس','السعر','मौसम','कीमत'),
 'user_memory':('remember about me','hakkımda','beni hatırla','记得我','تتذكر عني','मेरे बारे'),
 'group_memory':('group memory','community knowledge','grup hafız','topluluk bilg','群体记忆','ذاكرة المجموعة','समूह स्मृति'),
 'social':('/start','gm','gn','morning','night','how are','quiet','keyfin','sessiz','安静','هادئ','चुप','join a group','شارك','शामिल'),
 'humor':('😂','🤣','lol','haha','joke','şaka'),
 'emotional':('tired','yoruldum','yorgun','coffee','kahve','never mind','boşver','累','متعب','थक','咖啡','قهوة'),
 'conflict':('argument','disagree','kavga','anlaşam','争论','خلاف','बहस'),
 'learning':('learn','permanent','tomorrow','öğren','kalıcı','yarın','明天','دائم','غدا','कल','स्थायी','याद'),
}
class Router:
 def __init__(self,registry): self.registry=registry
 def candidates(self,message:Message):
  v=message.text.lower(); selected=list(BASE)
  for name,terms in LEXICAL.items():
   if any(term in v for term in terms): selected.append(name)
  if len(selected)==len(BASE): selected.extend(('social','emotional'))
  return tuple(dict.fromkeys(selected))
 def route(self,message,context):
  signals=[]
  for name in self.candidates(message):
   result=self.registry.get(name).evaluate(message,context)
   if result: signals.append(result)
  return sorted(signals,key=lambda s:(self.registry.get(s.layer).priority,s.confidence),reverse=True)
