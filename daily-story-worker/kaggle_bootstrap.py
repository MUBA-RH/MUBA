"""One-shot Kaggle bootstrap for the isolated MUBA Daily Story worker."""
from __future__ import annotations
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
COMFY=Path("/kaggle/working/ComfyUI")

def run(cmd,cwd=None): subprocess.check_call(cmd,cwd=cwd)

def main():
    if not COMFY.exists():
        run(["git","clone","--depth","1","https://github.com/Comfy-Org/ComfyUI.git",str(COMFY)])
    run([sys.executable,"-m","pip","install","-r",str(COMFY/"requirements.txt")])
    run([sys.executable,"-m","pip","install","-r",str(ROOT/"requirements.txt")])
    checkpoint=os.getenv("MUBA_COMFY_CHECKPOINT","sd_xl_base_1.0.safetensors")
    model=COMFY/"models"/"checkpoints"/checkpoint
    if not model.exists():
        url=os.getenv("MUBA_COMFY_CHECKPOINT_URL","https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors").strip()
        if not url: raise RuntimeError("Missing SDXL checkpoint URL")
        run(["wget","-q","--show-progress","-O",str(model),url])
    # Install reference-conditioning node and its SDXL ViT-H assets.
    nodes=COMFY/"custom_nodes"/"comfyui-ipadapter"
    if not nodes.exists():
        run(["git","clone","--depth","1","https://github.com/comfyorg/comfyui-ipadapter.git",str(nodes)])
    clip_dir=COMFY/"models"/"clip_vision"; clip_dir.mkdir(parents=True,exist_ok=True)
    ipa_dir=COMFY/"models"/"ipadapter"; ipa_dir.mkdir(parents=True,exist_ok=True)
    clip=clip_dir/"CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
    ipa=ipa_dir/"ip-adapter-plus_sdxl_vit-h.safetensors"
    if not clip.exists():
        run(["wget","-q","--show-progress","-O",str(clip),"https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors"])
    if not ipa.exists():
        run(["wget","-q","--show-progress","-O",str(ipa),"https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors"])
    print("MUBA Daily Story worker ready: SDXL + IPAdapter Plus reference-conditioning assets installed.")
    print("Start ComfyUI: python /kaggle/working/ComfyUI/main.py --listen 127.0.0.1 --port 8188 --lowvram")

if __name__=="__main__": main()
