"""One-shot Kaggle bootstrap for the isolated MUBA Daily Story worker."""
from __future__ import annotations
import os, subprocess, sys, shutil, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMFY = Path("/kaggle/working/ComfyUI")

def run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)

def download(url: str, dest: Path):
    """Restartable download: resume partial files instead of starting over."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = Path(str(dest) + ".part")
    run(["curl", "-L", "--fail", "--retry", "8", "--retry-delay", "3",
         "--connect-timeout", "30", "--speed-time", "60", "--speed-limit", "1024",
         "-C", "-", "-o", str(part), url])
    part.replace(dest)

def install_ipadapter_node():
    """Avoid a slow/stalled git clone on Kaggle by downloading the repo archive."""
    nodes = COMFY / "custom_nodes" / "comfyui-ipadapter"
    if nodes.exists():
        return
    custom = COMFY / "custom_nodes"
    custom.mkdir(parents=True, exist_ok=True)
    archive = Path("/kaggle/working/comfyui-ipadapter-main.zip")
    download("https://github.com/comfyorg/comfyui-ipadapter/archive/refs/heads/main.zip", archive)
    tmp = Path("/kaggle/working/ipadapter_extract")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(tmp)
    extracted = tmp / "comfyui-ipadapter-main"
    if not extracted.exists():
        raise RuntimeError("IPAdapter archive layout not recognized")
    shutil.move(str(extracted), str(nodes))
    shutil.rmtree(tmp, ignore_errors=True)
    archive.unlink(missing_ok=True)
    requirements = nodes / "requirements.txt"
    if requirements.exists():
        run([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

def main():
    if not COMFY.exists():
        run(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(COMFY)])
    run([sys.executable, "-m", "pip", "install", "-r", str(COMFY / "requirements.txt")])
    run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])

    checkpoint = os.getenv("MUBA_COMFY_CHECKPOINT", "sd_xl_base_1.0.safetensors")
    model = COMFY / "models" / "checkpoints" / checkpoint
    if not model.exists():
        url = os.getenv("MUBA_COMFY_CHECKPOINT_URL", "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors").strip()
        if not url:
            raise RuntimeError("Missing SDXL checkpoint URL")
        download(url, model)

    install_ipadapter_node()

    clip = COMFY / "models" / "clip_vision" / "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
    ipa = COMFY / "models" / "ipadapter" / "ip-adapter-plus_sdxl_vit-h.safetensors"
    if not clip.exists():
        download("https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors", clip)
    if not ipa.exists():
        download("https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors", ipa)

    print("MUBA Daily Story worker ready: SDXL + IPAdapter Plus reference-conditioning assets installed.")
    print("Start ComfyUI: python /kaggle/working/ComfyUI/main.py --listen 127.0.0.1 --port 8188 --lowvram")

if __name__ == "__main__":
    main()
