"""On-demand Kaggle T4 x2 batch bridge for MUBA Daily Story."""
from __future__ import annotations
import asyncio, base64, hashlib, hmac, io, json, os, subprocess, sys, tempfile, time
from datetime import datetime, timezone
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
def _download_output(kernel_id,out):
    args=["kernels","output",kernel_id,"-p",str(out),"-o","-q","--file-pattern",".*\\.png$"]
    for delay in (10,20,30):
        try:
            return _run(args,180)
        except RuntimeError as exc:
            # Kaggle can rate-limit output listing just after a completed run.
            # Retrying here preserves the finished GPU work; never push again.
            if "429" not in str(exc) or "ListKernelSessionOutput" not in str(exc):
                raise
            time.sleep(delay)
    return _run(args,180)
def _r2_upload_url(key):
    """Give the GPU a short-lived, single-object upload permission, never R2 keys."""
    from muba_gallery import _aws_quote, _r2_config
    cfg=_r2_config()
    if not cfg: raise RuntimeError("Daily Story Kaggle requires the private R2 archive")
    host=f'{cfg["account"]}.r2.cloudflarestorage.com'
    uri="/"+_aws_quote(cfg["bucket"])+"/"+"/".join(_aws_quote(p) for p in key.split("/"))
    now=datetime.now(timezone.utc)
    date=now.strftime("%Y%m%d")
    scope=f"{date}/auto/s3/aws4_request"
    fields={"X-Amz-Algorithm":"AWS4-HMAC-SHA256",
            "X-Amz-Credential":f'{cfg["access"]}/{scope}',
            "X-Amz-Date":now.strftime("%Y%m%dT%H%M%SZ"),
            "X-Amz-Expires":"21600","X-Amz-SignedHeaders":"host"}
    query="&".join(f"{_aws_quote(k)}={_aws_quote(v)}" for k,v in sorted(fields.items()))
    request="\n".join(("PUT",uri,query,f"host:{host}\n","host","UNSIGNED-PAYLOAD"))
    to_sign="\n".join(("AWS4-HMAC-SHA256",fields["X-Amz-Date"],scope,
                        hashlib.sha256(request.encode()).hexdigest()))
    def sign(secret,value): return hmac.new(secret,value.encode(),hashlib.sha256).digest()
    secret=sign(("AWS4"+cfg["secret"]).encode(),date)
    secret=sign(sign(sign(secret,"auto"),"s3"),"aws4_request")
    signature=hmac.new(secret,to_sign.encode(),hashlib.sha256).hexdigest()
    return f"https://{host}{uri}?{query}&X-Amz-Signature={signature}"

def _r2_image(key):
    from muba_gallery import _r2_request
    response=_r2_request("GET",key,allow_missing=True)
    return response.content if response is not None else None

