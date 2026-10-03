"""Pause only a quota-limited provider. Never buy capacity or choose a fallback.

This is a response-driven circuit breaker, not a provider billing meter. A paid
account that silently bills overage must be capped at the provider dashboard.
"""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from state import JSONRepository

_lock=threading.RLock()
_backend=None
_memory={}

class ProviderQuotaPaused(RuntimeError):
    def __init__(self,provider,until):
        self.provider=provider
        self.until=float(until)
        super().__init__('Provider quota is unavailable; this connection is temporarily paused. Other MUBA areas remain available.')
    @property
    def retry_after(self):
        return max(1,int(self.until-time.time()+1))

def _store():
    global _backend
    if _backend is None:
        configured=os.getenv('MUBA_QUOTA_STATE_FILE')
        memory_file=os.getenv('MUBA_MEMORY_FILE')
        path=Path(configured) if configured else (Path(memory_file).with_name('muba-free-quota-state.json') if memory_file else Path(tempfile.gettempdir())/'muba-free-quota-state.json')
        _backend=JSONRepository(str(path))
    return _backend

def _read(provider):
    try:
        row=_store().get('provider_quota',provider,None)
    except (OSError,ValueError):
        row=None
    try: saved=float((row or {}).get('until',0))
    except (ValueError,TypeError,AttributeError): saved=0
    return max(saved,float(_memory.get(provider,0)))

def ensure_available(provider):
    with _lock:
        until=_read(provider)
        if until>time.time():
            raise ProviderQuotaPaused(provider,until)

def _limited(status,detail,headers):
    text=str(detail or '').casefold()
    return status in (402,429) or (status>=400 and (
        any(word in text for word in ('quota','daily free allocation','rate limit','ratelimit','too many requests','insufficient credits','credits exhausted','resource exhausted','gpu limit','usage limit exceeded'))
        or str(headers.get('X-RateLimit-Remaining',headers.get('x-ratelimit-remaining','')))=='0'))

def _until(provider,detail,headers):
    now=time.time()
    text=str(detail or '').casefold()
    if provider=='cloudflare_ai' and any(word in text for word in ('daily','free allocation','quota')):
        return (datetime.fromtimestamp(now,timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1)).timestamp()
    value=headers.get('Retry-After',headers.get('retry-after'))
    if value:
        try: return now+max(1,min(float(value),604800))
        except (ValueError,TypeError):
            try: return max(now+1,min(parsedate_to_datetime(str(value)).timestamp(),now+604800))
            except (ValueError,TypeError,OverflowError): pass
    reset=headers.get('X-RateLimit-Reset',headers.get('x-ratelimit-reset'))
    if reset:
        try: return max(now+1,min(float(reset),now+604800))
        except (ValueError,TypeError): pass
    # Unknown reset times are rechecked only on a later request, never by a loop.
    return now+(3600 if provider in ('huggingface','kaggle','cloudflare_ai') else 300)

def guard_response(provider,status,detail='',headers=None):
    headers=headers or {}
    if not _limited(status,detail,headers): return
    with _lock:
        until=max(_read(provider),_until(provider,detail,headers))
        _memory[provider]=until
        try: _store().set('provider_quota',provider,{'until':until})
        except (OSError,ValueError): pass
    raise ProviderQuotaPaused(provider,until)

def guard_exception(provider,error):
    # SDK errors do not necessarily expose an HTTP status.
    detail=str(error)
    match=re.search(r'\b(402|429)\b',detail)
    guard_response(provider,int(match.group(1)) if match else 503,detail)

def quota_status():
    with _lock:
        return {provider:{'paused':_read(provider)>time.time(),
                          'retry_after':max(0,int(_read(provider)-time.time()+1))}
                for provider in ('cloudflare_ai','huggingface','kaggle','github','r2','prices')}
