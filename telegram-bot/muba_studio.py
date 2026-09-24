"""MUBA Studio: free, lightweight Telegram Mini App + inline meme renderer.

Uses the canonical public MUBA reference image and local Pillow composition.
No external AI/image-generation API is required.
"""
import hashlib, io, os, re, time
from collections import defaultdict
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

REFERENCE_URL="https://pbs.twimg.com/profile_images/2096316602623156224/FZ7iqD2r.jpg"
DAILY_LIMIT=1
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

_TEXT_REQUEST_MARKERS=(
    "write ","write:","written text","visible text","add text","text:","caption","headline","title:",
    "word:","words:","lettering","typography","says ","say:","quote:",
    "yaz ","yaz:","yazı","yazi","metin","kelime","cümle","cumle","başlık","baslik","altyazı","altyazi",
    "yazsın","yazsin","yazacak","slogan",
    "写","文字","字幕","标题","標題","标语","標語",
    "اكتب","كتابة","نص","كلمة","جملة","عنوان","عبارة",
    "लिख","टेक्स्ट","शब्द","वाक्य","शीर्षक","कैप्शन",
)

def wants_visible_text(prompt:str)->bool:
    value=" "+clean_prompt(prompt).casefold()+" "
    if any(marker in value for marker in _TEXT_REQUEST_MARKERS):
        return True
    # Quoted wording plus an explicit placement/request cue is also treated as text intent.
    if re.search(r"[\\\"'“”‘’][^\\\"'“”‘’]{1,80}[\\\"'“”‘’]",value):
        cues=(" on image "," on the image "," on top "," at the bottom "," üstüne "," üzerine "," resme "," görsele ")
        return any(cue in value for cue in cues)
    return False

def _text_policy(prompt:str)->str:
    if wants_visible_text(prompt):
        return (
            "TEXT POLICY: The user explicitly requested visible writing. Include only the wording the user requested. "
            "Do not invent extra captions, labels, logos, watermarks, slogans, random letters or additional typography. "
            "Spell the requested wording as accurately as possible."
        )
    return (
        "TEXT POLICY — STRICT: Produce an entirely text-free image. ABSOLUTELY NO visible words, letters, numbers, "
        "captions, labels, titles, speech bubbles, signs, logos, watermarks, slogans or typography anywhere in the image. "
        "Do not write MUBA on a cap, hoodie, clothing, object, background or border merely because the character is MUBA. "
        "Do not generate pseudo-text or random glyphs. This rule applies to Meme, Image, Sticker and Reaction formats."
    )

def ai_payload(prompt:str,kind:str,reference_data_uri:str)->dict:
    format_hint={
        "meme":"high-quality realistic meme scene with clear visual storytelling, expressive MUBA body language and believable lighting/environment; the image itself must work without relying on text",
        "image":"high-fidelity cinematic MUBA image with believable fur, materials, depth, lighting and environment; polished enough to feel like a finished character artwork",
        "sticker":"high-fidelity MUBA sticker with a crisp readable silhouette, strong expression, clean isolated composition and polished 3D/illustrative finish suitable for messaging",
        "emoji":"high-fidelity MUBA reaction icon focused on the face and emotion; use polished 3D emoji-like rendering with believable fur and lighting while preserving MUBA's facial identity. Make the requested emotion immediately readable (for example laughing, crying, heart-eyes, angry, surprised, sleepy or in-love) through eyes, eyelids, brows, mouth, tongue, tears or heart-eye treatment as appropriate. Do not turn MUBA into a generic yellow emoji",
    }.get(kind,"polished high-fidelity MUBA image")
    instruction=(f"Use the reference image as MUBA identity guidance, not as a rigid composition template. Keep MUBA recognizably MUBA through the core facial identity: wide expressive eyes, tan short fur, playful tongue expression, and the characteristic face proportions. Adapt the character naturally to the user's concept, pose, framing, scale, lighting, environment and visual style. Do not force a large centered MUBA portrait, circular avatar framing, black cap, or black $MUBA hoodie unless the user asks for them or they fit the scene naturally. Prefer a softer, more integrated interpretation while preserving MUBA's recognizable identity. The requested concept should lead the composition; MUBA should belong inside the scene rather than dominate it by default. {format_hint}. {_text_policy(prompt)} User request: {clean_prompt(prompt)}")
    return {"prompt":instruction,"input_image":reference_data_uri,"width":1024,"height":1024}

