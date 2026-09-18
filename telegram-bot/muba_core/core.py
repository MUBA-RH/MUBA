"""Protected central coordinator for the layered MUBA brain."""
from __future__ import annotations
import time
from .contracts import Message
from .decision_engine import DecisionEngine
from .registry import LayerRegistry
from .router import Router
from .operations import observe, remember_decision
from .semantic_conversation import resolve as resolve_semantic

VERSION='LAYERED-3.0'
class MubaCore:
 def __init__(self,repository):
  self.repository=repository; self.registry=LayerRegistry(); self.router=Router(self.registry); self.engine=DecisionEngine(repository); self.last_trace=None
 def process(self,message:Message):
  recent=self.repository.get('context',str(message.chat_id),[])
  signals=self.router.route(message,{'recent':recent})
  decision=self.engine.decide(message,signals)
  semantic=resolve_semantic(message.text,decision.language,recent)
  semantic_context=any(x.get('active_topic') in ('identity','difference','purpose','plan','community') for x in recent)
  protected={'security','impersonation','incident','ca_claim','ca','dev_identity','authority','moderation','official_sources','source_conflict','memory_policy','user_memory','group_memory','topic_memory','official_knowledge','current_information','timeline','archive','conflict','gm','gn','group_paused','unauthorized_group','self_message'}
  semantic_allowed=decision.trace.winning_rule in ('safe_fallback','deliberate_silence','casual','identity') or (semantic_context and decision.trace.winning_rule not in protected)
  if semantic and semantic_allowed:
   topic,response=semantic; decision.response=response; decision.intents=[topic]; decision.trace.winning_rule='semantic_'+topic
  self.last_trace=decision.trace
  observe(self.repository,message,decision)
  remember_decision(self.repository,message.chat_id,decision)
  if 'conflict' in decision.intents:
   self.repository.append('conflict',str(message.chat_id),{'participants':[message.user_id],'reply_graph':[],'subthreads':[],'claims':[{'text':message.text,'type':'interpretation'}],'agreements':[],'disagreements':[],'unresolved_questions':[],'evidence':[],'resolution_status':'open','level':1,'confidence':decision.trace.confidence,'at':time.time()},50)

  # Security/event evidence is append-only and scoped; it is not user truth.
  risk=next((s for s in signals if s.layer in ('security','risk','incident')),None)
  if risk:
   self.repository.append('security_event',str(message.chat_id),{'actor_id':message.user_id,'chat_id':message.chat_id,'timestamp':time.time(),'kind':risk.intent,'risk':risk.data.get('risk','MEDIUM'),'evidence':message.text,'decision':decision.trace.winning_rule,'action_request':None,'action_result':None},100)
  # Unauthorized groups and protected pause do not create conversational memory.
  if decision.trace.winning_rule not in ('unauthorized_group','group_paused'):
   self.repository.append('context',str(message.chat_id),{'user_id':message.user_id,'reply_to_user_id':message.reply_to_user_id,'text':message.text,'response':decision.response,'language':decision.language,'intents':decision.intents,'active_topic':decision.intents[0] if decision.intents else None,'unresolved':message.text if '?' in message.text and not decision.response else None,'social_state':decision.action.value,'conflict_state':'active' if 'conflict' in decision.intents else 'none','at':time.time()},20)
  self.repository.append('decision_trace',str(message.chat_id),{'layers':decision.trace.activated_layers,'suppressed':decision.trace.suppressed,'winner':decision.trace.winning_rule,'confidence':decision.trace.confidence,'state_changed':decision.trace.state_changed,'at':time.time()},100)
  return decision
