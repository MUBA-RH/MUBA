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

def _headers()->dict:
    token=os.getenv("HF_TOKEN","").strip()
    return {"Authorization":f"Bearer {token}"} if token else {}

async def _gradio_call(session,api_name:str,json_params:str,timeout_seconds:int=180):
    # RioShiina/ImageGen runs Gradio 6. Gradio's current agent API uses the
    # named-parameter v2 endpoint; the legacy positional {"data":[...]} call
    # returns HTTP 500 before ImageGen is invoked.
    call_url=f"{SPACE_BASE}/gradio_api/call/v2/{api_name}"
    async with session.post(call_url,json={"json_params":json_params},headers=_headers(),timeout=30) as response:
        raw=await response.text()
        if response.status not in (200,201):
            raise RuntimeError(f"Hugging Face Space call failed ({response.status})")
        try:
            event_id=json.loads(raw)["event_id"]
        except Exception as exc:
            raise RuntimeError("Hugging Face Space did not return an event id") from exc

    result_url=f"{SPACE_BASE}/gradio_api/call/{api_name}/{event_id}"
    async with session.get(result_url,headers=_headers(),timeout=timeout_seconds) as response:
        if response.status!=200:
            raise RuntimeError(f"Hugging Face Space result failed ({response.status})")
        payload=None
        async for raw_line in response.content:
            line=raw_line.decode("utf-8","replace").strip()
            if not line.startswith("data:"):
                continue
            value=line[5:].strip()
            if not value:
                continue
            try:
                decoded=json.loads(value)
            except json.JSONDecodeError:
                continue
            payload=decoded
        if payload is None:
            raise RuntimeError("Hugging Face Space returned no result")
        if isinstance(payload,list) and len(payload)==1:
            payload=payload[0]
        return payload

async def generate(session,prompt:str,reference_url:str)->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("HF_TOKEN is not configured")
    params=build_params(prompt,reference_url)
    result=await _gradio_call(session,API_NAME,json.dumps(params,separators=(",",":")))
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