def render_meme(reference_bytes:bytes,prompt:str,kind:str="meme")->bytes:
    prompt=clean_prompt(prompt)
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
    if wants_visible_text(prompt):
        try: font=ImageFont.truetype("DejaVuSans-Bold.ttf",max(26,size[0]//24))
        except OSError: font=ImageFont.load_default()
        quoted=re.search(r"[\\\"'“”‘’]([^\\\"'“”‘’]{1,80})[\\\"'“”‘’]",prompt)
        caption=(quoted.group(1).strip() if quoted else prompt)[:90]
        words=caption.split(); lines=[]; cur=""
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
*{{box-sizing:border-box}}body{{margin:0;background:#07040f;color:#fff;font-family:system-ui;padding:22px}}.card{{max-width:620px;margin:auto;background:#120a1f;border:1px solid #7c3aed;border-radius:24px;padding:20px;box-shadow:0 0 35px #6d28d955}}h1{{margin:0 0 6px}}small{{color:#b8a8d4}}img{{width:150px;height:150px;object-fit:cover;border-radius:50%;border:4px solid #b026ff;display:block;margin:18px auto}}textarea{{width:100%;min-height:105px;background:#090510;color:#fff;border:1px solid #51326f;border-radius:15px;padding:14px;font-size:16px}}.types{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}}button{{border:0;border-radius:13px;padding:13px;font-weight:700}}.type{{background:#241638;color:#ddd}}.type.on{{outline:2px solid #d946ef;color:#fff}}#go{{width:100%;background:linear-gradient(135deg,#b026ff,#7c3aed);color:#fff;font-size:17px}}#msg{{text-align:center;color:#d8c7ee;margin-top:12px}}#preview{{width:100%;height:auto;border-radius:16px;border:0;margin-top:14px;display:none}}#actions{{display:none;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}}#actions a,#actions button{{display:flex;align-items:center;justify-content:center;gap:7px;min-height:48px;text-align:center;text-decoration:none;background:linear-gradient(135deg,#2b1741,#1b102b);color:#fff;border:1px solid #8b5cf6;border-radius:14px;padding:12px 14px;font-weight:750;font-size:15px;box-shadow:0 6px 18px #0006,0 0 16px #7c3aed22;transition:transform .15s ease,box-shadow .15s ease,border-color .15s ease}}#actions a:active,#actions button:active{{transform:scale(.97)}}#actions a:hover,#actions button:hover{{border-color:#d946ef;box-shadow:0 7px 22px #0008,0 0 20px #d946ef33}}</style></head><body><div class="card">
<h1>🎭 MUBA Studio</h1><small>Create with the original MUBA. Daily limit: 1.</small>
<img src="{REFERENCE_URL}" alt="MUBA"><textarea id="p" maxlength="120" placeholder="Describe the MUBA visual. Add visible text only if you want words in the image."></textarea>
<div class="types"><button class="type on" data-k="meme">🖼 Meme</button><button class="type" data-k="image">✨ Image</button><button class="type" data-k="sticker">😄 Sticker</button><button class="type" data-k="emoji">🙂 Emoji</button></div>
<button id="go">CREATE</button><div id="msg"></div><img id="preview"><div id="actions"><a id="download" href="#" target="_blank">⬇️ Download</a><button id="copy" type="button">🔗 Copy link</button></div>
</div><script>
const tg=window.Telegram.WebApp;tg.ready();tg.expand();let kind='meme';
document.querySelectorAll('.type').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.type').forEach(x=>x.classList.remove('on'));b.classList.add('on');kind=b.dataset.k}});
document.getElementById('go').onclick=async()=>{{let prompt=document.getElementById('p').value.trim();if(!prompt)return;
let r=await fetch('{b}/studio/generate',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify({{initData:tg.initData,uid:new URLSearchParams(location.search).get('uid'),studioToken:new URLSearchParams(location.search).get('st'),prompt,kind}})}});
let m=document.getElementById('msg');if(!r.ok){{m.textContent=(await r.json()).error||'Could not create.';return}}
let outputUrl=r.headers.get('X-MUBA-Output-URL');await r.blob();if(!outputUrl){{m.textContent='Could not create a shareable output.';return}}let im=document.getElementById('preview');im.src=outputUrl;im.style.display='block';let actions=document.getElementById('actions');actions.style.display='grid';document.getElementById('download').href=outputUrl+'?download=1';document.getElementById('copy').onclick=async()=>{{try{{await navigator.clipboard.writeText(outputUrl);m.textContent='Link copied.'}}catch(e){{prompt('Copy this link:',outputUrl)}}}};let rem=r.headers.get('X-MUBA-Remaining');m.textContent='Created with MUBA AI. '+(rem==='DEV'?'DEV unlimited':rem+'/1 left today.')}};
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
