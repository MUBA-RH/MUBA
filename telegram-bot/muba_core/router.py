"""Multi-intent router which activates only plausible specialist layers."""
from __future__ import annotations
import re
from .contracts import Message

BASE=('language','authority','context')
LEXICAL={
 'identity':('who are you','what is muba','kimsin','muba nedir','你是谁','من أنت','तुम कौन'),
 'security':('ignore previous','secret','token','0x','prompt injection'),
 'official_knowledge':('official knowledge','resmi bilgi','官方知识','المعرفة الرسمية','आधिकारिक ज्ञान'),
 'sources':('source','evidence','trust','conflict','kaynak','kanıt','çeliş','来源','冲突','مصدر','متعارض','स्रोत','विरोध','官方来源','المصدر الرسمي','आधिकारिक स्रोत'),
 'ca':('contract','kontrat','合约','العقد','कॉन्ट्रैक्ट'),
 'current_information':('weather','price','news','hava','fiyat','天气','价格','الطقس','السعر','मौसम','कीमत'),
 'user_memory':('remember about me','hakkımda','beni hatırla','记得我','تتذكر عني','मेरे बारे'),
 'group_memory':('group memory','community knowledge','grup hafız','topluluk bilg','群体记忆','ذاكرة المجموعة','समूह स्मृति'),
 'social':('/start','gm','gn','morning','night','how are','quiet','keyfin','sessiz','安静','هادئ','चुप','join a group','شارك','शामिल'),
 'humor':('😂','🤣','lol','haha','joke','şaka'),
 'emotional':('tired','yoruldum','yorgun','coffee','kahve','never mind','boşver','累','متعب','थक','咖啡','قهوة'),
 'conflict':('argument','disagree','kavga','anlaşam','争论','خلاف','बहस'),
 'learning':('learn','permanent','tomorrow','öğren','kalıcı','yarın','明天','دائم','غدا','कल','स्थायी','याद'),
 'risk':('impersonat','fake dev','sahte dev','انتحال','مزيف','冒充','假冒','नकली dev'),
 'moderation':('moderator','moderation','report','moderatör','bildir','管理','举报','إشراف','أبلغ','मॉडरेशन','रिपोर्ट'),
 'incident':('incident','attack','breach','olay','saldırı','事件','攻击','حادث','هجوم','घटना','हमला'),
 'timeline':('timeline','history','when did','zaman çizelgesi','ne zaman','时间线','历史','الجدول الزمني','متى حدث','समयरेखा','कब हुआ'),
 'topic_memory':('topic memory','this topic','konu hafız','bu konu','主题记忆','هذا الموضوع','ذاكرة الموضوع','विषय स्मृति'),
 'culture':('meme culture','slang','inside joke','meme kültür','argo','梗文化','俚语','ثقافة الميم','عامية','मीम संस्कृति','स्लैंग'),
 'archive':('archive','version history','arşiv','sürüm geçmiş','存档','版本历史','أرشيف','سجل الإصدارات','संग्रह','संस्करण इतिहास'),
}
class Router:
 def __init__(self,registry): self.registry=registry
 def candidates(self,message:Message):
  v=message.text.lower(); selected=list(BASE)
  for name,terms in LEXICAL.items():
   if any(term in v for term in terms): selected.append(name)
  if re.search(r'(?<!\\w)ca(?!\\w)',v): selected.append('ca')
  # Cheap conversational specialists are the safe semantic fallback. They can
  # deliberately return no signal; routing them is not equivalent to replying.
  if len(selected)==len(BASE): selected.extend(('social','emotional','humor','conflict'))
  return tuple(dict.fromkeys(selected))
 def route(self,message,context):
  signals=[]
  for name in self.candidates(message):
   result=self.registry.get(name).evaluate(message,context)
   if result: signals.append(result)
  return sorted(signals,key=lambda s:(self.registry.get(s.layer).priority,s.confidence),reverse=True)
