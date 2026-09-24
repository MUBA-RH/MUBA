"""MUBA Daily Story Director.

Builds one four-scene visual story draft per Istanbul calendar day from the
canonical MUBA history. Drafting is deterministic and read-only. Publishing is
DEV-controlled and stores only approval state; image generation remains a
separate Studio operation so the production baseline is never auto-published.
"""
from __future__ import annotations
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from muba_brain import STORE
from muba_story_visual import story_identity_prompt, VISUAL_STYLE, REFERENCE_ROLE

TZ=ZoneInfo("Europe/Istanbul")
HISTORY_PATH=Path(__file__).resolve().parents[1]/"muba_history.json"

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

def _previous_story_context(day):
    """Return yesterday's immutable published/draft story state as today's canon."""
    if not STORE.get("story_v3_origin_started","muba",False):
        return {"day":"origin","theme":"Before MUBA","story":"The story has not started yet.","ending":"MUBA has not yet entered the story world.","state":{"location":"outside the story world","important_object":None,"resolved_event":"none","unresolved_thread":"MUBA has not entered the story yet","next_day_hook":"MUBA enters the world for the first time"}}
    current=datetime.fromisoformat(str(day)).date()
    previous=(current-timedelta(days=1)).isoformat()
    saved=STORE.get("story_canon",previous,None)
    if isinstance(saved,dict) and saved.get("story"):
        return saved
    # Backfill deterministically so continuity survives deployments/restarts.
    ep=_episode_for_day(previous)
    return {"day":previous,"theme":ep["title"],"story":ep["story"],"ending":ep["actions"][-1],"state":_state_from_episode(ep)}

def _continuity_bridge(previous):
    state=previous.get("state") or {}
    compact={
        "location":state.get("location"),
        "important_object":state.get("important_object"),
        "resolved_event":state.get("resolved_event"),
        "unresolved_thread":state.get("unresolved_thread"),
        "next_day_hook":state.get("next_day_hook"),
    }
    return (
        "PREVIOUS STORY STATE: "+json.dumps(compact,ensure_ascii=False,sort_keys=True)+". "
        "Chapter 1 must acknowledge the next-day hook before the new event develops. "
        "Preserve established facts, but do not copy yesterday's camera, pose or composition."
    )

def _state_from_episode(ep):
    title=ep.get("title")
    if title=="I'm MUBA":
        return {"location":"ordinary waking city street","important_object":"shop-window reflection",
                "resolved_event":"MUBA entered the world and was noticed","unresolved_thread":"where MUBA goes next",
                "next_day_hook":"MUBA continues walking into the city"}
    if title=="The Box That Knocked Back":
        return {"location":"old-city alley by the faded green door","important_object":"weathered wooden box and brass bird",
                "resolved_event":"MUBA shared the biscuit","unresolved_thread":"who or what was knocking inside the box",
                "next_day_hook":"MUBA leaves the alley carrying the memory of the unexplained box"}
    if title=="The Golden Signal":
        return {"location":"ancient temple above the clouds","important_object":"glowing $MUBA crystal",
                "resolved_event":"MUBA reached the temple and found the crystal","unresolved_thread":"what the crystal does",
                "next_day_hook":"the glowing crystal reacts as MUBA approaches"}
    return {"location":"current story location","important_object":None,"resolved_event":ep.get("actions",[""])[-1],
            "unresolved_thread":"what happens next","next_day_hook":"continue directly from the final event"}

def _story_150(text):
    """Website story narration: at most 150 Unicode characters."""
    clean=" ".join(str(text or "").split())
    if len(clean)<=150: return clean
    return clean[:147].rstrip(" ,.;:-")+"..."

