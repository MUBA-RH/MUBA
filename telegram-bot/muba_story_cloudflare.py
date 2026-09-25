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
from io import BytesIO

from PIL import Image, ImageOps

MODEL=os.getenv("MUBA_STORY_CF_MODEL","@cf/black-forest-labs/flux-2-klein-9b").strip()
WIDTH=int(os.getenv("MUBA_STORY_CF_WIDTH","1024"))
HEIGHT=int(os.getenv("MUBA_STORY_CF_HEIGHT",str(WIDTH*9//16)))

def configured()->bool:
    return bool(os.getenv("CLOUDFLARE_ACCOUNT_ID") and os.getenv("CLOUDFLARE_API_TOKEN") and MODEL)

def endpoint()->str:
    account=os.environ["CLOUDFLARE_ACCOUNT_ID"]
    return f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"

class GenerationCapacityError(RuntimeError):
    """Primary generation reservoir has exhausted or throttled capacity."""

def _capacity_limited(status:int,detail:str)->bool:
    text=(detail or "").lower()
    return status==429 or "daily free allocation" in text or "quota" in text or "rate limit" in text

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
        "Create one hand-drawn 2D chibi comic scene with clean dark outlines and soft cel shading using the attached character reference. "
        "Keep the same recognizable character appearance, clothing and proportions. "
        "Show one landscape 16:9 scene only, with no captions, logos added by the model, "
        "speech bubbles, collage, split frame or watermark. "
        "Scene: "+beat
    )

def _prepare_reference(reference_bytes:bytes)->tuple[bytes,str]:
    """Normalize for FLUX.2 input limit without cropping or changing aspect ratio.
    The 511px transport copy is provider-only; canonical identity geometry remains full resolution in V6.
    """
    try:
        with Image.open(BytesIO(reference_bytes)) as source:
            image=ImageOps.exif_transpose(source).convert("RGB")
            max_side=max(image.size)
            if max_side>=512:
                scale=511/max_side  # provider requires dimensions below 512; preserve full frame/aspect ratio
                image=image.resize(
                    (max(1,round(image.width*scale)),max(1,round(image.height*scale))),
                    Image.Resampling.LANCZOS,
                )
            out=BytesIO()
            image.save(out,format="JPEG",quality=95,optimize=True)
            return out.getvalue(),"image/jpeg"
    except Exception as exc:
        raise RuntimeError("Daily Story reference image could not be prepared for Cloudflare") from exc

async def _request(session,prompt:str,reference_bytes:bytes|None=None,reference_type:str="image/jpeg",continuity_bytes:bytes|None=None,continuity_type:str="image/jpeg"):
    """Issue one FLUX request; reference is optional for filter diagnostics."""

    form=__import__("aiohttp").FormData()
    form.add_field("prompt",prompt)
    form.add_field("width",str(WIDTH))
    form.add_field("height",str(HEIGHT))
    if reference_bytes is not None:
        form.add_field("input_image_0",reference_bytes,filename="muba-reference.jpg",content_type=reference_type)
    if continuity_bytes is not None:
        form.add_field("input_image_1",continuity_bytes,filename="previous-frame.jpg",content_type=continuity_type)
    form.add_field("guidance","5.0")
    headers={"Authorization":"Bearer "+os.environ["CLOUDFLARE_API_TOKEN"]}
    async with session.post(endpoint(),data=form,headers=headers,timeout=90) as response:
        return response.status,response.headers.get("Content-Type",""),await response.read()

async def generate(session,prompt:str,reference_bytes:bytes,*,reference_type:str="image/jpeg",continuity_bytes:bytes|None=None,continuity_type:str="image/jpeg")->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("Cloudflare Living Story engine is not configured")
    if WIDTH<=0 or HEIGHT<=0 or WIDTH*9!=HEIGHT*16:
        raise RuntimeError("Daily Story output dimensions must be landscape 16:9")

    # Cloudflare FLUX.2 requires every reference input to be smaller than
    # 512x512. Telegram photos are normally much larger, so normalize once
    # before both the primary request and any provider-filter retry.
    reference_bytes,reference_type=_prepare_reference(reference_bytes)
    if continuity_bytes is not None:
        continuity_bytes,continuity_type=_prepare_reference(continuity_bytes)
        prompt=("IMAGE 0 is the immutable MUBA identity/style reference. IMAGE 1 is the immediately previous story frame. "
                "Create exactly ONE full-bleed hand-drawn 2D chibi comic scene in 16:9, with clean dark outlines and soft cel shading; no photorealism or 3D rendering. Keep MUBA fully visible from cap to bare feet with upright biped anatomy and consistent tan/brown fur; never add shoes. Do not crop to a face-only portrait. Not a collage, grid, contact sheet, comic page, montage, diptych, triptych, or multi-panel layout. "
                "Continue the physical scene from IMAGE 1 while preserving MUBA from IMAGE 0: same face geometry, eyes, muzzle, nose, mouth, fur palette, cap, clothing and body proportions. "
                "Only pose, expression, gaze and camera may change. "+prompt)
    else:
        prompt=("IMAGE 0 is the immutable MUBA identity/style reference. Create exactly ONE full-bleed hand-drawn 2D chibi comic scene in 16:9, with clean dark outlines and soft cel shading; no photorealism or 3D rendering. Keep MUBA fully visible from cap to bare feet with upright biped anatomy and consistent tan/brown fur; never add shoes. Do not crop to a face-only portrait. Not a collage, grid, contact sheet, comic page, montage, diptych, triptych, or multi-panel layout. "
                "Preserve the exact face geometry, eyes, muzzle, nose, mouth, fur palette, cap, clothing and body proportions from IMAGE 0. "+prompt)
    status,content_type,raw=await _request(session,prompt,reference_bytes,reference_type,continuity_bytes,continuity_type)
    if status!=200:
        detail=raw[:1000].decode("utf-8","replace")
        if _capacity_limited(status,detail):
            raise GenerationCapacityError("Primary generation reservoir capacity unavailable")
        if _flagged(status,detail):
            retry_prompt=_safe_retry_prompt(prompt)
            status,content_type,raw=await _request(session,retry_prompt,reference_bytes,reference_type,continuity_bytes,continuity_type)
            if status!=200:
                detail=raw[:1000].decode("utf-8","replace")
                if _flagged(status,detail):
                    # Diagnostic isolation only: a neutral text-only probe tells us
                    # whether the provider is rejecting the reference image itself.
                    # Its output is discarded and is never shown/published.
                    probe_status,_,probe_raw=await _request(
                        session,
                        "A simple friendly fictional character standing in a quiet room.",
                    )
                    if probe_status==200:
                        raise RuntimeError(
                            "Cloudflare Living Story reference rejected by provider filter "
                            "(diagnostic=text-only-ok, reference-combination-flagged)"
                        )
                    probe_detail=probe_raw[:500].decode("utf-8","replace")
                    raise RuntimeError(
                        "Cloudflare Living Story provider filter unresolved "
                        f"(diagnostic=text-only-failed:{probe_status}): {probe_detail}"
                    )
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
