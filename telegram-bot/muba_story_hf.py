"""Hugging Face ZeroGPU IP-Adapter bridge for MUBA Living Story.

Living Story is isolated from Studio/Gallery. It calls InstantX's public
FLUX IP-Adapter ZeroGPU Space, whose current app exposes a GPU-backed
process_image(image, prompt, scale, seed, randomize_seed, width, height)
generation function. No Studio or Cloudflare fallback is permitted.
"""
from __future__ import annotations

import os
from pathlib import Path

SPACE_ID=os.getenv("MUBA_STORY_HF_SPACE","InstantX/flux-IP-adapter").strip()
API_CANDIDATES=("process_image","predict")
IP_WEIGHT=float(os.getenv("MUBA_STORY_HF_IP_WEIGHT","0.70"))

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
        if "process_image" in normalized.lower():
            return api_name
    raise RuntimeError(
        "Hugging Face FLUX IP-Adapter generation endpoint unavailable; discovered: "
        + ", ".join(sorted(named)[:20])
    )

def _run_gradio(prompt:str,reference_url:str):
    from gradio_client import Client, handle_file

    token=os.getenv("HF_TOKEN","").strip() or None
    client=Client(SPACE_ID,token=token,verbose=False)
    api_name=_select_endpoint(_named_endpoints(client))
    # Verified upstream contract:
    # image, prompt, IP scale, seed, randomize seed, width, height.
    return client.predict(
        handle_file(reference_url),
        prompt,
        IP_WEIGHT,
        42,
        True,
        1024,
        1024,
        api_name=api_name,
    )

def _result_path(result)->str:
    # process_image returns (generated_image, seed).
    image=result[0] if isinstance(result,(list,tuple)) and result else result
    if isinstance(image,str):
        return image
    if isinstance(image,dict):
        for key in ("path","name"):
            value=image.get(key)
            if value:
                return str(value)
    raise RuntimeError("Unexpected Hugging Face FLUX IP-Adapter image response")

async def generate(session,prompt:str,reference_url:str)->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("HF_TOKEN is not configured for Living Story")
    import asyncio
    result=await asyncio.to_thread(_run_gradio,prompt,reference_url)
    path=_result_path(result)
    body=await asyncio.to_thread(Path(path).read_bytes)
    if not body:
        raise RuntimeError("Hugging Face FLUX IP-Adapter returned an empty image")
    suffix=Path(path).suffix.lower()
    content_type={
        ".jpg":"image/jpeg",
        ".jpeg":"image/jpeg",
        ".webp":"image/webp",
    }.get(suffix,"image/png")
    return body,content_type
