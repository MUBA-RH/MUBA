"""OpenAI Images API bridge for MUBA Daily Story."""
from __future__ import annotations
import base64, os
from io import BytesIO
from PIL import Image, ImageOps

MODEL=os.getenv("MUBA_STORY_OPENAI_MODEL","gpt-image-2.5-sunburst").strip()
SIZE=os.getenv("MUBA_STORY_OPENAI_SIZE","1536x1024").strip()
QUALITY=os.getenv("MUBA_STORY_OPENAI_QUALITY","medium").strip()

def configured()->bool:
    return bool(os.getenv("OPENAI_API_KEY") and MODEL)

def endpoint()->str:
    return "https://api.openai.com/v1/images/edits"

def _png(raw:bytes)->bytes:
    with Image.open(BytesIO(raw)) as source:
        image=ImageOps.exif_transpose(source).convert("RGBA")
        out=BytesIO(); image.save(out,format="PNG"); return out.getvalue()

async def generate(session,prompt:str,reference_bytes:bytes,*,reference_type:str="image/jpeg",continuity_bytes:bytes|None=None,continuity_type:str="image/jpeg")->tuple[bytes,str]:
    if not configured():
        raise RuntimeError("OpenAI Daily Story image engine is not configured")
    identity=_png(reference_bytes)
    form=__import__("aiohttp").FormData()
    form.add_field("model",MODEL)
    form.add_field("prompt",(
        "IMAGE 1 is the immutable MUBA identity reference. Preserve the same face geometry, eyes, nose, muzzle, mouth, fur palette, cap, clothing and body proportions. "
        "Create exactly ONE single full-frame landscape image. Never create a collage, grid, comic page, split frame, contact sheet, montage, diptych, triptych or multiple versions of MUBA. "
        + ("IMAGE 2 is the immediately previous Daily Story frame. Continue its location, props, lighting and physical story state while keeping MUBA from IMAGE 1. " if continuity_bytes else "")
        + prompt
    ))
    form.add_field("size",SIZE)
    form.add_field("quality",QUALITY)
    form.add_field("input_fidelity","high")
    form.add_field("output_format","png")
    form.add_field("image[]",identity,filename="muba-reference.png",content_type="image/png")
    if continuity_bytes:
        form.add_field("image[]",_png(continuity_bytes),filename="previous-frame.png",content_type="image/png")
    headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]}
    async with session.post(endpoint(),data=form,headers=headers,timeout=180) as response:
        raw=await response.read()
        if response.status!=200:
            raise RuntimeError(f"OpenAI Daily Story request failed ({response.status}): {raw[:1000].decode('utf-8','replace')}")
    try:
        payload=__import__("json").loads(raw.decode("utf-8"))
        image=base64.b64decode(payload["data"][0]["b64_json"])
    except Exception as exc:
        raise RuntimeError("OpenAI Daily Story returned an unreadable image response") from exc
    return image,"image/png"
