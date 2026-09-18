"""Strict Group Guardian command gate.

Guardian operates only in the authorized MUBA group. Administrative commands are
accepted only from the numeric MUBA DEV account. Everyone else is ignored.
"""
from __future__ import annotations

DEV_ID = 934598759
GROUP_ID = -1004485415245

COMMANDS = {
    "#START": "Resume Guardian protected processing.",
    "#STOP": "Pause Guardian protected processing.",
    "#GUARDIAN": "Show Guardian status.",
    "#STATUS": "Show Guardian status.",
    "#HELP": "Show DEV command list.",
}

def is_guardian_group(chat_id):
    return chat_id == GROUP_ID

def is_dev(user_id):
    return user_id == DEV_ID

def command(text):
    value=(text or "").strip().upper()
    return value if value in COMMANDS else None

def is_control_attempt(text):
    value=(text or "").strip()
    return value.startswith("#")

def authorized_command(chat_id,user_id,text):
    cmd=command(text)
    if not cmd or not is_guardian_group(chat_id) or not is_dev(user_id):
        return None
    return cmd

def status_text(paused=False):
    state="PAUSED" if paused else "ACTIVE"
    return (
        "🛡️ GUARDIAN — "+state+"\n"
        "Main group: LOCKED\n"
        "Command authority: MUBA DEV ONLY"
    )

def help_text():
    return (
        "🛡️ GUARDIAN DEV COMMANDS\n"
        "#START — resume Guardian\n"
        "#STOP — pause Guardian\n"
        "#GUARDIAN / #STATUS — status\n"
        "#HELP — command list"
    )
