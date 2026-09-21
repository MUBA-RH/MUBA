"""Persistent-by-configuration archive for MUBA Studio creations.

The archive stores only public gallery metadata (label, kind, source, time)
and image bytes. It intentionally does not store Telegram IDs, usernames or
raw prompts.

Durability:
- MUBA_GALLERY_DIR -> preferred persistent gallery root.
- MUBA_MEMORY_FILE -> gallery uses a sibling directory when configured.
- otherwise -> temporary fallback, useful for runtime continuity but not
  durable across host replacement/redeploy.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_LOCK=threading.RLock()
_ID_RE=re.compile(r"^[a-f0-9]{24}$")
_ALLOWED_KINDS={"meme","image","sticker","emoji"}
_ALLOWED_TYPES={"image/png":".png","image/jpeg":".jpg","image/webp":".webp"}
_ALLOWED_VISIBILITY={"public","hidden","rejected"}

def _storage_root():
    configured=os.getenv("MUBA_GALLERY_DIR","").strip()
    if configured:
        return Path(configured), True
    memory_file=os.getenv("MUBA_MEMORY_FILE","").strip()
    if memory_file:
        return Path(memory_file).expanduser().resolve().parent/"muba-gallery", True
    render_disk=Path("/var/data")
    if render_disk.exists() and os.path.ismount(render_disk):
        return render_disk/"muba-gallery", True
    return Path(tempfile.gettempdir())/"muba-gallery", False

def storage_status():
    root,persistent=_storage_root()
    try:
        (root/"images").mkdir(parents=True,exist_ok=True)
        (root/"meta").mkdir(parents=True,exist_ok=True)
        probe=root/".write-test"
        probe.write_text("ok",encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable=True
    except OSError:
        writable=False
    return {"root":str(root),"persistent":persistent,"writable":writable}

def _normalize_kind(kind):
    value=(kind or "image").strip().casefold()
    if value=="reaction":
        value="emoji"
    return value if value in _ALLOWED_KINDS else "image"

def gallery_label(prompt,kind="image"):
    text=" ".join((prompt or "").strip().split())[:120]
    lower=text.casefold()
    rules=(
        (("astronaut","astronot","space suit","uzay kıyafet","uzay kiyafet"),"Astronaut MUBA"),
        (("heart eyes","kalp göz","kalp goz","😍"),"Heart Eyes MUBA"),
        (("crying","ağlayan","aglayan","sad tears","gözyaşı","gozyasi"),"Crying MUBA"),
        (("laughing","gülen","gulen","kahkaha","laugh"),"Laughing MUBA"),
        (("angry","kızgın","kizgin","sinirli"),"Angry MUBA"),
        (("surprised","şaşkın","saskin","şok","sok"),"Surprised MUBA"),
        (("sleepy","uykulu","sleeping","uyuyan"),"Sleepy MUBA"),
        (("grass","çim","cim","meadow"),"MUBA on the Grass"),
        (("beach","sahil","deniz","seaside","ocean"),"MUBA at the Beach"),
        (("moon","ayda","ay ","lunar"),"MUBA on the Moon"),
        (("city","şehir","sehir","neon city"),"MUBA in the City"),
    )
    for needles,label in rules:
        if any(n in lower for n in needles):
            return label
    cleaned=re.sub(r"\b(olsun|yap|yapalım|yapalim|oluştur|olustur|create|make|please|lütfen|lutfen)\b"," ",text,flags=re.I)
    cleaned=" ".join(cleaned.split()).strip(" .,-:;")
    if not cleaned:
        cleaned={"meme":"MUBA Meme","image":"MUBA Image","sticker":"MUBA Sticker","emoji":"MUBA Reaction"}.get(_normalize_kind(kind),"MUBA")
    if len(cleaned)>46:
        cleaned=cleaned[:43].rstrip()+"…"
    return cleaned[0].upper()+cleaned[1:] if cleaned else "MUBA"

def archive_creation(image_bytes,content_type,prompt,kind,source):
    if content_type not in _ALLOWED_TYPES:
        raise ValueError("unsupported image content type")
    if not image_bytes:
        raise ValueError("empty image")
    root,_=_storage_root()
    images=root/"images"; meta=root/"meta"
    with _LOCK:
        images.mkdir(parents=True,exist_ok=True)
        meta.mkdir(parents=True,exist_ok=True)
        stamp=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        digest=hashlib.sha256(image_bytes+stamp.encode("utf-8")).hexdigest()[:24]
        ext=_ALLOWED_TYPES[content_type]
        image_path=images/(digest+ext)
        meta_path=meta/(digest+".json")
        tmp=image_path.with_suffix(image_path.suffix+".tmp")
        tmp.write_bytes(image_bytes)
        os.replace(tmp,image_path)
        record={
            "id":digest,
            "label":gallery_label(prompt,kind),
            "kind":_normalize_kind(kind),
            "source":"telegram" if str(source).casefold()=="telegram" else "web",
            "created_at":stamp,
            "content_type":content_type,
            "file":image_path.name,
            "visibility":"public",
        }
        tmp_meta=meta_path.with_suffix(".json.tmp")
        tmp_meta.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True),encoding="utf-8")
        os.replace(tmp_meta,meta_path)
        return dict(record)

def _read_meta(item_id):
    if not _ID_RE.fullmatch(str(item_id or "")):
        return None
    root,_=_storage_root()
    meta_path=root/"meta"/(str(item_id)+".json")
    if not meta_path.exists():
        return None
    try:
        item=json.loads(meta_path.read_text(encoding="utf-8"))
        if "visibility" not in item:
            item["visibility"]="public"
        return item
    except (OSError,ValueError):
        return None

def get_gallery_item(item_id):
    item=_read_meta(item_id)
    return dict(item) if item else None

def set_gallery_visibility(item_id,visibility):
    visibility=str(visibility or "").casefold()
    if visibility not in _ALLOWED_VISIBILITY:
        raise ValueError("invalid gallery visibility")
    root,_=_storage_root()
    meta_path=root/"meta"/(str(item_id)+".json")
    with _LOCK:
        item=_read_meta(item_id)
        if not item:
            return None
        item["visibility"]=visibility
        tmp_meta=meta_path.with_suffix(".json.tmp")
        tmp_meta.write_text(json.dumps(item,ensure_ascii=False,sort_keys=True),encoding="utf-8")
        os.replace(tmp_meta,meta_path)
        return dict(item)

def list_gallery(limit=60,kind=None,visibility="public"):
    root,_=_storage_root()
    meta=root/"meta"
    if not meta.exists():
        return []
    wanted=_normalize_kind(kind) if kind else None
    if visibility is not None and visibility not in _ALLOWED_VISIBILITY:
        raise ValueError("invalid gallery visibility")
    rows=[]
    with _LOCK:
        for path in meta.glob("*.json"):
            try:
                item=json.loads(path.read_text(encoding="utf-8"))
            except (OSError,ValueError):
                continue
            item.setdefault("visibility","public")
            if wanted and item.get("kind")!=wanted:
                continue
            if visibility is not None and item.get("visibility")!=visibility:
                continue
            rows.append(item)
    rows.sort(key=lambda item:item.get("created_at",""),reverse=True)
    return rows[:max(1,min(int(limit or 60),120))]

def read_gallery_image(item_id,include_nonpublic=False):
    item=_read_meta(item_id)
    if not item:
        return None
    if not include_nonpublic and item.get("visibility","public")!="public":
        return None
    root,_=_storage_root()
    try:
        image_path=root/"images"/item["file"]
        return image_path.read_bytes(),item["content_type"]
    except (OSError,KeyError):
        return None
