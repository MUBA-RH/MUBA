"""On-demand Kaggle T4 x2 batch bridge for MUBA Daily Story."""
from __future__ import annotations
import asyncio, base64, json, os, subprocess, sys, tempfile, time
from pathlib import Path
OWNER=os.getenv("MUBA_KAGGLE_OWNER","mubarh").strip()
KERNEL=os.getenv("MUBA_KAGGLE_KERNEL","muba-daily-story-runtime").strip()
TIMEOUT=int(os.getenv("MUBA_KAGGLE_TIMEOUT","1800"))
def _api_token():
    return os.getenv("KAGGLE_API_TOKEN","").strip()
def configured():
    return bool(OWNER and KERNEL and _api_token())
def _run(args,timeout=120):
    token=_api_token()
    if not token:
        raise RuntimeError("KAGGLE_API_TOKEN is missing from the Render service environment")
    env=os.environ.copy()
    env.pop("KAGGLE_USERNAME",None)
    env.pop("KAGGLE_KEY",None)
    # Use both official non-interactive token sources. The file avoids
    # process/import token-consumption edge cases in Kaggle CLI releases.
    with tempfile.TemporaryDirectory() as auth_td:
        home=Path(auth_td)
        kaggle_dir=home/".kaggle"
        kaggle_dir.mkdir(mode=0o700)
        token_file=kaggle_dir/"access_token"
        token_file.write_text(token,encoding="utf-8")
        token_file.chmod(0o600)
        env["HOME"]=str(home)
        env["KAGGLE_API_TOKEN"]=token
        p=subprocess.run([sys.executable,"-m","kaggle",*args],env=env,capture_output=True,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError("Kaggle command failed: "+(p.stderr or p.stdout)[-1200:])
    return (p.stdout or "")+(p.stderr or "")
def _worker_source(reference_bytes,prompts):
    ref=base64.b64encode(reference_bytes).decode("ascii"); payload=json.dumps(prompts,ensure_ascii=False)
    return f'''import base64,io,subprocess,sys
subprocess.check_call([sys.executable,"-m","pip","install","-q","-U","diffusers","transformers","accelerate","sentencepiece","safetensors","huggingface_hub","bitsandbytes"])
import torch
from PIL import Image
from diffusers import DiffusionPipeline
pipe=DiffusionPipeline.from_pretrained("seochan99/Qwen-Image-Edit-2511-bnb-nf4",dtype=torch.bfloat16,device_map="balanced",max_memory={{0:"13GiB",1:"13GiB","cpu":"8GiB"}},low_cpu_mem_usage=True)
pipe.set_progress_bar_config(disable=True)
reference=Image.open(io.BytesIO(base64.b64decode({ref!r}))).convert("RGB")
prompts={payload}
previous=None
for index,prompt in enumerate(prompts,1):
    inputs=[reference] if previous is None else [reference,previous]
    previous=pipe(image=inputs,prompt=prompt,negative_prompt="collage, grid, split frame, multiple panels, text, watermark",true_cfg_scale=4.0,guidance_scale=1.0,num_inference_steps=28,num_images_per_prompt=1).images[0]
    previous.save(f"/kaggle/working/{{index:02d}}.png")
print("MUBA_DAILY_STORY_COMPLETE")
'''
def _generate(reference_bytes,prompts):
    if not configured(): raise RuntimeError("Kaggle Daily Story bridge is not configured")
    if len(prompts)!=4: raise ValueError("Daily Story requires exactly four prompts")
    kernel_id=f"{OWNER}/{KERNEL}"
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        (root/"story_worker.py").write_text(_worker_source(reference_bytes,prompts),encoding="utf-8")
        meta={"id":kernel_id,"title":"MUBA Daily Story Runtime","code_file":"story_worker.py","language":"python","kernel_type":"script","is_private":"true","enable_gpu":"true","enable_internet":"true","dataset_sources":[],"competition_sources":[],"kernel_sources":[],"model_sources":[]}
        (root/"kernel-metadata.json").write_text(json.dumps(meta),encoding="utf-8")
        _run(["kernels","push","-p",str(root),"--accelerator","NvidiaTeslaT4","-t",str(TIMEOUT)],180)
        deadline=time.time()+TIMEOUT
        while time.time()<deadline:
            status=_run(["kernels","status",kernel_id],60).lower()
            if "complete" in status: break
            if any(x in status for x in ("error","failed","cancel")): raise RuntimeError("Kaggle Daily Story run failed: "+status[-800:])
            time.sleep(15)
        else: raise RuntimeError("Kaggle Daily Story run timed out")
        out=root/"output"; out.mkdir()
        _run(["kernels","output",kernel_id,"-p",str(out),"-o","-q","--file-pattern",".*\\.png$"],180)
        result=[]
        for i in range(1,5):
            path=out/f"{i:02d}.png"
            if not path.exists(): raise RuntimeError(f"Kaggle output missing {i:02d}.png")
            result.append((path.read_bytes(),"image/png"))
        return result
async def generate_batch(reference_bytes,prompts): return await asyncio.to_thread(_generate,reference_bytes,prompts)
