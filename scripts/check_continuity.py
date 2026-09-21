#!/usr/bin/env python3
"""Continuity gate for MUBA user-facing changes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/"muba_history.json"
LANGS=("en","tr","zh","ar","hi")
TYPES={"new","updated","improved","fixed"}

def load_text(text):
    data=json.loads(text)
    entries=data.get("entries")
    if not isinstance(entries,list):
        raise SystemExit("muba_history.json must contain an entries list")
    ids=[]
    for item in entries:
        item_id=item.get("id")
        if not item_id or item_id in ids:
            raise SystemExit("history entry IDs must be unique and non-empty")
        ids.append(item_id)
        if item.get("type") not in TYPES:
            raise SystemExit(f"invalid history type for {item_id}")
        if not item.get("date") or not item.get("areas"):
            raise SystemExit(f"history entry {item_id} needs date and areas")
        for field in ("title","text"):
            localized=item.get(field) or {}
            missing=[lang for lang in LANGS if not localized.get(lang)]
            if missing:
                raise SystemExit(f"history entry {item_id} missing {field}: {','.join(missing)}")
    return data

def changed_files(base):
    result=subprocess.run(
        ["git","diff","--name-only",f"{base}...HEAD"],
        cwd=ROOT,text=True,capture_output=True,check=True
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def is_user_facing(path):
    protected_policy_paths={
        "LICENSE.md",
        "muba_authorizations.json",
        "MUBA_PERMISSION_TEMPLATE.json",
        "scripts/muba_permission_gate.py",
        "docs/MUBA_PERMISSION_MODEL.md",
    }
    if path in protected_policy_paths:
        return True
    if path=="index.html" or path.startswith("android-v3/"):
        return True
    if not path.startswith("telegram-bot/"):
        return False
    rel=path[len("telegram-bot/"):]
    if rel.startswith("tests/") or rel.endswith(".md") or rel.endswith(".txt"):
        return False
    return rel.endswith((".py",".json",".html"))

def git_show(ref,path):
    result=subprocess.run(["git","show",f"{ref}:{path}"],cwd=ROOT,text=True,capture_output=True)
    return result.stdout if result.returncode==0 else None

def main():
    current=load_text(HISTORY.read_text(encoding="utf-8"))
    base=os.getenv("BASE_REF","").strip()
    if not base:
        print("Continuity schema OK.")
        return 0
    if not base.startswith(("HEAD","origin/")):
        base="origin/"+base
    changed=changed_files(base)
    touches_product=any(is_user_facing(path) for path in changed)
    history_changed="muba_history.json" in changed
    old_text=git_show(base,"muba_history.json")
    if old_text:
        old=load_text(old_text)
        current_by_id={item["id"]:item for item in current["entries"]}
        for item in old["entries"]:
            if current_by_id.get(item["id"])!=item:
                raise SystemExit(f"append-only violation: historical entry changed or removed: {item['id']}")
        old_ids={item["id"] for item in old["entries"]}
        new_ids=[item["id"] for item in current["entries"] if item["id"] not in old_ids]
    else:
        new_ids=[item["id"] for item in current["entries"]]
    if touches_product and (not history_changed or not new_ids):
        raise SystemExit("user-facing MUBA changes require a new muba_history.json entry")
    print(f"Continuity OK: {len(changed)} changed files, {len(new_ids)} new history entries.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
