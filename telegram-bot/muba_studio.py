"""MUBA Studio: free, lightweight Telegram Mini App + inline meme renderer.

Uses the canonical public MUBA reference image and local Pillow composition.
No external AI/image-generation API is required.
"""
import hashlib, io, os, time
from collections import defaultdict
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

REFERENCE_URL="https://pbs.twimg.com/profile_images/2096316602623156224/FZ7iqD2r.jpg"
DAILY_LIMIT=3
DEV_USER_ID=934598759
AI_MODEL="@cf/black-forest-labs/flux-2-klein-4b"
_usage=defaultdict(lambda: {"day":"","count":0})
_cache={"image":None,"at":0.0}

def _day():
    return time.strftime("%Y-%m-%d", time.gmtime())

def is_dev(user_id:int)->bool:
    return int(user_id)==DEV_USER_ID

def remaining(user_id:int)->int:
    if is_dev(user_id): return 999
    row=_usage[int(user_id)]; day=_day()
    if row["day"]!=day: row.update(day=day,count=0)
    return max(0,DAILY_LIMIT-row["count"])

def consume(user_id:int)->bool:
    if is_dev(user_id): return True
    row=_usage[int(user_id)]; day=_day()
    if row["day"]!=day: row.update(day=day,count=0)
    if row["count"]>=DAILY_LIMIT: return False
    row["count"]+=1; return True

def clean_prompt(value:str)->str:
    return " ".join((value or "").strip().split())[:120]

def ai_configured()->bool:
    return bool(os.getenv("CLOUDFLARE_ACCOUNT_ID") and os.getenv("CLOUDFLARE_API_TOKEN"))

def ai_endpoint()->str:
    account=os.environ["CLOUDFLARE_ACCOUNT_ID"]
    return f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{AI_MODEL}"

def ai_payload(prompt:str,kind:str,reference_data_uri:str)->dict:
    format_hint={"meme":"cinematic meme image, leave clean space for a short caption","image":"polished cinematic image","sticker":"single expressive sticker subject, simple clean background","emoji":"single expressive emoji-like reaction, centered, simple clean background"}.get(kind,"polished image")
    instruction=(f"Create a new scene featuring the same MUBA character shown in the reference image. Preserve the recognizable face, huge expressive eyes, tan short fur, tongue, black MUBA cap and black $MUBA hoodie. {format_hint}. User request: {clean_prompt(prompt)}")
    return {"prompt":instruction,"input_image":reference_data_uri,"width":1024,"height":1024}

