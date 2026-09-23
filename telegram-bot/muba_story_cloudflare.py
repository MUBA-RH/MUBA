"""Cloudflare Workers AI bridge for MUBA Daily Story.

Each Daily Story frame is conditioned on the fresh DEV reference image.
A provider-side content-filter rejection gets one conservative retry with a
sanitized visual prompt; other HTTP failures still fail closed immediately.
"""
from __future__ import annotations

import base64
import json
import os
import re

MODEL=os.getenv("MUBA_STORY_CF_MODEL","@cf/black-forest-labs/flux-2-klein-4b").strip()
WIDTH=int(os.getenv("MUBA_STORY_CF_WIDTH","1024"))
HEIGHT=int(os.getenv("MUBA_STORY_CF_HEIGHT",str(WIDTH*9//16)))

def configured()->bool:
    return bool(os.getenv("CLOUDFLARE_ACCOUNT_ID") and os.getenv("CLOUDFLARE_API_TOKEN") and MODEL)

def endpoint()->str:
    account=os.environ["CLOUDFLARE_ACCOUNT_ID"]
    return f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"

def _flagged(status:int,detail:str)->bool:
    text=(detail or "").lower()
    return status==400 and ("flagged" in text or "prompt input image combination" in text)

def _safe_retry_prompt(prompt:str)->str:
    """Keep story intent while removing instruction-heavy wording on filter retry."""
    text=re.sub(r"\s+"," ",str(prompt or "")).strip()
    # The retry deliberately avoids meta/directive language and sends a short,
    # ordinary image-edit description while the same DEV reference stays attached.
    beat=text.split("CURRENT BEAT:",1)[-1].strip() if "CURRENT BEAT:" in text else text
    beat=beat[:700]
    return (
        "Create a friendly fictional illustrated scene using the attached character reference. "
        "Keep the same recognizable character appearance, clothing and proportions. "
        "Show one landscape 16:9 scene only, with no captions, logos added by the model, "
        "speech bubbles, collage, split frame or watermark. "
        "Scene: "+beat
    )

async def _request(session,prompt:str,reference_bytes:bytes,reference_type:str):
    form=__import__("aiohttp").FormData()
    form.add_field("prompt",prompt)
    form.add_field("width",str(WIDTH))
    form.add_field("height",str(HEIGHT))
    form.add_field("input_image_0",reference_bytes,filename="muba-reference.jpg",content_type=reference_type)
    headers={"Authorization":"Bearer "+os.environ["CLOUDFLARE_API_TOKEN"]}
    async with session.post(endpoint(),data=form,headers=headers,timeout=90) as response:
        return response.status,response.headers.get("Content-Type",""),await response.read()

async def generate(session,prompt:str,reference_bytes:bytes,*,reference_type:str="image/jpeg")->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("Cloudflare Living Story engine is not configured")
    if WIDTH<=0 or HEIGHT<=0 or WIDTH*9!=HEIGHT*16:
        raise RuntimeError("Daily Story output dimensions must be landscape 16:9")

    status,content_type,raw=await _request(session,prompt,reference_bytes,reference_type)
    if status!=200:
        detail=raw[:1000].decode("utf-8","replace")
        if _flagged(status,detail):
            retry_prompt=_safe_retry_prompt(prompt)
            status,content_type,raw=await _request(session,retry_prompt,reference_bytes,reference_type)
            if status!=200:
                detail=raw[:1000].decode("utf-8","replace")
                raise RuntimeError(f"Cloudflare Living Story request failed after safe retry ({status}): {detail}")
        else:
            raise RuntimeError(f"Cloudflare Living Story request failed ({status}): {detail}")

    if content_type.startswith("image/"):
        if not raw:
            raise RuntimeError("Cloudflare Living Story returned an empty image")
        return raw,content_type.split(";",1)[0]
    payload=json.loads(raw.decode("utf-8"))
    result=payload.get("result",payload)
    encoded=result.get("image") if isinstance(result,dict) else None
    if not encoded:
        raise RuntimeError("Cloudflare Living Story response contained no image")
    body=base64.b64decode(encoded)
    if not body:
        raise RuntimeError("Cloudflare Living Story returned an empty image")
    return body,"image/png"