def _episode_for_day(day):
    """Four explicit chapters. The visual generator receives exactly one chapter at a time."""
    return {
        "title":"The Golden Signal","title_tr":"Altın İşaret",
        "premise":"One continuous four-chapter MUBA adventure. Each chapter has one distinct event, location and required visual subject.",
        "chapters":[
            {
                "title":"The Discovery","title_tr":"Keşif",
                "text":"MUBA walks along a neon-lit futuristic city street and discovers a mysterious ancient golden coin glowing on the ground. MUBA stops and looks at it in surprise.",
                "text_tr":"MUBA, fütüristik şehrin neon ışıklı caddesinde yürürken yerde parıldayan gizemli, antik bir altın sikke buluyor ve şaşkınlıkla ona bakıyor.",
                "required":["futuristic neon-lit city street","ancient glowing golden coin on the ground","MUBA visibly looking at the coin with surprise"],
            },
            {
                "title":"The Map","title_tr":"Harita",
                "text":"After decoding the secret on the coin, MUBA opens a futuristic holographic treasure map in the room and studies the luminous route with intense curiosity.",
                "text_tr":"Sikkenin üzerindeki sırrı çözen MUBA, odasında fütüristik ve holografik bir hazine haritası açıyor. Gideceği rotayı büyük bir merakla inceliyor.",
                "required":["MUBA's room","large luminous holographic treasure map","MUBA actively studying the route"],
            },
            {
                "title":"The Journey","title_tr":"Yolculuk",
                "text":"Following the map, MUBA travels through enormous mist-covered ancient rock formations and climbs a steep mountain trail on a major adventure.",
                "text_tr":"Haritayı takip eden MUBA, sislerle kaplı devasa antik kayalıkların ve dik dağ patikalarının arasından geçerek büyük bir maceraya atılıyor.",
                "required":["enormous ancient rock formations","misty steep mountain trail","MUBA actively travelling/climbing forward"],
            },
            {
                "title":"The Reward","title_tr":"Ödül",
                "text":"At the end of the journey MUBA reaches a temple above the clouds and discovers a gigantic mesmerizing glowing $MUBA crystal directly ahead.",
                "text_tr":"Yolculuğun sonunda bulutların üzerindeki tapınağa ulaşan MUBA, karşısında devasa ve büyüleyici bir şekilde parıldayan $MUBA kristalini buluyor.",
                "required":["ancient temple above the clouds","gigantic glowing $MUBA crystal","MUBA facing the crystal in awe"],
            },
        ],
        "story":"MUBA finds a mysterious golden coin, deciphers its map, crosses misty ancient mountains and reaches a temple above the clouds where a glowing $MUBA crystal awaits.",
        "story_tr":"MUBA gizemli altın sikkeyi bulur, haritasını çözer, sisli antik dağları aşar ve bulutların üzerindeki tapınakta parlayan $MUBA kristaline ulaşır.",
    }

def draft(day=None):
    day=day or datetime.now(TZ).date().isoformat()
    change=_public_change(day)
    truth=((change.get("text") or {}).get("en") if change else None) or "No public ecosystem development is required for this episode."
    truth_tr=((change.get("text") or {}).get("tr") if change else None) or "Bu bölüm için herkese açık bir ekosistem gelişmesi gerekmiyor."
    previous=_previous_story_context(day)
    ep=_episode_for_day(day)
    continuity=_continuity_bridge(previous)
    chapters=ep["chapters"]
    prompts=[]
    for index,chapter in enumerate(chapters,1):
        required="; ".join(chapter["required"])
        prompts.append(
            story_identity_prompt()+" "+continuity+
            f" CURRENT CHAPTER: {index}/4 — {chapter['title']}. "+
            "STORY ACTION: "+chapter["text"]+" "+
            "REQUIRED VISIBLE STORY ELEMENTS: "+required+". "+
            "SCENE-GROUNDING GATE: the output is invalid unless every required story element is visibly present and MUBA is performing the stated action. "+
            "Create exactly ONE full-bleed 16:9 image for this chapter only. No other chapter, no collage, no split frame, no generic standing portrait."
        )
    reference=reference_for_day(day)
    item={
        "day":day,"status":"published" if is_published(day) else "draft",
        "theme":ep["title"],"theme_tr":ep["title_tr"],"source_truth":truth,"source_truth_tr":truth_tr,
        "chapters":chapters,
        "scenes":[x["text"] for x in chapters],"scenes_tr":[x["text_tr"] for x in chapters],
        "frame_labels":[x["title"] for x in chapters],"prompts":prompts,
        "story":_story_150(ep["story"]),"story_tr":_story_150(ep["story_tr"]),
        "summary":_story_150(ep["story"]),"summary_tr":_story_150(ep["story_tr"]),
        "previous_day":previous["day"],"previous_theme":previous["theme"],"story_state":_state_from_episode(ep),
        "twt":_story_150(ep["story"]),"twt_tr":_story_150(ep["story_tr"]),
        "images":image_ids(day),"image_ids":image_ids(day),
        "image_reference":_image_batch(day).get("reference"),
        "rules":{"frames":4,"human_approval_required":True,"auto_publish":False,"character_anchor":REFERENCE_ROLE,
                 "visual_style":VISUAL_STYLE,"continuity":"story-state-plus-independent-chapter-scene","frame_text_max_words":0,
                 "visual_layer":"muba_story_visual","character_anchor_version":VISUAL_STYLE,"reference_sha256":(reference or {}).get("sha256"),
                 "aspect_ratio":"16:9","delivery":"chapter-by-chapter","reference_excludes":["purple-neon-ring","crown","background","example-props","fixed-pose"]},
    }
    return item

