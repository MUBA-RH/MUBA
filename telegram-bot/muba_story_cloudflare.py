"""Cloudflare Workers AI bridge for MUBA Living Story.

Living Story is isolated from Studio UI but reuses the already-configured
Cloudflare Workers AI account. One daily post consists of four image calls.
Every panel is conditioned directly on the canonical MUBA reference image so
there is no extra identity-anchor generation call.
"""
from __future__ import annotations

import base64
import json
import os

MODEL=os.getenv("MUBA_STORY_CF_MODEL","@cf/black-forest-labs/flux-2-klein-4b").strip()
WIDTH=int(os.getenv("MUBA_STORY_CF_WIDTH","1024"))
HEIGHT=int(os.getenv("MUBA_STORY_CF_HEIGHT",str(WIDTH*9//16)))

def configured()->bool:
    return bool(os.getenv("CLOUDFLARE_ACCOUNT_ID") and os.getenv("CLOUDFLARE_API_TOKEN") and MODEL)

def endpoint()->str:
    account=os.environ["CLOUDFLARE_ACCOUNT_ID"]
    return f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"

async def generate(session,prompt:str,reference_bytes:bytes,*,reference_type:str="image/jpeg")->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("Cloudflare Living Story engine is not configured")
    if WIDTH<=0 or HEIGHT<=0 or WIDTH*9!=HEIGHT*16:
        raise RuntimeError("Daily Story output dimensions must be landscape 16:9")
    form=__import__("aiohttp").FormData()
    form.add_field("prompt",prompt)
    form.add_field("width",str(WIDTH))
    form.add_field("height",str(HEIGHT))
    form.add_field("input_image_0",reference_bytes,filename="muba-reference.jpg",content_type=reference_type)
    headers={"Authorization":"Bearer "+os.environ["CLOUDFLARE_API_TOKEN"]}
    async with session.post(endpoint(),data=form,headers=headers,timeout=90) as response:
        raw=await response.read()
        if response.status!=200:
            detail=raw[:500].decode("utf-8","replace")
            raise RuntimeError(f"Cloudflare Living Story request failed ({response.status}): {detail}")
        content_type=response.headers.get("Content-Type","")
        if content_type.startswith("image/"):
            if not raw: raise RuntimeError("Cloudflare Living Story returned an empty image")
            return raw,content_type.split(";",1)[0]
        payload=json.loads(raw.decode("utf-8"))
        result=payload.get("result",payload)
        encoded=result.get("image") if isinstance(result,dict) else None
        if not encoded: raise RuntimeError("Cloudflare Living Story response contained no image")
        body=base64.b64decode(encoded)
        if not body: raise RuntimeError("Cloudflare Living Story returned an empty image")
        return body,"image/png"
