"""MUBA Daily Story Director.

Builds one four-scene visual story draft per Istanbul calendar day from the
canonical MUBA history. Drafting is deterministic and read-only. Publishing is
DEV-controlled and stores only approval state; image generation remains a
separate Studio operation so the production baseline is never auto-published.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from muba_brain import STORE

TZ=ZoneInfo("Europe/Istanbul")
HISTORY_PATH=Path(__file__).resolve().parents[1]/"muba_history.json"

CHARACTER_ANCHOR=(
    "Preserve the supplied MUBA reference identity: large expressive eyes, tan short dense fur, "
    "small nose, playful tongue, and the same recognizable face proportions. Do not redesign the face. "
    "No anime, no comic-book treatment, no hard glossy CGI. Use soft cinematic, tactile, lightly surreal "
    "photographic-illustrative storytelling. The world adapts to MUBA; MUBA is not redesigned for the world."
)

def _history():
    try:
        payload=json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return list(payload.get("entries",[]))
    except (OSError,ValueError):
        return []

def _public_change(day):
    # Technical-only maintenance is not forced into the story. Prefer the newest
    # user-facing change from today, then fall back to MUBA's established world.
    for item in _history():
        if item.get("date")!=day: continue
        areas=set(item.get("areas",()))
        if areas & {"assistant","daily","gallery","studio","web","telegram","guardian"}:
            return item
    return None

def draft(day=None):
    day=day or datetime.now(TZ).date().isoformat()
    change=_public_change(day)
    if change:
        title=(change.get("title") or {}).get("en") or "A new MUBA day"
        fact=(change.get("text") or {}).get("en") or title
        theme=f"MUBA encounters a real change in its own living ecosystem: {title}."
        truth=fact
    else:
        theme="A quiet day inside MUBA's living world becomes a small unexpected character moment."
        truth="No public ecosystem development is required for this episode."\n        theme_tr="MUBA’nın yaşayan dünyasındaki sakin bir gün, küçük ve beklenmedik bir karakter anına dönüşüyor."\n        truth_tr="Bu bölüm için herkese açık bir ekosistem gelişmesi gerekmiyor."
    scenes=[
        "Opening: establish one believable place and mood. MUBA notices the day's situation without explanatory text.",
        "Development: show MUBA interacting with the situation; preserve location, light, wardrobe and object continuity.",
        "MUBA moment: a distinctive playful or curious reaction makes the event feel like MUBA rather than a product announcement.",
        "Closing: resolve the small event with a memorable visual beat that can stand as the final frame of the day.",
    ]
    scenes_tr=[\n        "Açılış: inandırıcı bir mekân ve atmosfer kurulur. MUBA, açıklayıcı yazı olmadan günün durumunu fark eder.",\n        "Gelişme: MUBA durumla etkileşime girer; mekân, ışık, kıyafet ve nesne devamlılığı korunur.",\n        "MUBA anı: özgün, oyuncu veya meraklı bir tepki olayı ürün duyurusundan çıkarıp MUBA hikâyesine dönüştürür.",\n        "Kapanış: küçük olay, günün son karesi olarak tek başına da güçlü durabilecek akılda kalıcı bir görsel anla tamamlanır.",\n    ]\n    prompts=[f"{CHARACTER_ANCHOR} {theme} {scene} No visible captions, logos, speech bubbles or watermarks." for scene in scenes]
    return {
        "day":day,"status":"published" if is_published(day) else "draft",
        "theme":theme,"theme_tr":theme_tr,"source_truth":truth,"source_truth_tr":truth_tr,"scenes":scenes,"scenes_tr":scenes_tr,"prompts":prompts,
        "twt":"MUBA keeps moving. Today simply became part of the story.",
        "twt_tr":"MUBA ilerlemeye devam ediyor. Bugün de hikâyenin bir parçası oldu.",
        "images":image_ids(day),
        "rules":{"frames":4,"human_approval_required":True,"auto_publish":False,"character_anchor":"reference-image"},
    }

def set_images(day,image_ids):
    STORE.set("story_images",str(day),list(image_ids)[:4])
    return draft(day)

def image_ids(day):
    return list(STORE.get("story_images",str(day),[]) or [])[:4]

def is_published(day):
    return bool(STORE.get("story_publish",str(day),False))

def publish(day):
    STORE.set("story_publish",str(day),True)
    return draft(day)

def unpublish(day):
    STORE.set("story_publish",str(day),False)
    return draft(day)

def public_story(day=None):
    item=draft(day)
    return item if item["status"]=="published" else None
