"""Robust Hugging Face ZeroGPU bridge for MUBA Living Story.

The bridge is intentionally isolated from Studio. It uses the public FLUX
IP-Adapter Space, retries transient ZeroGPU failures, accepts current
gradio_client file result shapes and can condition from URL or local files.
"""
from __future__ import annotations

import asyncio
import os
import random
from pathlib import Path

SPACE_ID=os.getenv("MUBA_STORY_HF_SPACE","InstantX/flux-IP-adapter").strip()
API_CANDIDATES=("process_image","predict")
PANEL_IP_WEIGHT=float(os.getenv("MUBA_STORY_HF_IP_WEIGHT","0.78"))
ANCHOR_IP_WEIGHT=float(os.getenv("MUBA_STORY_HF_ANCHOR_WEIGHT","0.82"))
MAX_ATTEMPTS=max(1,int(os.getenv("MUBA_STORY_HF_ATTEMPTS","3")))

def configured()->bool:
    # The public Space does not require a token. A token is used when configured
    # but is not a hard runtime prerequisite.
    return bool(SPACE_ID)

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
    raise RuntimeError("Hugging Face FLUX IP-Adapter generation endpoint unavailable; discovered: "+", ".join(sorted(named)[:20]))

def _run_gradio(prompt:str,reference:str,weight:float,seed:int):
    from gradio_client import Client, handle_file
    token=os.getenv("HF_TOKEN","").strip() or None
    client=Client(SPACE_ID,token=token,verbose=False)
    api_name=_select_endpoint(_named_endpoints(client))
    return client.predict(
        handle_file(reference),prompt,weight,seed,False,1024,1024,
        api_name=api_name,
    )

def _result_path(result)->str:
    image=result[0] if isinstance(result,(list,tuple)) and result else result
    if isinstance(image,str):
        return image
    if isinstance(image,dict):
        for key in ("path","name"):
            value=image.get(key)
            if value:
                return str(value)
    for key in ("path","name"):
        value=getattr(image,key,None)
        if value:
            return str(value)
    raise RuntimeError("Unexpected Hugging Face FLUX IP-Adapter image response")

async def generate(session,prompt:str,reference:str,*,weight:float|None=None,seed:int=42)->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("Living Story HF Space is not configured")
    last_error=None
    for attempt in range(MAX_ATTEMPTS):
        try:
            result=await asyncio.wait_for(
                asyncio.to_thread(_run_gradio,prompt,reference,PANEL_IP_WEIGHT if weight is None else weight,seed),
                timeout=240,
            )
            path=_result_path(result)
            body=await asyncio.to_thread(Path(path).read_bytes)
            if not body:
                raise RuntimeError("Hugging Face FLUX IP-Adapter returned an empty image")
            suffix=Path(path).suffix.lower()
            content_type={".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"}.get(suffix,"image/png")
            return body,content_type
        except Exception as exc:
            last_error=exc
            if attempt+1>=MAX_ATTEMPTS:
                break
            await asyncio.sleep(4*(attempt+1)+random.random())
    raise RuntimeError(f"Living Story generation failed after {MAX_ATTEMPTS} attempts") from last_error

async def generate_anchor(session,prompt:str,reference:str)->tuple[bytes,str]:
    return await generate(session,prompt,reference,weight=ANCHOR_IP_WEIGHT,seed=20260922)
