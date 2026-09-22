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
    "MUBA into a generic cute animal. Art direction: premium comic-book x anime hybrid, expressive hand-drawn linework, "
    "cinematic anime lighting, textured painted backgrounds, dynamic panel composition, never glossy 3D CGI. "
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

def draft(day=None):
    day=day or datetime.now(TZ).date().isoformat()
    change=_public_change(day)

    # Product/maintenance changelog is context, never the literal plot. A real
    # development may inspire the episode only when it can be expressed naturally.
    if change:
        truth=(change.get("text") or {}).get("en") or "A real MUBA ecosystem change happened today."
        truth_tr=(change.get("text") or {}).get("tr") or truth
        seed="Something in MUBA's familiar world works differently today, and MUBA discovers it through a small everyday adventure."
        seed_tr="MUBA'nın tanıdık dünyasında bugün bir şey farklı işler; MUBA bunu küçük, günlük bir macera içinde keşfeder."
    else:
        truth="No public ecosystem development is required for this episode."
        truth_tr="Bu bölüm için herkese açık bir ekosistem gelişmesi gerekmiyor."
        seed="A quiet ordinary moment turns into a strange little adventure when MUBA notices something unexpected nearby."
        seed_tr="Sıradan ve sakin bir an, MUBA yakındaki beklenmedik bir şeyi fark edince küçük ve tuhaf bir maceraya dönüşür."

    theme="A four-panel MUBA mini-episode: "+seed
    theme_tr="Dört karelik bir MUBA mini bölümü: "+seed_tr
    labels=["WAIT...","WHAT?","MUBA.","AGAIN?"]
    scenes=[
        "FRAME 1 — OPENING. Wide establishing shot. MUBA enters or occupies the setting and notices one specific unusual object or event. Create a clear visual question that demands a next frame.",
        "FRAME 2 — ACTION. Continue from FRAME 1 in the exact same setting. MUBA approaches, touches, follows or tests the same object/event. Show physical action and consequence; do not reset the scene.",
        "FRAME 3 — TURN. Continue the consequence from FRAME 2. Give MUBA a strong, funny, unmistakable reaction and reveal the small twist. Preserve every continuity detail from earlier frames.",
        "FRAME 4 — PAYOFF. Continue immediately from FRAME 3 and resolve the event with a memorable visual joke or character beat. The final image must feel like the ending of the same episode, not a new portrait.",
    ]
    scenes_tr=[
        "Kare 1 — Açılış: geniş planla mekân kurulur. MUBA belirli ve sıra dışı bir nesne ya da olayı fark eder; sonraki kareyi merak ettiren görsel soru oluşur.",
        "Kare 2 — Hareket: aynı mekânda ilk karenin doğrudan devamıdır. MUBA aynı nesne/olaya yaklaşır, dokunur, takip eder veya dener; eylemin sonucu görünür.",
        "Kare 3 — Dönüm: ikinci karenin sonucu devam eder. Küçük sürpriz açığa çıkar ve MUBA güçlü, komik, kendine özgü bir tepki verir; tüm devamlılık korunur.",
        "Kare 4 — Final: üçüncü karenin hemen devamında olay akılda kalıcı bir görsel şaka veya karakter anıyla çözülür; yeni bir portre değil aynı bölümün finalidir.",
    ]
    prompts=[]
    continuity="CONTINUITY LOCK: same setting, same wardrobe, same recurring object/event and sequential cause-and-effect from the previous frame."
    for i,scene in enumerate(scenes):
        prompts.append(
            f"{CHARACTER_ANCHOR} {STORY_BIBLE} EPISODE PREMISE: {seed} {continuity} {scene} "
            f'Allow exactly one tiny narrative caption reading "{labels[i]}" integrated like restrained comic lettering. '
            "No other words, speech bubbles, logos, watermarks or extra captions."
        )
    story=(
        "MUBA expected an ordinary day. Then one small detail in the familiar surroundings refused to behave normally. "
        "Curiosity won, as it usually does. One closer look became an experiment, the experiment became a problem, "
        "and the problem became exactly the kind of moment MUBA somehow turns into a story. By the final frame, "
        "nothing world-changing has happened—just one strange little episode that now belongs to MUBA's living world."
    )
    story_tr=(
        "MUBA sıradan bir gün bekliyordu. Sonra tanıdık çevredeki küçücük bir ayrıntı normal davranmamaya başladı. "
        "Merak yine ağır bastı. Yakından bakmak küçük bir denemeye, deneme bir probleme, problem de MUBA'nın bir şekilde "
        "hikâyeye dönüştürdüğü o tuhaf anlardan birine dönüştü. Son karede dünyayı değiştiren bir şey olmadı; yalnızca "
        "MUBA'nın yaşayan dünyasına eklenen küçük ve garip bir bölüm daha ortaya çıktı."
    )
    return {
        "day":day,"status":"published" if is_published(day) else "draft",
        "theme":theme,"theme_tr":theme_tr,"source_truth":truth,"source_truth_tr":truth_tr,
        "scenes":scenes,"scenes_tr":scenes_tr,"frame_labels":labels,"prompts":prompts,
        "story":story,"story_tr":story_tr,"twt":story,"twt_tr":story_tr,
        "images":image_ids(day),
        "rules":{"frames":4,"human_approval_required":True,"auto_publish":False,"character_anchor":"reference-image",
                 "visual_style":"comic-anime-hybrid","continuity":"locked-sequential","frame_text_max_words":3},
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
