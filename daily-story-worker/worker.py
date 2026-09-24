from __future__ import annotations
import json,os,time,uuid
from pathlib import Path
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/"config.json").read_text())
COMFY=os.getenv("MUBA_COMFY_URL","http://127.0.0.1:8188").rstrip("/")
CHECKPOINT=os.getenv("MUBA_COMFY_CHECKPOINT",CFG["model"]["default_checkpoint"])

def load_job(path):
    job=json.loads(Path(path).read_text(encoding="utf-8"))
    chapters=job.get("chapters") or []
    if len(chapters)!=4: raise ValueError("Daily Story job requires exactly four chapters")
    ref=Path(job["reference_path"])
    if not ref.exists(): raise FileNotFoundError(ref)
    return job,ref

def workflow(prompt,seed):
    wf=json.loads((ROOT/CFG["workflow"]).read_text())
    wf["4"]["inputs"]["ckpt_name"]=CHECKPOINT
    wf["6"]["inputs"]["text"]=prompt
    wf["3"]["inputs"]["seed"]=int(seed)
    return wf

def queue(wf):
    client=str(uuid.uuid4())
    r=requests.post(COMFY+"/prompt",json={"prompt":wf,"client_id":client},timeout=30);r.raise_for_status()
    return r.json()["prompt_id"]

def wait(pid,timeout=600):
    end=time.time()+timeout
    while time.time()<end:
        r=requests.get(COMFY+"/history/"+pid,timeout=30);r.raise_for_status()
        data=r.json()
        if pid in data:
            images=[]
            for node in data[pid].get("outputs",{}).values(): images.extend(node.get("images",[]))
            if images:return images[-1]
        time.sleep(2)
    raise TimeoutError(pid)

def fetch(meta,dest):
    r=requests.get(COMFY+"/view",params={"filename":meta["filename"],"subfolder":meta.get("subfolder",""),"type":meta.get("type","output")},timeout=60);r.raise_for_status()
    Path(dest).write_bytes(r.content)
    with Image.open(dest) as im:
        if im.size!=(1024,576): raise ValueError(f"Invalid output size: {im.size}")

def run(job_path,out_dir):
    job,ref=load_job(job_path); out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    # V11 validates the fresh reference at the worker boundary. The first low-VRAM
    # workflow is prompt-conditioned; reference adapters can be inserted later
    # without changing the job or Telegram contracts.
    with Image.open(ref) as im: im.verify()
    results=[]
    for i,ch in enumerate(job["chapters"],1):
        prompt=ch["prompt"]+" CURRENT CHAPTER ONLY. Same canonical MUBA identity as the supplied Daily Story reference."
        pid=queue(workflow(prompt,int(job.get("seed",260925))+i))
        dest=out/f"chapter_{i:02d}.png";fetch(wait(pid),dest);results.append(str(dest))
    result={"schema_version":1,"job_id":job["job_id"],"day":job["day"],"status":"complete","images":results}
    (out/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8");return result

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("job");ap.add_argument("--out",default="output");a=ap.parse_args()
    print(json.dumps(run(a.job,a.out),indent=2))
