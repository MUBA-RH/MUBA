"""Strict Group Guardian policy and DEV-only command gate."""
from __future__ import annotations
import re, time
import threading
import tempfile
from pathlib import Path
from state import JSONRepository
from urllib.parse import urlsplit
from collections import defaultdict, deque

DEV_ID=934598759
GROUP_ID=-1004485415245

COMMANDS={
 "#START":"Resume Guardian.","#STOP":"Pause Guardian.","#GUARDIAN":"Show Guardian status.",
 "#STATUS":"Show Guardian status.","#HELP":"Show DEV command list.","#SECURITY":"Show security posture.",
 "#LOCKDOWN":"Enable strict lockdown.","#NORMAL":"Return to normal protection.","#WARN":"Warn the replied-to user.",
 "#MUTE":"Mute the replied-to user.","#UNMUTE":"Unmute the replied-to user.","#BAN":"Ban the replied-to user.",
 "#UNBAN":"Unban a user by numeric ID.","#DELETE":"Delete the replied-to message.",
}

_LINK_RE=re.compile(r"(?:(?:https?://|www\.)[^\s<>()]+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s<>()]*)?)",re.I)
_ADDR_RE=re.compile(r"\b(?:0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})\b")
_SCAM=("fake ca","sahte ca","scam","phishing","airdrop claim","connect wallet","seed phrase","private key","wallet verify","doğrula cüzdan","cüzdanını bağla")
_ALLOWED_LINKS={("muba-rh.github.io","/MUBA"),("x.com","/MUBA_RH"),("t.me","/MUBA_RH")}
_rate=defaultdict(lambda:deque(maxlen=12))
_security_lock=threading.RLock()
_fallback_store=None
MUTE_SECONDS=30*60

def _store():
 from muba_brain import STORE
 if isinstance(STORE,JSONRepository): return STORE
 # A local file preserves process restarts even when the general brain is in
 # memory. It is explicitly NOT durable across ephemeral-host replacement.
 global _fallback_store
 if _fallback_store is None:
  _fallback_store=JSONRepository(str(Path(tempfile.gettempdir())/'muba-guardian-state.json'))
 return _fallback_store

def security_storage_status():
 from muba_brain import STORE
 return {'backend':'json','durability':'configured_file' if isinstance(STORE,JSONRepository) else 'local_process_only'}

def _security_state():
 return _store().get('guardian_security',str(GROUP_ID),{'lockdown':False,'fake_ca':{},'risk':{}})

def _increment(category,user_id):
 with _security_lock:
  state=_security_state(); counts=state.setdefault(category,{})
  key=str(int(user_id)); counts[key]=int(counts.get(key,0))+1
  _store().set('guardian_security',str(GROUP_ID),state)
  return counts[key]

def is_guardian_group(chat_id): return chat_id==GROUP_ID
def is_dev(user_id): return user_id==DEV_ID
def command(text):
 value=(text or "").strip().split(maxsplit=1)[0]
 return value if value in COMMANDS else None
def is_control_attempt(text): return (text or "").strip().startswith("#")
def authorized_command(chat_id,user_id,text):
 cmd=command(text)
 return cmd if cmd and is_guardian_group(chat_id) and is_dev(user_id) else None
def set_lockdown(value):
 with _security_lock:
  state=_security_state(); state['lockdown']=bool(value)
  _store().set('guardian_security',str(GROUP_ID),state)
def lockdown_enabled(): return bool(_security_state().get('lockdown',False))
def command_arg(text):
 parts=(text or "").strip().split(maxsplit=1)
 return parts[1].strip() if len(parts)>1 else ""
def status_text(paused=False,lang='en'):
 from muba_runtime_text import guardian_status
 return guardian_status(paused,lockdown_enabled(),lang)
def help_text(lang='en'):
 if lang!='en':
  from muba_runtime_text import guardian_help
  return guardian_help(lang)
 return """🛡️ GUARDIAN DEV COMMANDS
#START / #STOP — resume / pause
#STATUS / #GUARDIAN — status
#SECURITY — security posture
#LOCKDOWN / #NORMAL — protection mode
#WARN — warn replied user
#MUTE / #UNMUTE — restrict replied user
#BAN — ban replied user
#UNBAN <user_id> — unban numeric user ID
#DELETE — delete replied message
#HELP — this list"""
def security_text(paused=False,lang='en'):
 if lang!='en':
  from muba_runtime_text import guardian_status
  return guardian_status(paused,lockdown_enabled(),lang,security=True)
 if paused:
  return "🛡️ Security: PAUSED\nRuntime protection: OFF until #START\nConfigured mode: "+("LOCKDOWN" if lockdown_enabled() else "NORMAL")+"\nDEV-only control: ON"
 return "🛡️ Security: "+("LOCKDOWN" if lockdown_enabled() else "NORMAL")+"\nRuntime protection: ON\nFake CA: 1st=MUTE / 2nd=BAN\nExternal links: DELETE\nFlood detection: ON\nDEV-only control: ON"

