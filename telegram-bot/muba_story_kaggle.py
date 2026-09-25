"""On-demand Kaggle T4 x2 batch bridge for MUBA Daily Story."""
from __future__ import annotations
import asyncio, base64, io, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image
OWNER=os.getenv("MUBA_KAGGLE_OWNER","mubarh").strip()
KERNEL=os.getenv("MUBA_KAGGLE_KERNEL","muba-daily-story-runtime").strip()
TIMEOUT=int(os.getenv("MUBA_KAGGLE_TIMEOUT","1800"))
WORKER=Path(__file__).resolve().parent.parent/"daily-story-worker"
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
    names=("kaggle_bootstrap.py","worker.py","config.json","muba_master_reference_v1.json","requirements.txt")
    sources={name:base64.b64encode((WORKER/name).read_bytes()).decode("ascii") for name in names}
    sources["reference.png"]=base64.b64encode(reference_bytes).decode("ascii")
    job={"job_id":"kaggle-daily-story","day":"on-demand","seed":260925,
         "reference_path":"/kaggle/working/muba-story/reference.png",
         "chapters":[{"prompt":prompt} for prompt in prompts]}
    return "import base64,json,pathlib,shutil,subprocess,sys,time,urllib.request\n"+\
           "files="+repr(sources)+"\njob="+repr(job)+"\n"+'''
root=pathlib.Path("/kaggle/working/muba-story")
root.mkdir(parents=True,exist_ok=True)
for name,encoded in files.items():
    (root/name).write_bytes(base64.b64decode(encoded))
(root/"job.json").write_text(json.dumps(job),encoding="utf-8")
subprocess.check_call([sys.executable,str(root/"kaggle_bootstrap.py")],timeout=1200)
server=subprocess.Popen([sys.executable,"/kaggle/working/ComfyUI/main.py","--listen","127.0.0.1","--port","8188","--lowvram"],stdout=sys.stdout,stderr=subprocess.STDOUT)
try:
    for attempt in range(120):
        if server.poll() is not None:
            raise RuntimeError("ComfyUI exited before the API became ready")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8188/system_stats",timeout=2) as response:
                if response.status==200: break
        except Exception:
            time.sleep(2)
    else:
        raise RuntimeError("ComfyUI API did not start")
    subprocess.check_call([sys.executable,str(root/"worker.py"),str(root/"job.json"),"--out",str(root/"output")],timeout=1200)
    for i in range(1,5):
        shutil.copyfile(root/"output"/f"chapter_{i:02d}.png",pathlib.Path("/kaggle/working")/f"{i:02d}.png")
    print("MUBA_DAILY_STORY_COMPLETE",flush=True)
finally:
    server.terminate()
    try: server.wait(timeout=10)
    except subprocess.TimeoutExpired: server.kill()
'''
def _generate(reference_bytes,prompts):
    if not configured(): raise RuntimeError("Kaggle Daily Story bridge is not configured")
    if len(prompts)!=4: raise ValueError("Daily Story requires exactly four prompts")
    if not (WORKER/"kaggle_bootstrap.py").is_file(): raise RuntimeError("ComfyUI Daily Story worker is missing")
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
            body=path.read_bytes()
            with Image.open(io.BytesIO(body)) as im:
                im.verify()
            with Image.open(io.BytesIO(body)) as im:
                if im.size!=(1024,576): raise RuntimeError(f"Kaggle frame {i} has invalid dimensions")
            result.append((body,"image/png"))
        return result
async def generate_batch(reference_bytes,prompts): return await asyncio.to_thread(_generate,reference_bytes,prompts)
