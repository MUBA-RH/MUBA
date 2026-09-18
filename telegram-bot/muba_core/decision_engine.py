"""Deterministic arbitration and response policy."""
from __future__ import annotations
import hashlib, time
from .contracts import Action, Decision, DecisionTrace
from .locales import choices as locale_choices
from .locales import text as locale_text

class DecisionEngine:
 def __init__(self,repository): self.repo=repository
 def decide(self,message,signals):
  lang=next((s.data.get('language') for s in signals if s.layer=='language'),'en'); intents=[s.intent for s in signals if s.intent not in ('language','context')]
  trace=DecisionTrace([s.layer for s in signals],[s.reason for s in signals],confidence=max((s.confidence for s in signals),default=.4))
  if message.user_id == 8661249663:
   trace.winning_rule='self_message'; return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
  auth=next((s for s in signals if s.intent=='protected_command'),None)
  if auth:
   trace.winning_rule='protected_numeric_authority'
   if not auth.data.get('authenticated'): return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
   paused=auth.data['command']=='#STOP'; self.repo.set('operations',str(message.chat_id),{'paused':paused,'actor':message.user_id,'at':time.time()}); trace.state_changed=True
   return Decision(Action.PROTECTED_COMMAND,'MUBA DEV' if paused else '',lang,intents,trace)
  paused=self.repo.get('operations',str(message.chat_id),{}).get('paused',False)
  if paused: trace.winning_rule='group_paused'; return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
  if message.chat_id < 0 and message.chat_id != -1004485415245: trace.winning_rule='unauthorized_group'; return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
  priority=('security','impersonation','incident','ca_claim','ca','authority','moderation','official_sources','source_conflict','memory_policy','user_memory','group_memory','topic_memory','official_knowledge','identity','current_information','timeline','archive','culture','fatigue','space','conflict','social','start','casual','humor','gm','gn')
  chosen=next((x for x in priority if x in intents),None); trace.winning_rule=chosen or 'safe_fallback'
  if chosen in ('security','impersonation','ca_claim'): response=locale_text(lang,'ca') if chosen=='ca_claim' else locale_text(lang,'security_rejected')
  elif chosen=='ca': response=locale_text(lang,'ca')
  elif chosen=='authority': response=locale_text(lang,'authority')
  elif chosen=='incident': response=locale_text(lang,'incident')
  elif chosen=='moderation': response=locale_text(lang,'moderation')
  elif chosen=='official_sources': response=locale_text(lang,'official_sources')
  elif chosen=='source_conflict': response=locale_text(lang,'source_conflict')
  elif chosen in ('memory_policy','official_knowledge'): response=locale_text(lang,'memory_policy')
  elif chosen=='user_memory': response=locale_text(lang,'user_memory')
  elif chosen=='group_memory': response=locale_text(lang,'group_memory')
  elif chosen=='identity': response=locale_text(lang,'identity')
  elif chosen=='current_information': response=locale_text(lang,'current_information')
  elif chosen in ('topic_memory','timeline','archive'):
   response=locale_text(lang,'topic_records')
  elif chosen=='culture':
   response=locale_text(lang,'culture')
  elif chosen=='fatigue': response=locale_text(lang,'fatigue')
  elif chosen=='space': response=locale_text(lang,'space')
  elif chosen in ('gm','gn'):
   local_day=str(message.metadata.get('local_date') or time.strftime('%Y-%m-%d',time.gmtime())); wave=f'{message.chat_id}:{local_day}:{chosen}'; users=set(self.repo.get('social_wave',wave,[])); users.add(message.user_id); self.repo.set('social_wave',wave,list(users));
   if len(users)<3: return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
   last=self.repo.get('social_sent',wave,0); now=time.time()
   if now-last<86400: return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
   response=locale_text(lang,chosen); self.repo.set('social_sent',wave,now)
  elif chosen in ('social','start','casual','humor'):
   options=locale_choices(lang,'social'); seed=f'{message.chat_id}:{message.user_id}:{message.text}:{len(self.repo.get("context",str(message.chat_id),[]))}'; response=options[int(hashlib.sha256(seed.encode()).hexdigest(),16)%len(options)]
  elif chosen=='conflict': response=locale_text(lang,'conflict')
  else:
   recent=next((s.data.get('recent',[]) for s in signals if s.intent=='context'),[])
   fatigue=next((turn for turn in reversed(recent) if 'fatigue' in turn.get('intents',[])),None)
   if fatigue and any(x in message.text.lower() for x in ('why','neden','为什么','لماذا','क्यों')):
    response=locale_text(lang,'fatigue_followup')
   elif message.chat_id < 0 and '?' not in message.text and message.reply_to_user_id != 8661249663:
    trace.winning_rule='deliberate_silence'; return Decision(Action.SILENT,language=lang,intents=intents,trace=trace)
   else: response=locale_text(lang,'fallback')
  action=Action.CONFLICT_SUPPORT if chosen=='conflict' else Action.DIRECT_REPLY
  return Decision(action,response,lang,intents,trace)
