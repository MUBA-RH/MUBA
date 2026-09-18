"""Stable public adapter for the modular MUBA brain.

Transport code imports this module; all reasoning lives in muba_core and isolated layers.
"""
from __future__ import annotations
import importlib, os
from types import MappingProxyType
from muba_core import Message, MubaCore, VERSION
from muba_core.actions import create as _create_action, transition as _transition_action, verify as _verify_action
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
def reset_runtime_state():
 global STORE,CORE
 STORE=MemoryRepository(); CORE=MubaCore(STORE)
def brain_self_test():
 return {'ok':build_reply('Who are you?',user_id=1).startswith("I'M MUBA"),'version':VERSION,'languages':[detect_language(x) for x in ('hello','merhaba nasılsın','你好','مرحبا','नमस्ते')]}
master_self_test=brain_self_test