def render_meme(reference_bytes:bytes,prompt:str,kind:str="meme")->bytes:
    prompt=clean_prompt(prompt) or "WE LIVE HERE NOW"
    src=Image.open(io.BytesIO(reference_bytes)).convert("RGB")
    if kind in ("sticker","emoji"):
        size=(512,512)
    else:
        size=(1200,675)
    canvas=Image.new("RGB",size,(9,5,18))
    draw=ImageDraw.Draw(canvas)
    # Purple MUBA frame, with the original image preserved rather than redrawn.
    side=min(size[1]-70,520)
    avatar=src.resize((side,side))
    x=(size[0]-side)//2; y=20
    canvas.paste(avatar,(x,y))
    draw.rounded_rectangle((x-8,y-8,x+side+8,y+side+8),radius=30,outline=(188,74,255),width=8)
    try: font=ImageFont.truetype("DejaVuSans-Bold.ttf",max(26,size[0]//24))
    except OSError: font=ImageFont.load_default()
    words=prompt.split(); lines=[]; cur=""
    maxchars=30 if size[0]>600 else 18
    for w in words:
        nxt=(cur+" "+w).strip()
        if len(nxt)>maxchars and cur: lines.append(cur); cur=w
        else: cur=nxt
    if cur: lines.append(cur)
    lines=lines[:3]
    text="\\n".join(lines)
    box=draw.multiline_textbbox((0,0),text,font=font,spacing=8,align="center")
    tw=box[2]-box[0]; th=box[3]-box[1]
    ty=size[1]-th-24
    draw.rounded_rectangle((max(12,(size[0]-tw)//2-18),ty-12,min(size[0]-12,(size[0]+tw)//2+18),size[1]-10),radius=16,fill=(0,0,0))
    draw.multiline_text((size[0]//2,ty),text,font=font,fill="white",anchor="ma",spacing=8,align="center")
    out=io.BytesIO(); canvas.save(out,"JPEG",quality=90,optimize=True); return out.getvalue()

def studio_html(base_url:str)->str:
    b=base_url.rstrip("/")
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://telegram.org/js/telegram-web-app.js"></script><style>
*{{box-sizing:border-box}}body{{margin:0;background:#07040f;color:#fff;font-family:system-ui;padding:22px}}.card{{max-width:620px;margin:auto;background:#120a1f;border:1px solid #7c3aed;border-radius:24px;padding:20px;box-shadow:0 0 35px #6d28d955}}h1{{margin:0 0 6px}}small{{color:#b8a8d4}}img{{width:150px;height:150px;object-fit:cover;border-radius:50%;border:4px solid #b026ff;display:block;margin:18px auto}}textarea{{width:100%;min-height:105px;background:#090510;color:#fff;border:1px solid #51326f;border-radius:15px;padding:14px;font-size:16px}}.types{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}}button{{border:0;border-radius:13px;padding:13px;font-weight:700}}.type{{background:#241638;color:#ddd}}.type.on{{outline:2px solid #d946ef;color:#fff}}#go{{width:100%;background:linear-gradient(135deg,#b026ff,#7c3aed);color:#fff;font-size:17px}}#msg{{text-align:center;color:#d8c7ee;margin-top:12px}}#preview{{width:100%;height:auto;border-radius:16px;border:0;margin-top:14px;display:none}}</style></head><body><div class="card">
<h1>🎭 MUBA Studio</h1><small>Create with the original MUBA. Daily limit: 3.</small>
<img src="{REFERENCE_URL}" alt="MUBA"><textarea id="p" maxlength="120" placeholder="What should your MUBA meme say?"></textarea>
<div class="types"><button class="type on" data-k="meme">🖼 Meme</button><button class="type" data-k="image">✨ Image</button><button class="type" data-k="sticker">😄 Sticker</button><button class="type" data-k="emoji">🙂 Emoji</button></div>
<button id="go">CREATE</button><div id="msg"></div><img id="preview">
</div><script>
const tg=window.Telegram.WebApp;tg.ready();tg.expand();let kind='meme';
document.querySelectorAll('.type').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.type').forEach(x=>x.classList.remove('on'));b.classList.add('on');kind=b.dataset.k}});
document.getElementById('go').onclick=async()=>{{let prompt=document.getElementById('p').value.trim();if(!prompt)return;
let r=await fetch('{b}/studio/generate',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify({{initData:tg.initData,uid:new URLSearchParams(location.search).get('uid'),studioToken:new URLSearchParams(location.search).get('st'),prompt,kind}})}});
let m=document.getElementById('msg');if(!r.ok){{m.textContent=(await r.json()).error||'Could not create.';return}}
let blob=await r.blob(),u=URL.createObjectURL(blob),im=document.getElementById('preview');im.src=u;im.style.display='block';let rem=r.headers.get('X-MUBA-Remaining');m.textContent='Created with MUBA AI. '+(rem==='DEV'?'DEV unlimited':rem+'/3 left today.')}};
</script></body></html>"""

def studio_token(user_id:int,bot_token:str)->str:
    return hashlib.sha256(("studio:"+str(int(user_id))+":"+bot_token).encode()).hexdigest()

def validate_studio_token(user_id,token:str,bot_token:str):
    import hmac
    try: uid=int(user_id)
    except (TypeError,ValueError): return None
    expected=studio_token(uid,bot_token)
    return {"id":uid} if token and hmac.compare_digest(expected,str(token)) else None

def validate_init_data(init_data:str,bot_token:str):
    from urllib.parse import parse_qsl
    import hmac, json
    if not init_data: return None
    data=dict(parse_qsl(init_data,keep_blank_values=True)); supplied=data.pop("hash",None)
    if not supplied: return None
    check="\\n".join(f"{k}={v}" for k,v in sorted(data.items()))
    secret=hmac.new(b"WebAppData",bot_token.encode(),hashlib.sha256).digest()
    calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc,supplied): return None
    try: return json.loads(data.get("user","{}"))
    except Exception: return None
