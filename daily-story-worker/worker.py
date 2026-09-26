from __future__ import annotations
import json, os, shutil, time, uuid
from pathlib import Path
import requests
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/"config.json").read_text())
IDENTITY=json.loads((ROOT/"muba_master_reference_v1.json").read_text(encoding="utf-8"))
COMFY=os.getenv("MUBA_COMFY_URL","http://127.0.0.1:8188").rstrip("/")
COMFY_INPUT=Path(os.getenv("MUBA_COMFY_INPUT","/kaggle/working/ComfyUI/input"))
CHECKPOINT=os.getenv("MUBA_COMFY_CHECKPOINT",CFG["model"]["default_checkpoint"])

def load_job(path):
    job=json.loads(Path(path).read_text(encoding="utf-8"))
    chapters=job.get("chapters") or []
    if len(chapters)!=1: raise ValueError("Daily Story job requires exactly one scene")
    ref=Path(job["reference_path"])
    if not ref.exists(): raise FileNotFoundError(ref)
    return job,ref

def identity_prompt(prompt):
    return ("A single bright, airy 16:9 illustrated story scene. Thick clean outlines, soft cel shading, "
            "large head and small body, expressive face, one coherent setting. "
            + prompt + " " + IDENTITY["identity_prompt"] + " IDENTITY LOCK: " + " ".join(IDENTITY["rules"]))

def workflow(prompt,seed,ref_name):
    negative=IDENTITY["negative_prompt"]+", generic mascot, owl, cat, dog, sloth, symmetrical normal eyes, changed face, redesigned character, duplicate character, collage, split frame, character sheet, infographic, labels, subtitles, photorealism"
    return {
      "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":CHECKPOINT}},
      "2":{"class_type":"LoadImage","inputs":{"image":ref_name}},
      "3":{"class_type":"IPAdapterUnifiedLoader","inputs":{"model":["1",0],"preset":"PLUS (high strength)"}},
      "4":{"class_type":"IPAdapterAdvanced","inputs":{"model":["3",0],"ipadapter":["3",1],"image":["2",0],"weight":1.30,"weight_type":"linear","combine_embeds":"concat","start_at":0.0,"end_at":1.0,"embeds_scaling":"V only"}},
      "5":{"class_type":"CLIPTextEncode","inputs":{"text":identity_prompt(prompt),"clip":["1",1]}},
      "6":{"class_type":"CLIPTextEncode","inputs":{"text":negative,"clip":["1",1]}},
      "7":{"class_type":"LoadImage","inputs":{"image":"MUBA_DAILY_STORY_INIT.png"}},
      "11":{"class_type":"VAEEncode","inputs":{"pixels":["7",0],"vae":["1",2]}},
      "8":{"class_type":"KSampler","inputs":{"seed":int(seed),"steps":32,"cfg":5.0,"sampler_name":"euler","scheduler":"normal","denoise":0.58,"model":["4",0],"positive":["5",0],"negative":["6",0],"latent_image":["11",0]}},
      "9":{"class_type":"VAEDecode","inputs":{"samples":["8",0],"vae":["1",2]}},
      "10":{"class_type":"SaveImage","inputs":{"filename_prefix":"MUBA_DAILY_STORY","images":["9",0]}}
    }

def queue(wf):
    r=requests.post(COMFY+"/prompt",json={"prompt":wf,"client_id":str(uuid.uuid4())},timeout=30)
    if not r.ok: raise RuntimeError("ComfyUI rejected workflow: "+r.text)
    return r.json()["prompt_id"]

def wait(pid,timeout=900):
    end=time.time()+timeout
    while time.time()<end:
        r=requests.get(COMFY+"/history/"+pid,timeout=30); r.raise_for_status()
        data=r.json()
        if pid in data:
            imgs=[]
            for node in data[pid].get("outputs",{}).values(): imgs.extend(node.get("images",[]))
            if imgs:return imgs[-1]
            raise RuntimeError("Generation completed without image")
        print(".",end="",flush=True); time.sleep(2)
    raise TimeoutError(pid)

def fetch(meta,dest):
    r=requests.get(COMFY+"/view",params={"filename":meta["filename"],"subfolder":meta.get("subfolder",""),"type":meta.get("type","output")},timeout=60);r.raise_for_status()
    Path(dest).write_bytes(r.content)
    with Image.open(dest) as im:
        if im.size!=(1024,576): raise ValueError(f"Invalid output size: {im.size}")

def run(job_path,out_dir):
    job,ref=load_job(job_path); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    with Image.open(ref) as im: im.verify()
    COMFY_INPUT.mkdir(parents=True,exist_ok=True)
    ref_name="MUBA_DAILY_STORY_MASTER_REFERENCE.png"
    with Image.open(ref) as source:
        master=ROOT/"muba_daily_story_master_reference.png"
        # Feed the character crop to the adapter; use the approved landscape
        # image only for composition and color, without locking its location.
        if master.is_file():
            with Image.open(master) as sheet:
                character=sheet.crop((310,0,1105,825)).copy()
        else:
            character=source.copy()
        character.convert("RGB").save(COMFY_INPUT/ref_name)
        # Use a scene-sized edit input. A portrait pasted onto a flat canvas
        # creates the very side borders rejected by the Telegram preview gate.
        ImageOps.fit(source.convert("RGB"),(1024,576),method=Image.Resampling.LANCZOS).save(COMFY_INPUT/"MUBA_DAILY_STORY_INIT.png")
    results=[]
    base_seed=int(job.get("seed",260925))
    for i,ch in enumerate(job["chapters"],1):
        prompt=ch["prompt"]+" TODAY'S STORY ONLY. One scene, one canonical MUBA. Preserve the face, eyes, muzzle, tongue, fur, cap and hoodie from the master reference; do not repeat yesterday's picture."
        print("\nMUBA_DAILY_STORY_SCENE=QUEUED",flush=True)
        meta=wait(queue(workflow(prompt,base_seed+i,ref_name)))
        dest=out/"scene.png"; fetch(meta,dest); results.append(str(dest))
        print("\nMUBA_DAILY_STORY_SCENE=PASS",flush=True)
    result={"schema_version":2,"job_id":job["job_id"],"day":job["day"],"status":"awaiting_visual_review","approval":"telegram-dev","images":results}
    (out/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("\nMUBA_DAILY_STORY_SINGLE_SCENE_TECHNICAL_TEST=PASS",flush=True)
    print("NEXT_GATE=VISUAL_REVIEW_THEN_TELEGRAM_DEV_APPROVAL",flush=True)
    return result

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("job");ap.add_argument("--out",default="output");a=ap.parse_args()
    print(json.dumps(run(a.job,a.out),indent=2))
