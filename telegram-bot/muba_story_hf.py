"""Hugging Face ZeroGPU IP-Adapter bridge for MUBA Living Story.

Living Story is isolated from Studio/Gallery. The bridge targets a public
ZeroGPU Space whose Gradio API exposes a real SDXL + IP-Adapter text-to-image
function. The Space and endpoint are discovered at runtime; no Studio or
Cloudflare fallback is permitted.
"""
from __future__ import annotations

import os
from pathlib import Path

SPACE_ID=os.getenv("MUBA_STORY_HF_SPACE","tonyassi/IP-Adapter-Playground").strip()
API_CANDIDATES=("text_to_image","text_to_image_1")
IP_WEIGHT=float(os.getenv("MUBA_STORY_HF_IP_WEIGHT","0.72"))
NEGATIVE_PROMPT=(
    "photorealistic, 3d, cgi, plush toy, mascot render, close-up portrait, "
    "circular avatar, purple neon ring, crown, watermark, extra text"
)

def configured()->bool:
    return bool(os.getenv("HF_TOKEN")) and bool(SPACE_ID)

def _named_endpoints(client)->dict[str,str]:
    endpoints=client.view_api(return_format="dict",print_info=False) or {}
    named=(endpoints.get("named_endpoints") or {}) if isinstance(endpoints,dict) else {}
    return {str(name).lstrip("/"):str(name) for name in named}

def _select_endpoint(named:dict[str,str])->str:
    for candidate in API_CANDIDATES:
        if candidate in named:
            return named[candidate]
    for normalized,api_name in named.items():
        low=normalized.lower()
        if "text_to_image" in low or "text-to-image" in low:
            return api_name
    raise RuntimeError(
        "Hugging Face IP-Adapter generation endpoint unavailable; discovered: "
        + ", ".join(sorted(named)[:20])
    )

def _run_gradio(prompt:str,reference_url:str):
    from gradio_client import Client, handle_file

    token=os.getenv("HF_TOKEN","").strip() or None
    client=Client(SPACE_ID,token=token,verbose=False)
    api_name=_select_endpoint(_named_endpoints(client))
    # Upstream Space contract (verified from its current app.py):
    # reference, prompt, negative, width, height, IP scale, strength, CFG, steps.
    return client.predict(
        handle_file(reference_url),
        prompt,
        NEGATIVE_PROMPT,
        768,
        768,
        IP_WEIGHT,
        0.70,
        7.5,
        50,
        api_name=api_name,
    )

def _result_path(result)->str:
    if isinstance(result,str):
        return result
    if isinstance(result,dict):
        for key in ("path","name"):
            value=result.get(key)
            if value:
                return str(value)
    if isinstance(result,(list,tuple)) and result:
        return _result_path(result[0])
    raise RuntimeError("Unexpected Hugging Face IP-Adapter image response")

async def generate(session,prompt:str,reference_url:str)->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("HF_TOKEN is not configured for Living Story")
    import asyncio
    result=await asyncio.to_thread(_run_gradio,prompt,reference_url)
    path=_result_path(result)
    body=await asyncio.to_thread(Path(path).read_bytes)
    if not body:
        raise RuntimeError("Hugging Face IP-Adapter returned an empty image")
    suffix=Path(path).suffix.lower()
    content_type={
        ".jpg":"image/jpeg",
        ".jpeg":"image/jpeg",
        ".webp":"image/webp",
    }.get(suffix,"image/png")
    return body,content_type
