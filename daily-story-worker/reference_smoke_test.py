#!/usr/bin/env python3
from pathlib import Path
import json, shutil, subprocess, sys, time, uuid
import requests

ROOT = Path("/kaggle/working/MUBA/daily-story-worker")
COMFY = Path("/kaggle/working/ComfyUI")
OUT = Path("/kaggle/working/muba-smoke-test")
OUT.mkdir(parents=True, exist_ok=True)

pngs = sorted(ROOT.glob("*.png"))
contract = ROOT / "muba_master_reference_v1.json"
required = [
    COMFY / "models/checkpoints/sd_xl_base_1.0.safetensors",
    COMFY / "models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
    COMFY / "models/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors",
]
assert len(pngs) >= 2, "Two MUBA reference PNGs are required"
assert contract.exists(), "muba_master_reference_v1.json missing"
for p in required: assert p.exists(), f"Missing required asset: {p}"

identity = json.loads(contract.read_text(encoding="utf-8"))
# Prefer the smaller clean character reference over the annotated identity sheet.
primary = min(pngs, key=lambda p: p.stat().st_size)
input_dir = COMFY / "input"
input_dir.mkdir(parents=True, exist_ok=True)
ref_name = "MUBA_MASTER_REFERENCE.png"
shutil.copy2(primary, input_dir / ref_name)

base = "http://127.0.0.1:8188"
def alive():
    try: return requests.get(base + "/system_stats", timeout=2).ok
    except Exception: return False
if not alive():
    subprocess.Popen([sys.executable, str(COMFY/"main.py"), "--listen", "127.0.0.1", "--port", "8188", "--lowvram"],
                     stdout=open("/kaggle/working/comfyui.log","a"), stderr=subprocess.STDOUT)
    for _ in range(90):
        if alive(): break
        time.sleep(2)
    else: raise RuntimeError("ComfyUI did not start")

prompt = (
    "MUBA, one single canonical character, full body visible head to bare feet, standing upright, centered, "
    "match the reference image identity extremely closely: same asymmetric huge protruding brown eyes, same eye spacing, "
    "same tiny dark nose, same short muzzle, same pink tongue sticking out, same tan/brown dense short fur, "
    "same oversized head and compact small body proportions, same black cap with MUBA, same black hoodie with $MUBA. "
    "Do not redesign or reinterpret the character. Neutral simple daylight background. "
    + identity.get("identity_prompt","")
)
negative = (
    identity.get("negative_prompt","")
    + ", generic mascot, owl, cat, dog, sloth, round symmetrical eyes, normal sized eyes, different eye spacing, "
      "different nose, different muzzle, closed mouth, tongue missing, portrait crop, close-up, cropped feet, "
      "collage, split frame, duplicate character, extra limbs, shoes, changed face, redesigned character, watermark"
)

wf = {
 "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"sd_xl_base_1.0.safetensors"}},
 "2":{"class_type":"LoadImage","inputs":{"image":ref_name}},
 "3":{"class_type":"IPAdapterUnifiedLoader","inputs":{"model":["1",0],"preset":"PLUS (high strength)"}},
 "4":{"class_type":"IPAdapterAdvanced","inputs":{"model":["3",0],"ipadapter":["3",1],"image":["2",0],"weight":1.30,"weight_type":"linear","combine_embeds":"concat","start_at":0.0,"end_at":1.0,"embeds_scaling":"V only"}},
 "5":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["1",1]}},
 "6":{"class_type":"CLIPTextEncode","inputs":{"text":negative,"clip":["1",1]}},
 "7":{"class_type":"EmptyLatentImage","inputs":{"width":768,"height":1024,"batch_size":1}},
 "8":{"class_type":"KSampler","inputs":{"seed":260926,"steps":32,"cfg":5.0,"sampler_name":"euler","scheduler":"normal","denoise":1.0,"model":["4",0],"positive":["5",0],"negative":["6",0],"latent_image":["7",0]}},
 "9":{"class_type":"VAEDecode","inputs":{"samples":["8",0],"vae":["1",2]}},
 "10":{"class_type":"SaveImage","inputs":{"filename_prefix":"MUBA_REFERENCE_SMOKE_V2","images":["9",0]}}
}
client=str(uuid.uuid4())
r=requests.post(base+"/prompt",json={"prompt":wf,"client_id":client},timeout=30)
if not r.ok:
    raise RuntimeError("ComfyUI workflow rejected: "+r.text)
pid=r.json()["prompt_id"]
print("MUBA identity V2 generation queued:", pid)
for _ in range(300):
    h=requests.get(base+"/history/"+pid,timeout=30).json()
    if pid in h:
        imgs=[]
        for node in h[pid].get("outputs",{}).values(): imgs.extend(node.get("images",[]))
        if not imgs: raise RuntimeError("Generation finished without image: "+json.dumps(h[pid])[:1500])
        meta=imgs[-1]
        data=requests.get(base+"/view",params={"filename":meta["filename"],"subfolder":meta.get("subfolder",""),"type":meta.get("type","output")},timeout=60).content
        dest=OUT/"MUBA_REFERENCE_SMOKE_V2.png"; dest.write_bytes(data)
        print("MUBA_REFERENCE_SMOKE_V2_TEST=PASS")
        print("REFERENCE_USED:", primary.name)
        print("OUTPUT:",dest)
        break
    time.sleep(2)
else: raise TimeoutError("MUBA reference V2 generation timed out")
