"""MUBA Studio — isolated Assistant module. No Guardian dependency."""
import hashlib, io, time, hmac, json
from collections import defaultdict
from urllib.parse import parse_qsl
from PIL import Image, ImageDraw, ImageFont

REFERENCE_URL="https://pbs.twimg.com/profile_images/2096316602623156224/FZ7iqD2r.jpg"
DAILY_LIMIT=5
_usage=defaultdict(lambda:{"day":"","count":0})

def _day(): return time.strftime("%Y-%m-%d",time.gmtime())
def remaining(uid):
    r=_usage[int(uid)]; d=_day()
    if r["day"]!=d:r.update(day=d,count=0)
    return max(0,DAILY_LIMIT-r["count"])
def consume(uid):
    r=_usage[int(uid)]; d=_day()
    if r["day"]!=d:r.update(day=d,count=0)
    if r["count"]>=DAILY_LIMIT:return False
    r["count"]+=1;return True
def clean_prompt(v): return " ".join((v or "").strip().split())[:120]
def validate_init_data(raw,token):
    if not raw:return None
    data=dict(parse_qsl(raw,keep_blank_values=True)); supplied=data.pop("hash",None)
    if not supplied:return None
    check="\n".join(f"{k}={v}" for k,v in sorted(data.items()))
    secret=hmac.new(b"WebAppData",token.encode(),hashlib.sha256).digest()
    if not hmac.compare_digest(hmac.new(secret,check.encode(),hashlib.sha256).hexdigest(),supplied):return None
    try:return json.loads(data.get("user","{}"))
    except Exception:return None
def render_meme(raw,prompt,kind="meme"):
    src=Image.open(io.BytesIO(raw)).convert("RGB")
    size=(512,512) if kind in ("sticker","emoji") else (1200,675)
    out=Image.new("RGB",size,(9,5,18)); side=min(size[1]-90,500)
    avatar=src.resize((side,side)); x=(size[0]-side)//2; out.paste(avatar,(x,18))
    d=ImageDraw.Draw(out); d.rounded_rectangle((x-7,11,x+side+7,25+side),radius=25,outline=(188,74,255),width=7)
    try:f=ImageFont.truetype("DejaVuSans-Bold.ttf",max(24,size[0]//25))
    except OSError:f=ImageFont.load_default()
    text=clean_prompt(prompt) or "WE LIVE HERE NOW"; text=text[:70]
    box=d.textbbox((0,0),text,font=f); tw=box[2]-box[0]
    d.rounded_rectangle((max(10,(size[0]-tw)//2-15),size[1]-70,min(size[0]-10,(size[0]+tw)//2+15),size[1]-12),radius=14,fill=(0,0,0))
    d.text((size[0]//2,size[1]-58),text,font=f,fill="white",anchor="ma")
    b=io.BytesIO();out.save(b,"JPEG",quality=90);return b.getvalue()
def studio_html(base):
    base=base.rstrip("/")
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://telegram.org/js/telegram-web-app.js"></script><style>body{{background:#07040f;color:white;font-family:system-ui;padding:20px}}main{{max-width:600px;margin:auto;background:#120a1f;padding:20px;border-radius:22px}}img{{width:150px;height:150px;object-fit:cover;border-radius:50%;display:block;margin:auto;border:4px solid #b026ff}}textarea{{width:100%;min-height:100px;margin:18px 0;background:#090510;color:white;border:1px solid #7c3aed;border-radius:14px;padding:12px;box-sizing:border-box}}button{{padding:12px;border:0;border-radius:12px;margin:4px}}#go{{width:100%;background:#8b2be2;color:white;font-weight:bold}}#preview{{width:100%;height:auto;border-radius:14px;display:none;margin-top:15px}}</style></head><body><main><h2>🎭 MUBA Studio</h2><p>Original MUBA • 5 creations/day</p><img src="{REFERENCE_URL}"><textarea id="p" maxlength="120" placeholder="What should MUBA say?"></textarea><div id="k"><button data-v="meme">🖼 Meme</button><button data-v="image">✨ Image</button><button data-v="sticker">😄 Sticker</button><button data-v="emoji">🙂 Emoji</button></div><button id="go">CREATE</button><p id="m"></p><img id="preview"></main><script>const tg=Telegram.WebApp;tg.ready();tg.expand();let kind="meme";document.querySelectorAll("#k button").forEach(b=>b.onclick=()=>kind=b.dataset.v);go.onclick=async()=>{{let prompt=p.value.trim();if(!prompt)return;let r=await fetch("{base}/studio/generate",{{method:"POST",headers:{{"content-type":"application/json"}},body:JSON.stringify({{initData:tg.initData,prompt,kind}})}});if(!r.ok){{m.textContent=(await r.json()).error;return}}let u=URL.createObjectURL(await r.blob());preview.src=u;preview.style.display="block";m.textContent=r.headers.get("X-MUBA-Remaining")+"/5 left today";}};</script></body></html>'''
