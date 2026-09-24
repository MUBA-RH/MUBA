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
        url=os.getenv("MUBA_COMFY_CHECKPOINT_URL","").strip()
        if not url: raise RuntimeError("Set MUBA_COMFY_CHECKPOINT_URL once to the chosen SDXL-compatible checkpoint.")
        run(["wget","-q","--show-progress","-O",str(model),url])
    print("MUBA Daily Story worker ready. Start ComfyUI with: python /kaggle/working/ComfyUI/main.py --listen 127.0.0.1 --port 8188 --lowvram")

if __name__=="__main__": main()
