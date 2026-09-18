"""Scoped memory and reversible learning operations."""
from __future__ import annotations
import time, uuid
PROTECTED_SCOPES={'core_identity','official_knowledge','official_sources','authority','permanent_security','ca'}
STAGES=('CANDIDATE','OBSERVED','TRUSTED') # OFFICIAL requires the protected Founder/source process.

def remember(repository,scope,owner_id,value,provenance,confidence=.5):
 if scope in PROTECTED_SCOPES: return False
 item={'id':uuid.uuid4().hex,'value':value,'provenance':provenance,'confidence':max(0.0,min(1.0,confidence)),'scope':scope,'owner_id':owner_id,'created_at':time.time(),'version':1,'status':'active'}
 repository.append(f'memory:{scope}',str(owner_id),item,500); return item['id']
def recall(repository,scope,owner_id): return repository.get(f'memory:{scope}',str(owner_id),[])
def learning_candidate(repository,scope,owner_id,value,provenance,confidence=.3):
 if scope in PROTECTED_SCOPES: return None
 item={'id':uuid.uuid4().hex,'value':value,'scope':scope,'owner_id':owner_id,'provenance':provenance,'confidence':confidence,'maturity':'CANDIDATE','reversible':True,'created_at':time.time()}
 repository.set('learning',item['id'],item); return item['id']
def mature(repository,item_id,stage):
 if stage not in STAGES: return False
 item=repository.get('learning',item_id)
 if not item or STAGES.index(stage)<STAGES.index(item['maturity']): return False
 item['maturity']=stage; repository.set('learning',item_id,item); return True
def forget(repository,item_id):
 item=repository.get('learning',item_id)
 if not item or not item.get('reversible'): return False
 item['status']='removed'; item['removed_at']=time.time(); repository.set('learning',item_id,item); return True
