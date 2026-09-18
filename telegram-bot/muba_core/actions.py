"""Verified action lifecycle; SENT is never completion."""
from __future__ import annotations
import time, uuid
VALID=('REQUESTED','QUEUED','SENT','ACKNOWLEDGED','VERIFIED','FAILED')
NEXT={'REQUESTED':{'QUEUED','SENT','FAILED'},'QUEUED':{'SENT','FAILED'},'SENT':{'ACKNOWLEDGED','FAILED'},'ACKNOWLEDGED':{'FAILED'},'FAILED':set(),'VERIFIED':set()}
def create(repository,chat_id,message_id,target,requested):
 key=f'{chat_id}:{message_id}:{requested}'
 existing=repository.get('action_identity',key)
 if existing: return existing
 action_id=uuid.uuid4().hex
 repository.set('actions',action_id,{'id':action_id,'chat_id':chat_id,'message_id':message_id,'target':target,'requested':requested,'state':'REQUESTED','verification':None,'at':time.time()})
 repository.set('action_identity',key,action_id); return action_id
def transition(repository,action_id,state):
 if state not in VALID or state=='VERIFIED': return False
 item=repository.get('actions',action_id)
 if not item: return False
 if state not in NEXT.get(item['state'],set()): return False
 item['state']=state; item['updated_at']=time.time(); repository.set('actions',action_id,item); return True
def verify(repository,action_id,verified):
 item=repository.get('actions',action_id)
 if not item: return False
 if item['state'] not in {'SENT','ACKNOWLEDGED'}: return False
 item['verification']={'verified':bool(verified),'at':time.time()}; item['state']='VERIFIED' if verified else 'FAILED'; repository.set('actions',action_id,item); return True
