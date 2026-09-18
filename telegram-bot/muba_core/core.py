"""Protected central coordinator for the layered MUBA brain."""
from __future__ import annotations
import time
from .contracts import Message
from .decision_engine import DecisionEngine
from .registry import LayerRegistry
from .router import Router
from .operations import observe, remember_decision

VERSION='LAYERED-3.0'
class MubaCore:
 def __init__(self,repository):
  self.repository=repository; self.registry=LayerRegistry(); self.router=Router(self.registry); self.engine=DecisionEngine(repository); self.last_trace=None
 def process(self,message:Message):
  recent=self.repository.get('context',str(message.chat_id),[])
  signals=self.router.route(message,{'recent':recent})
  decision=self.engine.decide(message,signals); self.last_trace=decision.trace
  observe(self.repository,message,decision)
  remember_decision(self.repository,message.chat_id,decision)
  if 'conflict' in decision.intents:
   self.repository.append('conflict',str(message.chat_id),{'participants':[message.user_id],'reply_graph':[],'subthreads':[],'claims':[{'text':message.text,'type':'interpretation'}],'agreements':[],'disagreements':[],'unresolved_questions':[],'evidence':[],'resolution_status':'open','level':1,'confidence':decision.trace.confidence,'at':time.time()},50)
  # Unauthorized groups and protected pause do not create conversational memory.
  if decision.trace.winning_rule not in ('unauthorized_group','group_paused'):
   self.repository.append('context',str(message.chat_id),{'user_id':message.user_id,'text':message.text,'response':decision.response,'language':decision.language,'intents':decision.intents,'at':time.time()},20)
  self.repository.append('decision_trace',str(message.chat_id),{'layers':decision.trace.activated_layers,'suppressed':decision.trace.suppressed,'winner':decision.trace.winning_rule,'confidence':decision.trace.confidence,'state_changed':decision.trace.state_changed,'at':time.time()},100)
  return decision
