"""MUBA Gallery archive with Cloudflare R2 persistence and local fallback.

Public Gallery metadata intentionally excludes Telegram IDs, usernames, raw prompts
and credentials.

Backend selection:
- Cloudflare R2 when R2 credentials are configured;
- otherwise the existing configured local persistent path;
- otherwise a temporary local fallback.

When R2 is configured, archive operations never silently fall back to temporary
local storage. R2 failures are surfaced to the caller so a generation can remain
successful without falsely claiming durable archival.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from typing import Optional

import httpx

_LOCK=threading.RLock()
_ID_RE=re.compile(r"^[a-f0-9]{24}$")
_ALLOWED_KINDS={"meme","image","sticker","emoji"}
_ALLOWED_TYPES={"image/png":".png","image/jpeg":".jpg","image/webp":".webp"}
_ALLOWED_VISIBILITY={"public","hidden","rejected"}
_R2_INDEX_KEY="gallery/index.json"


class GalleryStorageError(RuntimeError):
    pass


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


def _r2_config():
    account=(os.getenv("MUBA_R2_ACCOUNT_ID") or os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
    access=os.getenv("MUBA_R2_ACCESS_KEY_ID","").strip()
    secret=os.getenv("MUBA_R2_SECRET_ACCESS_KEY","").strip()
    bucket=os.getenv("MUBA_R2_BUCKET","muba-gallery").strip() or "muba-gallery"
    credentials=(account,access,secret)
    if any(credentials) and not all(credentials):
        missing=[
            name for name,value in (
                ("account id",account),
                ("access key id",access),
                ("secret access key",secret),
            ) if not value
        ]
        raise GalleryStorageError("Incomplete R2 configuration: "+", ".join(missing))
    if not all(credentials):
        return None
    return {"account":account,"access":access,"secret":secret,"bucket":bucket}


def _r2_enabled():
    return _r2_config() is not None


def _aws_quote(value):
    return quote(str(value),safe="-_.~")


def _r2_request(method,key="",body=b"",content_type=None,query=None,allow_missing=False):
    cfg=_r2_config()
    if not cfg:
        raise GalleryStorageError("R2 is not configured.")
    method=method.upper()
    body=body or b""
    if isinstance(body,str):
        body=body.encode("utf-8")
    host=f'{cfg["account"]}.r2.cloudflarestorage.com'
    bucket_path=_aws_quote(cfg["bucket"])
    key_path="/".join(_aws_quote(part) for part in str(key).split("/") if part!="")
    canonical_uri=f"/{bucket_path}"+(f"/{key_path}" if key_path else "")
    query=query or {}
    pairs=[]
    for qkey,qvalue in query.items():
        if isinstance(qvalue,(list,tuple)):
            for item in qvalue:
                pairs.append((_aws_quote(qkey),_aws_quote(item)))
        else:
            pairs.append((_aws_quote(qkey),_aws_quote(qvalue)))
    pairs.sort()
    canonical_query="&".join(f"{k}={v}" for k,v in pairs)
    now=datetime.now(timezone.utc)
    amzdate=now.strftime("%Y%m%dT%H%M%SZ")
    datestamp=now.strftime("%Y%m%d")
    payload_hash=hashlib.sha256(body).hexdigest()
    canonical_headers=(
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amzdate}\n"
    )
    signed_headers="host;x-amz-content-sha256;x-amz-date"
    canonical_request="\n".join((
        method,
        canonical_uri,
        canonical_query,
        canonical_headers,
        signed_headers,
        payload_hash,
    ))
    scope=f"{datestamp}/auto/s3/aws4_request"
    string_to_sign="\n".join((
        "AWS4-HMAC-SHA256",
        amzdate,
        scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ))

    def sign(key_bytes,message):
        return hmac.new(key_bytes,message.encode("utf-8"),hashlib.sha256).digest()

    date_key=sign(("AWS4"+cfg["secret"]).encode("utf-8"),datestamp)
    region_key=sign(date_key,"auto")
    service_key=sign(region_key,"s3")
    signing_key=sign(service_key,"aws4_request")
    signature=hmac.new(signing_key,string_to_sign.encode("utf-8"),hashlib.sha256).hexdigest()
    authorization=(
        "AWS4-HMAC-SHA256 "
        f'Credential={cfg["access"]}/{scope}, '
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    headers={
        "Authorization":authorization,
        "Host":host,
        "x-amz-content-sha256":payload_hash,
        "x-amz-date":amzdate,
    }
    if content_type:
        headers["Content-Type"]=content_type
    url="https://"+host+canonical_uri+(("?"+canonical_query) if canonical_query else "")
    try:
        response=httpx.request(method,url,content=body,headers=headers,timeout=20.0)
    except httpx.HTTPError as exc:
        raise GalleryStorageError("R2 request failed.") from exc
    if allow_missing and response.status_code==404:
        return None
    if response.status_code<200 or response.status_code>=300:
        raise GalleryStorageError(f"R2 request failed with status {response.status_code}.")
    return response


def _r2_load_index():
    response=_r2_request("GET",_R2_INDEX_KEY,allow_missing=True)
    if response is None:
        return []
    try:
        data=json.loads(response.content.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise GalleryStorageError("R2 Gallery index is invalid.") from exc
    if not isinstance(data,list):
        raise GalleryStorageError("R2 Gallery index must be a list.")
    return data


def _r2_save_index(rows):
    body=(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8")
    _r2_request("PUT",_R2_INDEX_KEY,body=body,content_type="application/json")


def _r2_find(rows,item_id):
    for item in rows:
        if item.get("id")==item_id:
            item.setdefault("visibility","public")
            return item
    return None


def _local_storage_root():
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
    cfg=_r2_config()
    if cfg:
        return {
            "backend":"r2",
            "persistent":True,
            "writable":True,
            "bucket":cfg["bucket"],
        }
    root,persistent=_local_storage_root()
    try:
        (root/"images").mkdir(parents=True,exist_ok=True)
        (root/"meta").mkdir(parents=True,exist_ok=True)
        probe=root/".write-test"
        probe.write_text("ok",encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable=True
    except OSError:
        writable=False
    return {
        "backend":"local-persistent" if persistent else "local-temporary",
        "persistent":persistent,
        "writable":writable,
    }


def _new_record(image_bytes,content_type,prompt,kind,source):
    stamp=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    digest=hashlib.sha256(image_bytes+stamp.encode("utf-8")).hexdigest()[:24]
    ext=_ALLOWED_TYPES[content_type]
    return {
        "id":digest,
        "label":gallery_label(prompt,kind),
        "kind":_normalize_kind(kind),
        "source":"telegram" if str(source).casefold()=="telegram" else "web",
        "created_at":stamp,
        "content_type":content_type,
        "file":digest+ext,
        "visibility":"public",
    }


def archive_creation(image_bytes,content_type,prompt,kind,source):
    if content_type not in _ALLOWED_TYPES:
        raise ValueError("unsupported image content type")
    if not image_bytes:
        raise ValueError("empty image")
    with _LOCK:
        record=_new_record(image_bytes,content_type,prompt,kind,source)
        if _r2_enabled():
            record["file"]="images/"+record["file"]
            rows=_r2_load_index()
            _r2_request("PUT",record["file"],body=image_bytes,content_type=content_type)
            rows.append(record)
            rows.sort(key=lambda item:item.get("created_at",""),reverse=True)
            _r2_save_index(rows)
            return dict(record)

        root,_=_local_storage_root()
        images=root/"images"; meta=root/"meta"
        images.mkdir(parents=True,exist_ok=True)
        meta.mkdir(parents=True,exist_ok=True)
        image_path=images/record["file"]
        meta_path=meta/(record["id"]+".json")
        tmp=image_path.with_suffix(image_path.suffix+".tmp")
        tmp.write_bytes(image_bytes)
        os.replace(tmp,image_path)
        tmp_meta=meta_path.with_suffix(".json.tmp")
        tmp_meta.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True),encoding="utf-8")
        os.replace(tmp_meta,meta_path)
        return dict(record)


def _local_read_meta(item_id):
    if not _ID_RE.fullmatch(str(item_id or "")):
        return None
    root,_=_local_storage_root()
    meta_path=root/"meta"/(str(item_id)+".json")
    if not meta_path.exists():
        return None
    try:
        item=json.loads(meta_path.read_text(encoding="utf-8"))
        item.setdefault("visibility","public")
        return item
    except (OSError,ValueError):
        return None


def get_gallery_item(item_id):
    if not _ID_RE.fullmatch(str(item_id or "")):
        return None
    if _r2_enabled():
        with _LOCK:
            item=_r2_find(_r2_load_index(),str(item_id))
            return dict(item) if item else None
    item=_local_read_meta(item_id)
    return dict(item) if item else None


def set_gallery_visibility(item_id,visibility):
    visibility=str(visibility or "").casefold()
    if visibility not in _ALLOWED_VISIBILITY:
        raise ValueError("invalid gallery visibility")
    if not _ID_RE.fullmatch(str(item_id or "")):
        return None
    with _LOCK:
        if _r2_enabled():
            rows=_r2_load_index()
            item=_r2_find(rows,str(item_id))
            if not item:
                return None
            item["visibility"]=visibility
            _r2_save_index(rows)
            return dict(item)

        root,_=_local_storage_root()
        meta_path=root/"meta"/(str(item_id)+".json")
        item=_local_read_meta(item_id)
        if not item:
            return None
        item["visibility"]=visibility
        tmp_meta=meta_path.with_suffix(".json.tmp")
        tmp_meta.write_text(json.dumps(item,ensure_ascii=False,sort_keys=True),encoding="utf-8")
        os.replace(tmp_meta,meta_path)
        return dict(item)


def list_gallery(limit=60,kind=None,visibility="public"):
    wanted=_normalize_kind(kind) if kind else None
    if visibility is not None and visibility not in _ALLOWED_VISIBILITY:
        raise ValueError("invalid gallery visibility")
    limit=max(1,min(int(limit or 60),120))

    if _r2_enabled():
        with _LOCK:
            rows=[dict(item) for item in _r2_load_index() if isinstance(item,dict)]
            for item in rows:
                item.setdefault("visibility","public")
    else:
        root,_=_local_storage_root()
        meta=root/"meta"
        if not meta.exists():
            return []
        rows=[]
        with _LOCK:
            for path in meta.glob("*.json"):
                try:
                    item=json.loads(path.read_text(encoding="utf-8"))
                except (OSError,ValueError):
                    continue
                item.setdefault("visibility","public")
                rows.append(item)

    filtered=[]
    for item in rows:
        if wanted and item.get("kind")!=wanted:
            continue
        if visibility is not None and item.get("visibility")!=visibility:
            continue
        filtered.append(item)
    filtered.sort(key=lambda item:item.get("created_at",""),reverse=True)
    return filtered[:limit]


def read_gallery_image(item_id,include_nonpublic=False):
    if not _ID_RE.fullmatch(str(item_id or "")):
        return None
    if _r2_enabled():
        with _LOCK:
            item=_r2_find(_r2_load_index(),str(item_id))
            if not item:
                return None
            if not include_nonpublic and item.get("visibility","public")!="public":
                return None
            response=_r2_request("GET",item["file"],allow_missing=True)
            if response is None:
                return None
            return response.content,item["content_type"]

    item=_local_read_meta(item_id)
    if not item:
        return None
    if not include_nonpublic and item.get("visibility","public")!="public":
        return None
    root,_=_local_storage_root()
    try:
        image_path=root/"images"/item["file"]
        return image_path.read_bytes(),item["content_type"]
    except (OSError,KeyError):
        return None