def _worker_source(reference_bytes,prompts,upload_url=None):
    names=("kaggle_bootstrap.py","worker.py","config.json","muba_master_reference_v1.json","muba_daily_story_master_reference.png","requirements.txt")
    sources={name:base64.b64encode((WORKER/name).read_bytes()).decode("ascii") for name in names}
    sources["reference.png"]=base64.b64encode(reference_bytes).decode("ascii")
    job={"job_id":"kaggle-daily-story","day":"on-demand","seed":260925,
         "reference_path":"/kaggle/working/muba-story/reference.png",
         "chapters":[{"prompt":prompt} for prompt in prompts]}
    return "import base64,json,pathlib,shutil,subprocess,sys,time,urllib.request\n"+\
           "files="+repr(sources)+"\njob="+repr(job)+"\nupload_url="+repr(upload_url)+"\n"+'''
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
    shutil.copyfile(root/"output"/"scene.png",pathlib.Path("/kaggle/working")/"01.png")
    if upload_url:
        image=pathlib.Path("/kaggle/working/01.png").read_bytes()
        request=urllib.request.Request(upload_url,data=image,method="PUT",headers={"Content-Type":"image/png"})
        with urllib.request.urlopen(request,timeout=120) as response:
            if response.status not in (200,201,204): raise RuntimeError("Daily Story private archive upload failed")
finally:
    server.terminate()
    try: server.wait(timeout=10)
    except subprocess.TimeoutExpired: server.kill()
# Kaggle otherwise publishes hundreds of ComfyUI/model files as kernel output.
# Keep only the scene so the output listing stays small and the GPU work is reusable.
shutil.rmtree(root,ignore_errors=True)
shutil.rmtree("/kaggle/working/ComfyUI",ignore_errors=True)
for unused in pathlib.Path("/kaggle/working").glob("comfyui-*.zip"):
    unused.unlink(missing_ok=True)
print("MUBA_DAILY_STORY_COMPLETE",flush=True)
'''
def _generate(reference_bytes,prompts,day=None,fresh=False):
    if not configured(): raise RuntimeError("Kaggle Daily Story bridge is not configured")
    if len(prompts)!=1: raise ValueError("Daily Story requires exactly one prompt")
    if not (WORKER/"kaggle_bootstrap.py").is_file(): raise RuntimeError("ComfyUI Daily Story worker is missing")
    kernel_id=f"{OWNER}/{KERNEL}"
    signature=hashlib.sha256(reference_bytes+prompts[0].encode("utf-8")).hexdigest()
    from muba_story import STORE
    key=f"daily-story/kaggle/{day or 'adhoc'}/{signature}.png"
    # Fetching this one object avoids Kaggle's rate-limited output listing.
    # A restarted Render worker can also recover the result without a new run.
    if day and not fresh:
        existing=_r2_image(key)
        if existing: return _checked_image(existing)
    saved=STORE.get("story_kaggle_job",day,None) if day and not fresh else None
    reuse=isinstance(saved,dict) and saved.get("signature")==signature and saved.get("kernel")==kernel_id
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        if not reuse:
            (root/"story_worker.py").write_text(_worker_source(reference_bytes,prompts,_r2_upload_url(key)),encoding="utf-8")
            meta={"id":kernel_id,"title":"MUBA Daily Story Runtime","code_file":"story_worker.py","language":"python","kernel_type":"script","is_private":"true","enable_gpu":"true","enable_internet":"true","dataset_sources":[],"competition_sources":[],"kernel_sources":[],"model_sources":[]}
            (root/"kernel-metadata.json").write_text(json.dumps(meta),encoding="utf-8")
            _run(["kernels","push","-p",str(root),"--accelerator","NvidiaTeslaT4","-t",str(TIMEOUT)],180)
            if day: STORE.set("story_kaggle_job",day,{"signature":signature,"kernel":kernel_id})
        deadline=time.time()+TIMEOUT
        while time.time()<deadline:
            status=_run(["kernels","status",kernel_id],60).lower()
            if "complete" in status: break
            if any(x in status for x in ("error","failed","cancel")): raise RuntimeError("Kaggle Daily Story run failed: "+status[-800:])
            time.sleep(30)
        else: raise RuntimeError("Kaggle Daily Story run timed out")
        for _ in range(5):
            body=_r2_image(key)
            if body: return _checked_image(body)
            time.sleep(2)
        # A legacy run may have completed before direct archive delivery existed.
        out=root/"output"; out.mkdir()
        _download_output(kernel_id,out)
        path=out/"01.png"
        if not path.exists(): raise RuntimeError("Kaggle output missing 01.png")
        return _checked_image(path.read_bytes())

def _checked_image(body):
    with Image.open(io.BytesIO(body)) as im: im.verify()
    with Image.open(io.BytesIO(body)) as im:
        if im.size!=(1024,576): raise RuntimeError("Kaggle frame has invalid dimensions")
    return [(body,"image/png")]
async def generate_batch(reference_bytes,prompts,day=None,fresh=False):
    return await asyncio.to_thread(_generate,reference_bytes,prompts,day,fresh)
