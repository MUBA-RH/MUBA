"""Open-source Qwen Daily Story HTTP bridge."""
from __future__ import annotations
import os, base64, aiohttp
ENDPOINT=os.getenv("MUBA_STORY_QWEN_URL","").rstrip("/")
TOKEN=os.getenv("MUBA_STORY_QWEN_TOKEN","")
def configured(): return bool(ENDPOINT)
async def generate(session,prompt,reference_bytes,reference_type="image/png",continuity_bytes=None,continuity_type="image/png"):
    form=aiohttp.FormData()
    form.add_field("prompt",prompt); form.add_field("response_format","b64_json")
    form.add_field("images",reference_bytes,filename="muba-reference.png",content_type=reference_type)
    if continuity_bytes: form.add_field("images",continuity_bytes,filename="previous-frame.png",content_type=continuity_type)
    headers={"Authorization":"Bearer "+TOKEN} if TOKEN else {}
    async with session.post(ENDPOINT+"/v1/image/edit",data=form,headers=headers,timeout=600) as resp:
        raw=await resp.json(content_type=None)
        if resp.status!=200: raise RuntimeError(f"Qwen Daily Story request failed ({resp.status}): {str(raw)[:1000]}")
        payload=(raw.get("data") or [{}])[0]; encoded=payload.get("b64_json") or raw.get("b64_json")
        if not encoded: raise RuntimeError("Qwen Daily Story response has no b64_json")
        return base64.b64decode(encoded),"image/png"
