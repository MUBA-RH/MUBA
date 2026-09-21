"""Stable public adapter for the modular MUBA brain.

Transport code imports this module; all reasoning lives in muba_core and isolated layers.
"""
from __future__ import annotations
import importlib, os
from types import MappingProxyType
from muba_core import Message, MubaCore, VERSION
from muba_core.actions import create as _create_action, transition as _transition_action, verify as _verify_action
from muba_core.operations import specification as _specification, health as _health, audit as _audit, close_incident as _close_incident, snapshot as _snapshot
from muba_core.memory import learning_candidate as _learning_candidate
from state import JSONRepository, MemoryRepository

BRAIN_VERSION=VERSION
MASTER_BRAIN_VERSION=VERSION
SUPPORTED_LANGUAGES=('en','tr','zh','ar','hi')
FOUNDER_DISPLAY_NAME='MUBA DEV'
FOUNDER_IDS={934598759}
AUTHORIZED_GROUP_IDS={-1004485415245}
MUBA_BOT_IDS={8661249663}
PROTECTED_OFFICIAL_SOURCES=MappingProxyType({'official_x':'@MUBA_RH','official_website':'https://muba-rh.github.io/MUBA/'})

def _repository():
 path=os.getenv('MUBA_MEMORY_FILE','').strip()
 return JSONRepository(path) if path else MemoryRepository()
STORE=_repository(); CORE=MubaCore(STORE)

def detect_language(text): return importlib.import_module('layers.13_language.layer').detect(text)
def contains_muba(text): return 'muba' in (text or '').casefold()
def detect_social_intent(text,language=None):
 result=importlib.import_module('layers.12_social.layer').match(Message(text,language=language),{})
 return result.intent if result else None
def build_reply(text,chat_id=0,language=None,user_id=None,**metadata):
 return CORE.process(_message(text,chat_id,language,user_id,metadata)).response
def build_decision(text,chat_id=0,language=None,user_id=None,**metadata):
 return CORE.process(_message(text,chat_id,language,user_id,metadata))
def _message(text,chat_id,language,user_id,metadata):
 reply_to=metadata.pop('reply_to_user_id',None); forwarded=bool(metadata.pop('is_forwarded',False))
 return Message(text=text or '',chat_id=int(chat_id or 0),user_id=user_id,language=language,reply_to_user_id=reply_to,is_forwarded=forwarded,metadata=metadata)
def is_founder(user_id): return user_id in FOUNDER_IDS
def is_authorized_group(chat_id): return chat_id in AUTHORIZED_GROUP_IDS
def is_muba_bot_id(user_id): return user_id in MUBA_BOT_IDS
def group_conversation_paused(chat_id): return bool(STORE.get('operations',str(chat_id),{}).get('paused',False))
def classify_knowledge_source(url): return importlib.import_module('layers.05_sources.policy').classify(url)
def research_current(query,source_url=None):
 if os.getenv('MUBA_WEB_ENABLED','0').lower() not in {'1','true','yes','on'}: return {'ok':False,'error':'web_disabled'}
 if not source_url: return {'ok':False,'error':'approved_source_required'}
 policy=importlib.import_module('layers.05_sources.policy')
 q=(query or '').casefold()
 subject='weather' if any(x in q for x in ('weather','hava','天气','الطقس','मौसम')) else ('muba' if 'muba' in q else 'general')
 if not policy.relevant_for(subject,source_url): return {'ok':False,'error':'source_not_relevant','subject':subject}
 return policy.retrieve(source_url)
def create_action(chat_id,actor_id,action,target=None,message_id=None): return _create_action(STORE,chat_id,message_id,target,action)
def update_action_state(action_id,state,actor_id=None,result=None): return _transition_action(STORE,action_id,state)
def verify_action_result(action_id,verified,actor_id=None,verification=None): return _verify_action(STORE,action_id,verified)
def get_master_brain_spec(): return _specification(VERSION,CORE.registry.names())
def master_health(): return _health(STORE,VERSION,CORE.registry.names())
def observe_message(text,chat_id=0,user_id=None,language=None,**metadata): return build_decision(text,chat_id,language,user_id,**metadata)
def record_audit(category,actor_id=None,chat_id=0,evidence=None): return _audit(STORE,category,actor_id,chat_id,evidence)
def queue_master_learning(scope,owner_id,value,provenance,confidence=.3): return _learning_candidate(STORE,scope,owner_id,value,provenance,confidence)
def remember_decision(chat_id,decision,provenance='manual'): return __import__('muba_core.operations',fromlist=['remember_decision']).remember_decision(STORE,chat_id,decision,provenance)
def close_incident(incident_id,actor_id,resolution): return _close_incident(STORE,incident_id,actor_id,resolution)
def memory_snapshot(): return _snapshot(STORE)
master_brain_specification=get_master_brain_spec
master_is_founder=is_founder
master_is_authorized_group=is_authorized_group
master_is_muba_bot=is_muba_bot_id
master_observe_message=observe_message
master_record_audit=record_audit
master_queue_learning=queue_master_learning
master_remember_decision=remember_decision
master_close_incident=close_incident
master_snapshot=memory_snapshot
def get_assistant_language(user_id):
 return STORE.get('assistant_language',str(user_id),None)
def set_assistant_language(user_id,language):
 if language not in SUPPORTED_LANGUAGES: return False
 STORE.set('assistant_language',str(user_id),language); return True
def clear_assistant_language(user_id):
 STORE.set('assistant_language',str(user_id),None)

def get_assistant_update_seen(user_id,area):
 return STORE.get('assistant_update_seen',str(user_id)+':'+str(area),None)
def mark_assistant_update_seen(user_id,area,update_id):
 STORE.set('assistant_update_seen',str(user_id)+':'+str(area),update_id)
 return True

def get_guardian_report_language():
 return STORE.get('guardian_report_settings','language',None)
def set_guardian_report_language(language):
 if language not in SUPPORTED_LANGUAGES: return False
 STORE.set('guardian_report_settings','language',language); return True
def append_guardian_violation(record):
 history=STORE.get('guardian_violation_history','all',[])
 history.append(dict(record or {}))
 STORE.set('guardian_violation_history','all',history)
 return len(history)-1
def guardian_violation_history(category=None):
 history=STORE.get('guardian_violation_history','all',[])
 if not category: return history
 return [item for item in history if item.get('category')==category]

def reset_runtime_state():
 global STORE,CORE
 STORE=MemoryRepository(); CORE=MubaCore(STORE)
def brain_self_test():
 return {'ok':build_reply('Who are you?',user_id=1).startswith("I'M MUBA"),'version':VERSION,'languages':[detect_language(x) for x in ('hello','merhaba nasılsın','你好','مرحبا','नमस्ते')]}
master_self_test=brain_self_test
