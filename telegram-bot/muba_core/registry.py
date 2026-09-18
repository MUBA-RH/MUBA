"""Central registry: the only component allowed to discover specialist layers."""
from __future__ import annotations
import importlib

LAYER_MODULES={
 'authority':'layers.01_authority.layer','identity':'layers.02_identity.layer','security':'layers.03_security.layer',
 'official_knowledge':'layers.04_official_knowledge.layer','sources':'layers.05_sources.layer','ca':'layers.06_ca.layer',
 'current_information':'layers.07_current_information.layer','user_memory':'layers.08_user_memory.layer',
 'group_memory':'layers.09_group_memory.layer','context':'layers.10_context.layer','timeline':'layers.11_timeline.layer',
 'social':'layers.12_social.layer','language':'layers.13_language.layer','humor':'layers.14_humor.layer',
 'emotional':'layers.15_emotional.layer','conflict':'layers.16_conflict.layer','risk':'layers.17_risk.layer',
 'incident':'layers.18_incident.layer','moderation':'layers.19_moderation.layer','learning':'layers.20_learning.layer',
 'culture':'layers.21_culture.layer','topic_memory':'layers.22_topic_memory.layer','archive':'layers.23_archive.layer',
}

class LayerRegistry:
 def __init__(self): self._cache={}
 def get(self,name):
  if name not in self._cache: self._cache[name]=importlib.import_module(LAYER_MODULES[name]).LAYER
  return self._cache[name]
 def names(self): return tuple(LAYER_MODULES)