def _clean_url(raw):
 value=(raw or "").rstrip(".,!?;:)]}>'\"")
 if not re.match(r"^[a-z]+://",value,re.I):
  value="https://"+value.removeprefix("www.")
 return value

def is_official_link(raw):
 try:
  p=urlsplit(_clean_url(raw))
  host=(p.hostname or "").casefold()
  path=(p.path or "").rstrip("/") or "/"
  return (host,path) in _ALLOWED_LINKS and not p.username and not p.password
 except Exception:
  return False

def links_in(text): return _LINK_RE.findall(text or "")
def fake_ca_strikes(user_id): return _security_state().get('fake_ca',{}).get(str(int(user_id)),0)
def reset_runtime_security_state():
 with _security_lock:
  state=_security_state(); state['fake_ca']={}; state['risk']={}
  _store().set('guardian_security',str(GROUP_ID),state); _rate.clear()
def register_fake_ca(user_id):
 return _increment('fake_ca',user_id)
def register_risk(user_id):
 return _increment('risk',user_id)
def _credential_theft(v):
 return any(x in v for x in ("seed phrase","private key","recovery phrase","mnemonic","seed kelim","özel anahtar"))
def _wallet_lure(v):
 wallet=any(x in v for x in ("connect wallet","wallet verify","verify wallet","cüzdanını bağla","cüzdan bağla","doğrula cüzdan"))
 lure=any(x in v for x in ("claim","airdrop","giveaway","reward","ödül","bedava","free token"))
 return wallet and lure

def inspect_message(chat_id,user_id,text,now=None):
 """Return a Guardian event. Automatic sanctions always remain bound to sender numeric ID."""
 if not is_guardian_group(chat_id) or is_dev(user_id): return None
 v=(text or "").casefold()
 if is_control_attempt(text): return {"kind":"unauthorized_control","action":"silent"}

 # Official CA is not configured yet: every contract-shaped address is unverified.
 if _ADDR_RE.search(text or ""):
  strike=register_fake_ca(user_id)
  return {"kind":"security","subkind":"fake_ca","action":"mute" if strike==1 else "ban","strike":strike,
          "mute_seconds":MUTE_SECONDS,
          "text":"🚨 GUARDIAN: Fake/unverified CA detected — user muted." if strike==1
                 else "🚨 GUARDIAN: Repeated fake/unverified CA — user banned."}

 links=links_in(text)
 if links and any(not is_official_link(url) for url in links):
  if _credential_theft(v) or _wallet_lure(v):
   strike=register_risk(user_id)
   return {"kind":"suspicious_link","subkind":"phishing","action":"mute" if strike==1 else "ban",
           "strike":strike,"mute_seconds":MUTE_SECONDS,
           "text":"🚨 GUARDIAN: High-risk phishing pattern detected — user muted." if strike==1 else "🚨 GUARDIAN: Repeated high-risk phishing — user banned."}
  return {"kind":"suspicious_link","subkind":"blocked_link","action":"delete","text":"🚨 GUARDIAN: Only official MUBA links are allowed."}

 if _credential_theft(v) and any(x in v for x in ("send ","share ","give me","dm me","gönder","paylaş","yolla")):
  strike=register_risk(user_id)
  return {"kind":"security","subkind":"credential_theft","action":"mute" if strike==1 else "ban",
          "strike":strike,"mute_seconds":MUTE_SECONDS,
          "text":"🚨 GUARDIAN: Credential-theft pattern detected — user muted." if strike==1 else "🚨 GUARDIAN: Repeated credential-theft pattern — user banned."}

 if any(x in v for x in _SCAM):
  return {"kind":"security","action":"warn","text":"🚨 GUARDIAN: Scam-like content detected. Trust only official MUBA sources."}

 now=time.time() if now is None else now
 key=(chat_id,user_id); q=_rate[key]; q.append(now)
 recent=[x for x in q if now-x<=8]
 if len(recent)>=7:
  return {"kind":"flood","action":"warn","text":"⚠️ GUARDIAN: Flood/spam activity detected."}
 return None
