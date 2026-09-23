"""Hugging Face ZeroGPU client for MUBA Daily Story."""
from __future__ import annotations
import asyncio, os, tempfile
from pathlib import Path
SPACE=os.getenv("MUBA_STORY_HF_SPACE","").strip()
TOKEN=os.getenv("HF_TOKEN","").strip()
API_NAME=os.getenv("MUBA_STORY_HF_API_NAME","/edit").strip()
def configured(): return bool(SPACE and TOKEN)
def _predict(prompt,reference_bytes,continuity_bytes):
    from gradio_client import Client, handle_file
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); ref=root/"reference.png"; ref.write_bytes(reference_bytes)
        args={"prompt":prompt,"reference":handle_file(str(ref))}
        if continuity_bytes:
            prev=root/"previous.png"; prev.write_bytes(continuity_bytes); args["previous"]=handle_file(str(prev))
        result=Client(SPACE,token=TOKEN,verbose=False).predict(api_name=API_NAME,**args)
        path=result[0] if isinstance(result,(list,tuple)) else result
        if isinstance(path,dict): path=path.get("path") or path.get("name")
        if not path: raise RuntimeError("ZeroGPU Space returned no image")
        return Path(path).read_bytes(),"image/png"
async def generate(session,prompt,reference_bytes,reference_type="image/png",continuity_bytes=None,continuity_type="image/png"):
    del session,reference_type,continuity_type
    return await asyncio.to_thread(_predict,prompt,reference_bytes,continuity_bytes)
