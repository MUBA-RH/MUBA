"""MUBA Daily Story Director.

Builds one four-scene visual story draft per Istanbul calendar day from the
canonical MUBA history. Drafting is deterministic and read-only. Publishing is
DEV-controlled and stores only approval state; image generation remains a
separate Studio operation so the production baseline is never auto-published.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from muba_brain import STORE

TZ=ZoneInfo("Europe/Istanbul")
HISTORY_PATH=Path(__file__).resolve().parents[1]/"muba_history.json"

CHARACTER_ANCHOR=(
    "Preserve the supplied MUBA reference identity exactly: the same large expressive eyes, tan short dense fur, "
    "small nose, playful tongue, black MUBA cap, black hoodie and recognizable face proportions. Do not redesign "
    "MUBA into a generic cute animal. Art direction: polished modern manga/anime illustration with comic-panel storytelling: "
    "clean expressive ink lines, refined cel shading, selective soft digital painting, luminous but restrained highlights, crisp high-resolution finish, elegant color separation and dynamic manga composition. Mostly illustrated, only lightly digital; no photorealism, no plush/toy render, no 3D mascot look, no glossy CGI. The manga reference is a QUALITY/FINISH target only, never a character-design source. "
)

STORY_BIBLE=(
    "Treat all four frames as ONE continuous mini-episode, not four independent portraits. Keep the exact same MUBA "
    "design, wardrobe, location, time of day, lighting direction and recurring props across every frame. Each frame must "
    "visibly advance the action from the previous frame. Use varied camera language: establishing shot, action/interaction "
    "shot, expressive reaction, then a resolving final shot. Do not repeat the same portrait composition. "
)

def _history():
    try:
        payload=json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return list(payload.get("entries",[]))
    except (OSError,ValueError):
        return []

def _public_change(day):
    # Technical-only maintenance is not forced into the story. Prefer the newest
    # user-facing change from today, then fall back to MUBA's established world.
    for item in _history():
        if item.get("date")!=day: continue
        areas=set(item.get("areas",()))
        if areas & {"assistant","daily","gallery","studio","web","telegram","guardian"}:
            return item
    return None

def _episode_for_day(day):
    """Concrete deterministic episode seed; avoids vague 'something happened' plots."""
    options=[
        {
            "title":"The Box That Knocked Back","title_tr":"Karşılık Veren Kutu",
            "premise":"In a narrow old-city alley, MUBA finds a small weathered wooden box beside a closed shop. When MUBA taps the lid, something inside taps back.",
            "premise_tr":"Eski şehirde dar bir sokakta MUBA, kapalı bir dükkânın yanında küçük ve yıpranmış ahşap bir kutu bulur. Kapağı tıklatınca içeriden aynı şekilde karşılık gelir.",
            "labels":["KNOCK.","KNOCK?","OH.","YOURS."],
            "story":"At the end of a quiet alley, MUBA noticed a battered wooden box that definitely had not been there a moment ago. One cautious knock on the lid came back from inside. Naturally, MUBA knocked again. The box jumped, the lid cracked open, and a tiny wind-up bird burst out carrying a biscuit almost as large as itself. It dropped the biscuit at MUBA's feet, folded its metal wings and disappeared back into the box. MUBA stared at the unexpected delivery for a second, then sat beside the box and shared the biscuit with whoever—or whatever—was still knocking from inside.",
            "story_tr":"Sessiz bir sokağın sonunda MUBA, az önce orada olmadığına emin olduğu eski bir ahşap kutu fark etti. Kapağa temkinli bir kez vurdu; içeriden aynı vuruşla cevap geldi. Elbette MUBA bir kez daha vurdu. Kutu sıçradı, kapak aralandı ve içinden neredeyse kendisi kadar büyük bir bisküvi taşıyan minik kurmalı bir kuş çıktı. Bisküviyi MUBA'nın ayaklarının önüne bıraktı, metal kanatlarını kapattı ve tekrar kutunun içine kayboldu. MUBA beklenmedik teslimata bir an baktı, sonra kutunun yanına oturup bisküviyi içeride hâlâ tıklatan her kimse—ya da her neyse—onunla paylaştı."
        },
        {
            "title":"The Runaway Paper","title_tr":"Kaçak Kâğıt",
            "premise":"On a breezy neighborhood street, a folded paper slips from a bench and keeps escaping MUBA every time it is almost caught.",
            "premise_tr":"Rüzgârlı bir mahalle sokağında banktan uçan katlanmış bir kâğıt, MUBA her yaklaştığında yeniden kaçmaya başlar.",
            "labels":["HEY.","GOTCHA—","NOPE.","FINE."],
            "story":"A folded piece of paper skated past MUBA's shoes and stopped just long enough to look catchable. It was a trap. Every time MUBA reached down, the wind carried it a few steps farther through the same street. The chase passed one bench, one puddle and one increasingly annoyed MUBA. At last the paper landed against a wall. MUBA pounced—and unfolded a completely blank sheet. Before the disappointment could settle in, the wind lifted MUBA's cap instead. The paper stayed put. MUBA chased the cap. Apparently the street had chosen a new game.",
            "story_tr":"Katlanmış bir kâğıt MUBA'nın ayaklarının önünden kayıp geçti ve tam yakalanabilecekmiş gibi durdu. Bu bir tuzaktı. MUBA her eğildiğinde rüzgâr kâğıdı aynı sokakta birkaç adım daha ileri taşıdı. Kovalamaca bir bankı, bir su birikintisini ve giderek sinirlenen bir MUBA'yı geride bıraktı. Sonunda kâğıt bir duvara yaslandı. MUBA üzerine atladı—ve tamamen boş bir sayfa açtı. Hayal kırıklığı daha yerleşemeden rüzgâr bu kez MUBA'nın şapkasını kaptı. Kâğıt yerinde kaldı. MUBA şapkanın peşinden koştu. Görünüşe göre sokak yeni bir oyun seçmişti."
        },
    ]
    return options[sum(ord(x) for x in str(day))%len(options)]

def draft(day=None):
    day=day or datetime.now(TZ).date().isoformat()
    change=_public_change(day)
    truth=((change.get("text") or {}).get("en") if change else None) or "No public ecosystem development is required for this episode."
    truth_tr=((change.get("text") or {}).get("tr") if change else None) or "Bu bölüm için herkese açık bir ekosistem gelişmesi gerekmiyor."
    ep=_episode_for_day(day)
    theme=ep["title"]
    theme_tr=ep["title_tr"]
    labels=ep["labels"]
    actions=[
        "FRAME 1 — ESTABLISH. Wide shot. Show MUBA discovering the exact story object in the stated location. The object and surrounding geography must be clearly readable.",
        "FRAME 2 — ACTION. Continue seconds later. Show MUBA physically interacting with that same object and the first consequence. Preserve exact spatial placement and environmental details.",
        "FRAME 3 — TURN. Continue the consequence. Show the concrete surprise/reveal from the premise with a strong MUBA reaction. This must visibly follow frame 2.",
        "FRAME 4 — PAYOFF. Continue immediately. Resolve the exact event with the story's visual punchline and a satisfying ending composition.",
    ]
    actions_tr=[
        "Kare 1 — Kurulum: geniş planda MUBA'nın hikâyedeki somut nesneyi belirtilen mekânda bulduğu an gösterilir.",
        "Kare 2 — Eylem: birkaç saniye sonrası; MUBA aynı nesneyle fiziksel olarak etkileşir ve ilk sonuç ortaya çıkar.",
        "Kare 3 — Dönüm: ikinci karenin sonucu devam eder; hikâyedeki somut sürpriz açığa çıkar ve MUBA belirgin tepki verir.",
        "Kare 4 — Final: olay hemen devam eder; aynı olay görsel espri ve tamamlanmış bir final kompozisyonuyla çözülür.",
    ]
    prompts=[]
    for i,action in enumerate(actions):
        prompts.append(
            f"{CHARACTER_ANCHOR} {STORY_BIBLE} EPISODE TITLE: {theme}. EXACT PLOT: {ep['premise']} "
            f"CONTINUITY: same physical location, same black cap and hoodie, same story object, sequential seconds/minutes. {action} "
            f'Tiny panel caption only: "{labels[i]}". The caption must help bridge this frame into the next like restrained manga narration. No speech balloons, no extra writing. '
            "IMPORTANT: the purple neon ring/crown/background from the identity reference is NOT part of MUBA and must NOT appear. "
            "Use the reference only for MUBA's face/body identity. Compose an actual narrative action panel, never a centered character portrait."
        )
    return {
        "day":day,"status":"published" if is_published(day) else "draft",
        "theme":theme,"theme_tr":theme_tr,"source_truth":truth,"source_truth_tr":truth_tr,
        "scenes":actions,"scenes_tr":actions_tr,"frame_labels":labels,"prompts":prompts,
        "story":ep["story"],"story_tr":ep["story_tr"],
        "summary":("A loose page leads MUBA through the street; when the paper finally stops, the wind steals the cap and the chase changes direction." if ep["title"]=="The Runaway Paper" else "A mysterious box answers MUBA's knock; curiosity opens the lid and the strange encounter ends with an unexpected little gift."),
        "summary_tr":("Kaçak bir kâğıt MUBA'yı sokakta peşinden sürükler; kâğıt sonunda durunca bu kez rüzgâr şapkayı kapar ve kovalamaca yön değiştirir." if ep["title"]=="The Runaway Paper" else "Gizemli bir kutu MUBA'nın vuruşuna karşılık verir; merak kapağı açtırır ve tuhaf karşılaşma beklenmedik küçük bir hediyeyle biter."),
        "twt":ep["story"],"twt_tr":ep["story_tr"],
        "images":image_ids(day),
        "rules":{"frames":4,"human_approval_required":True,"auto_publish":False,"character_anchor":"identity-only",
                 "visual_style":"modern-manga-light-digital","continuity":"previous-frame-image","frame_text_max_words":3,
                 "reference_excludes":["purple-neon-ring","crown","background"]},
    }

def set_images(day,image_ids):
    STORE.set("story_images",str(day),list(image_ids)[:4])
    return draft(day)

def image_ids(day):
    return list(STORE.get("story_images",str(day),[]) or [])[:4]

def is_published(day):
    return bool(STORE.get("story_publish",str(day),False))

def publish(day):
    if len(image_ids(day)) != 4:
        raise ValueError("Daily Story requires four approved images before publishing")
    STORE.set("story_publish",str(day),True)
    return draft(day)

def unpublish(day):
    STORE.set("story_publish",str(day),False)
    return draft(day)

def public_story(day=None):
    item=draft(day)
    return item if item["status"]=="published" and len(item.get("images",[]))==4 else None
