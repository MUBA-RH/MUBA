"""Canonical MUBA history loader shared by Assistant, Daily and tests."""
from __future__ import annotations

import json
from pathlib import Path

_HISTORY_PATH=Path(__file__).resolve().parents[1]/"muba_history.json"
_LANGS=("en","tr","zh","ar","hi")
_TYPES=("new","updated","improved","fixed")

def load_history():
    data=json.loads(_HISTORY_PATH.read_text(encoding="utf-8"))
    entries=list(data.get("entries") or [])
    seen=set()
    for item in entries:
        item_id=str(item.get("id") or "")
        if not item_id or item_id in seen:
            raise ValueError("MUBA history IDs must be non-empty and unique")
        seen.add(item_id)
        if item.get("type") not in _TYPES:
            raise ValueError(f"Unsupported MUBA history type: {item.get('type')}")
        for field in ("title","text"):
            localized=item.get(field) or {}
            if any(not localized.get(lang) for lang in _LANGS):
                raise ValueError(f"MUBA history entry {item_id} lacks five-language {field}")
    return data

HISTORY=load_history()
UPDATES=HISTORY["entries"]

def entries(lang="en",area=None):
    lang=lang if lang in _LANGS else "en"
    rows=[item for item in UPDATES if not area or area in item.get("areas",())]
    return [dict(item,title_text=item["title"].get(lang,item["title"]["en"]),text=item["text"].get(lang,item["text"]["en"])) for item in rows]

def latest_id(area=None):
    rows=entries("en",area)
    return rows[0]["id"] if rows else None

def has_unseen(area,seen_id):
    latest=latest_id(area)
    return bool(latest and seen_id!=latest)

def badge_type(area,seen_id):
    if not has_unseen(area,seen_id):
        return ""
    for item in UPDATES:
        if area in item.get("areas",()):
            return item["type"]
    return "new"

def devlog(lang="en"):
    lang=lang if lang in _LANGS else "en"
    grouped={"new":[],"updates":[],"fixed":[]}
    for item in UPDATES:
        category="new" if item["type"]=="new" else ("updates" if item["type"]=="updated" else "fixed")
        text=item["text"].get(lang,item["text"]["en"])
        grouped[category].append(f'{item["date"]} — {text}')
    return grouped