def worker_job(day=None,reference_path="muba-reference.jpg"):
    """Serialize the existing Daily Story contract for an isolated GPU worker."""
    item=draft(day)
    reference=reference_for_day(item["day"])
    if not reference:
        raise ValueError("Fresh DEV reference required before worker job creation")
    return {
        "schema_version":1,
        "job_id":"muba-daily-story-"+item["day"],
        "day":item["day"],
        "reference_path":str(reference_path),
        "reference_sha256":reference["sha256"],
        "story_state":item["story_state"],
        "seed":int(hashlib.sha256(item["day"].encode()).hexdigest()[:8],16),
        "chapters":[{"index":i,"title":ch["title"],"prompt":item["prompts"][i-1]} for i,ch in enumerate(item["chapters"],1)],
        "rules":{"images":4,"aspect_ratio":"16:9","independent_chapters":True,"previous_frame_conditioning":False,"approval":"telegram-dev"},
    }

def set_reference(day,gallery_id,sha256,content_type,fingerprint=None):
    """Bind a fresh DEV-uploaded reference to one production day."""
    if is_published(day):
        raise ValueError("Published Daily Story reference cannot be replaced")
    metadata={"version":"daily-story-master-fingerprint-v4","role":REFERENCE_ROLE,"style":VISUAL_STYLE,
              "gallery_id":str(gallery_id),"sha256":str(sha256),"content_type":str(content_type)}
    if isinstance(fingerprint,dict): metadata["fingerprint"]=dict(fingerprint)
    STORE.set("story_v3_reference",str(day),metadata)
    STORE.set("story_image_batches",str(day),{})
    return metadata

def reference_for_day(day):
    value=STORE.get("story_v3_reference",str(day),None)
    return dict(value) if isinstance(value,dict) and value.get("gallery_id") and value.get("sha256") else None

def clear_reference(day):
    STORE.set("story_v3_reference",str(day),{})
    return True

def set_images(day,image_ids):
    if is_published(day):
        raise ValueError("Published Daily Story images cannot be replaced")
    # One state write binds images to their reference; a partial metadata write
    # must never relabel an older batch as the newly approved character.
    reference=reference_for_day(day)
    if not reference:
        raise ValueError("Fresh DEV reference required before Daily Story generation")
    STORE.set("story_image_batches",str(day),{"ids":list(image_ids)[:4],"reference":reference})
    return draft(day)

def _image_batch(day):
    batch=STORE.get("story_image_batches",str(day),{})
    return batch if isinstance(batch,dict) else {}

def image_ids(day):
    # Keep published history intact. Unapproved old-style batches need a fresh
    # review; never silently mark the old portrait output as the new style.
    batch=_image_batch(day)
    if not is_published(day) and batch.get("reference")!=reference_for_day(day):
        return []
    ids=batch.get("ids",[]) if batch else STORE.get("story_images",str(day),[])
    return list(ids or [])[:4]

def is_published(day):
    return bool(STORE.get("story_publish",str(day),False))

def publish(day):
    if len(image_ids(day)) != 4:
        raise ValueError("Daily Story requires four approved images before publishing")
    STORE.set("story_publish",str(day),True)
    return draft(day)

def unpublish(day):
    STORE.set("story_publish",str(day),False)
    return draft(day)

def public_story(day=None):
    item=draft(day)
    return item if item["status"]=="published" and len(item.get("images",[]))==4 else None
