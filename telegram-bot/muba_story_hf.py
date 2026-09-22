"""Hugging Face ZeroGPU IP-Adapter bridge for MUBA Living Story.

This module is deliberately isolated from Studio/Gallery. It calls the public
RioShiina ImageGen high-level Gradio API, using SDXL + IP-Adapter PLUS so the
canonical MUBA image is an identity reference rather than an img2img canvas.
"""
from __future__ import annotations
import json
import os
from urllib.parse import urljoin

SPACE_BASE=os.getenv("MUBA_STORY_HF_SPACE","https://rioshiina-imagegen.hf.space").rstrip("/")
MODEL=os.getenv("MUBA_STORY_HF_MODEL","stabilityai/SDXL-Base-1.0")
API_NAME="run_imagegen"
API_CANDIDATES=("run_imagegen","ImageGen_run_imagegen")
IP_PRESET=os.getenv("MUBA_STORY_HF_IP_PRESET","PLUS (high strength)")
IP_WEIGHT=float(os.getenv("MUBA_STORY_HF_IP_WEIGHT","0.72"))
FINAL_WEIGHT=float(os.getenv("MUBA_STORY_HF_FINAL_WEIGHT","0.78"))

def configured()->bool:
    return bool(os.getenv("HF_TOKEN"))

def build_params(prompt:str,reference_url:str)->dict:
    return {
        "task_type":"txt2img",
        "model":MODEL,
        "prompt":prompt,
        "negative_prompt":"photorealistic, 3d, cgi, plush toy, mascot render, close-up portrait, circular avatar, purple neon ring, crown, watermark, extra text",
        "width":1024,
        "height":1024,
        "batch_size":1,
        "chain":[{
            "injector_type":"ipadapter",
            "image":reference_url,
            "weight":IP_WEIGHT,
            "preset":IP_PRESET,
            "embeds_scaling":"V only",
            "combine_method":"concat",
            "final_weight":FINAL_WEIGHT,
        }],
    }

def _run_gradio(json_params:str):
    # Discover the endpoint exported by the currently deployed Space instead of
    # hard-coding a Gradio api_name. Gradio 6 derives names from the registered
    # function and the upstream Space can expose either short or qualified form.
    from gradio_client import Client
    token=os.getenv("HF_TOKEN","").strip() or None
    client=Client("RioShiina/ImageGen",token=token,verbose=False)
    endpoints=client.view_api(return_format="dict",print_info=False) or {}
    named=(endpoints.get("named_endpoints") or {}) if isinstance(endpoints,dict) else {}
    normalized={str(name).lstrip("/"):str(name) for name in named}
    for candidate in API_CANDIDATES:
        if candidate in normalized:
            return client.predict(json_params=json_params,api_name=normalized[candidate])
    # Upstream may rename the registered wrapper while retaining its semantic name.
    for normalized_name,api_name in normalized.items():
        if normalized_name.lower().endswith("run_imagegen"):
            return client.predict(json_params=json_params,api_name=api_name)
    raise RuntimeError(
        "Hugging Face ImageGen endpoint unavailable; discovered: "
        + ", ".join(sorted(normalized)[:20])
    )

def _headers()->dict:
    token=os.getenv("HF_TOKEN","").strip()
    return {"Authorization":f"Bearer {token}"} if token else {}

async def generate(session,prompt:str,reference_url:str)->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("HF_TOKEN is not configured")
    params=build_params(prompt,reference_url)
    import asyncio
    result=await asyncio.to_thread(_run_gradio,json.dumps(params,separators=(",",":")))
    if not isinstance(result,dict):
        raise RuntimeError("Unexpected Hugging Face image response")
    if result.get("status")!="completed":
        message=((result.get("error") or {}).get("message") if isinstance(result.get("error"),dict) else None) or "generation failed"
        raise RuntimeError(f"Hugging Face image generation failed: {message}")
    images=((result.get("result") or {}).get("images") or [])
    if not images:
        raise RuntimeError("Hugging Face generation returned no image URL")
    image_url=str(images[0])
    if image_url.startswith("/"):
        image_url=urljoin(SPACE_BASE+"/",image_url.lstrip("/"))
    async with session.get(image_url,headers=_headers(),timeout=60) as response:
        body=await response.read()
        if response.status!=200 or not body:
            raise RuntimeError("Could not download Hugging Face generated image")
        content_type=response.headers.get("Content-Type","image/png").split(";",1)[0]
        if not content_type.startswith("image/"):
            content_type="image/png"
        return body,content_type
