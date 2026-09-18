"""Deterministic modular router.

Every specialist is cheap and side-effect free at evaluation time, so every
message is offered to every specialist. This avoids a second, duplicated
keyword router becoming a source of missed intents. Specialists remain fully
isolated; the decision engine arbitrates only the signals they emit.
"""
from __future__ import annotations

class Router:
 def __init__(self,registry): self.registry=registry
 def candidates(self,message):
  return self.registry.names()
 def route(self,message,context):
  signals=[]
  for name in self.candidates(message):
   result=self.registry.get(name).evaluate(message,context)
   if result: signals.append(result)
  return sorted(signals,key=lambda s:(self.registry.get(s.layer).priority,s.confidence),reverse=True)
