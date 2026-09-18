"""Strict Group Guardian policy and DEV-only command gate."""
from __future__ import annotations
import re, time\nfrom urllib.parse import urlsplit
from collections import defaultdict, deque

DEV_ID=934598759
GROUP_ID=-1004485415245

COMMANDS={
 "#START":"Resume Guardian.",
 "#STOP":"Pause Guardian.",
 "#GUARDIAN":"Show Guardian status.",
 "#STATUS":"Show Guardian status.",
 "#HELP":"Show DEV command list.",
 "#SECURITY":"Show security posture.",
 "#LOCKDOWN":"Enable strict lockdown.",
 "#NORMAL":"Return to normal protection.",
 "#WARN":"Warn the replied-to user.",
 "#MUTE":"Mute the replied-to user.",
 "#UNMUTE":"Unmute the replied-to user.",
 "#BAN":"Ban the replied-to user.",
 "#UNBAN":"Unban a user by numeric ID.",
 "#DELETE":"Delete the replied-to message.",
}

_LINK_RE=re.compile(r"(?:https?://|www\.)\S+",re.I)
_ADDR_RE=re.compile(r"\b(?:0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})\b")
_SCAM=("fake ca","sahte ca","scam","phishing","airdrop claim","connect wallet","seed phrase","private key","wallet verify","doğrula cüzdan","cüzdanını bağla")
_rate=defaultdict(lambda:deque(maxlen=12))
_lockdown=False

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
 global _lockdown; _lockdown=bool(value)
def lockdown_enabled(): return _lockdown
def command_arg(text):
 parts=(text or "").strip().split(maxsplit=1)
 return parts[1].strip() if len(parts)>1 else ""
def status_text(paused=False):
 return "🛡️ GUARDIAN — "+("PAUSED" if paused else "ACTIVE")+"\nMain group: LOCKED\nCommand authority: MUBA DEV ONLY\nSecurity: "+("LOCKDOWN" if _lockdown else "NORMAL")
def help_text():
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
def security_text():
 return "🛡️ Security: "+("LOCKDOWN" if _lockdown else "NORMAL")+"\nFake CA/scam: ON\nSuspicious links: ON\nFlood detection: ON\nDEV-only control: ON"

def inspect_message(chat_id,user_id,text,now=None):
 """Return passive Guardian event; never treats ordinary users as command authority."""
 if not is_guardian_group(chat_id) or is_dev(user_id): return None
 v=(text or "").casefold()
 if is_control_attempt(text): return {"kind":"unauthorized_control","action":"silent"}
 if _LINK_RE.search(text or "") and (_lockdown or any(x in v for x in ("claim","airdrop","wallet","verify","connect","giveaway"))):
  return {"kind":"suspicious_link","action":"warn","text":"🚨 GUARDIAN: Suspicious link pattern detected. Do not connect wallets or share credentials."}
 if any(x in v for x in _SCAM) or _ADDR_RE.search(text or ""):
  return {"kind":"security","action":"warn","text":"🚨 GUARDIAN: Unverified CA / scam-like content detected. Trust only official MUBA sources."}
 now=time.time() if now is None else now
 key=(chat_id,user_id); q=_rate[key]; q.append(now)
 recent=[x for x in q if now-x<=8]
 if len(recent)>=7:
  return {"kind":"flood","action":"warn","text":"⚠️ GUARDIAN: Flood/spam activity detected."}
 return None
