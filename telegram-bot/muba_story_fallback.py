"""Secondary image-generation reservoir for MUBA.

Primary generation remains unchanged. This layer is used only after a capacity
failure from the primary engine. Provider names never leak into public UI.
"""
from __future__ import annotations
import os
from urllib.parse import quote

ENDPOINT=os.getenv("MUBA_FALLBACK_IMAGE_ENDPOINT","https://gen.pollinations.ai/image/").rstrip("/")+"/"
MODEL=os.getenv("MUBA_FALLBACK_IMAGE_MODEL","flux").strip() or "flux"

def configured()->bool:
    # The secondary reservoir can run anonymously; an optional key may raise
    # service priority/quota without being required by MUBA.
    return bool(ENDPOINT and MODEL)

async def generate(session,prompt:str,reference_bytes:bytes|None=None,*,reference_type:str="image/jpeg",width:int=1024,height:int=576)->tuple[bytes,str]:
    if width<=0 or height<=0 or width*9!=height*16:
        raise RuntimeError("Fallback output dimensions must be landscape 16:9")
    # This reservoir is text-to-image. Master identity geometry is already
    # serialized into the prompt by the caller; no secret/provider detail is
    # exposed to users.
    url=ENDPOINT+quote(prompt,safe="")
    params={"model":MODEL,"width":str(width),"height":str(height),"nologo":"true","safe":"true"}
    headers={}
    key=os.getenv("MUBA_FALLBACK_IMAGE_KEY","").strip()
    if key:
        headers["Authorization"]="Bearer "+key
    async with session.get(url,params=params,headers=headers,timeout=120) as response:
        raw=await response.read()
        if response.status!=200:
            raise RuntimeError("Secondary generation reservoir unavailable")
        ctype=(response.headers.get("Content-Type") or "image/jpeg").split(";",1)[0]
        if not ctype.startswith("image/"):
            raise RuntimeError("Secondary generation reservoir returned non-image output")
        return raw,ctype
