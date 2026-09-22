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
from muba_story_chibi import panel_prompt

TZ=ZoneInfo("Europe/Istanbul")
HISTORY_PATH=Path(__file__).resolve().parents[1]/"muba_history.json"

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
            "premise":"A quiet narrow old-city alley in warm morning daylight: faded green shop door, stone pavement, one clay flowerpot, and one small weathered wooden box beside the door. Keep these exact landmarks in every panel.",
            "actions":[
                "Wide establishing shot: MUBA walks into the alley, notices the closed wooden box beside the faded green door, stops two steps away and leans forward curiously. The box is still.",
                "Same alley seconds later: MUBA crouches beside the SAME box and taps its lid once. The lid visibly bumps upward from a knock inside; MUBA jerks backward in surprise.",
                "Immediate continuation: the SAME box lid flips half open and a tiny brass wind-up bird springs out carrying one large round biscuit in its beak. MUBA falls backward onto the stone pavement. Keep the green door and flowerpot.",
                "Payoff in the SAME alley: MUBA sits beside the open box and breaks the biscuit in half. The tiny brass bird perches on the box edge and receives one half. Calm warm daylight, resolved ending."
            ],
            "premise_tr":"Eski şehirde dar bir sokakta MUBA, kapalı bir dükkânın yanında küçük ve yıpranmış ahşap bir kutu bulur. Kapağı tıklatınca içeriden aynı şekilde karşılık gelir.",
            "labels":["KNOCK.","KNOCK?","OH.","YOURS."],
            "story":"At the end of a quiet alley, MUBA noticed a battered wooden box that definitely had not been there a moment ago. One cautious knock on the lid came back from inside. Naturally, MUBA knocked again. The box jumped, the lid cracked open, and a tiny wind-up bird burst out carrying a biscuit almost as large as itself. It dropped the biscuit at MUBA's feet, folded its metal wings and disappeared back into the box. MUBA stared at the unexpected delivery for a second, then sat beside the box and shared the biscuit with whoever—or whatever—was still knocking from inside.",
            "story_tr":"Sessiz bir sokağın sonunda MUBA, az önce orada olmadığına emin olduğu eski bir ahşap kutu fark etti. Kapağa temkinli bir kez vurdu; içeriden aynı vuruşla cevap geldi. Elbette MUBA bir kez daha vurdu. Kutu sıçradı, kapak aralandı ve içinden neredeyse kendisi kadar büyük bir bisküvi taşıyan minik kurmalı bir kuş çıktı. Bisküviyi MUBA'nın ayaklarının önüne bıraktı, metal kanatlarını kapattı ve tekrar kutunun içine kayboldu. MUBA beklenmedik teslimata bir an baktı, sonra kutunun yanına oturup bisküviyi içeride hâlâ tıklatan her kimse—ya da her neyse—onunla paylaştı."
        },
        {
            "title":"The Runaway Paper","title_tr":"Kaçak Kâğıt",
            "premise":"A bright breezy neighborhood street in daytime: one wooden bench on the left, one shallow puddle near the curb, a pale yellow wall at the far end, and one folded white paper. Keep these exact landmarks in every panel.",
            "actions":[
                "Wide establishing shot: the folded white paper lifts from the bench and skates across the pavement in front of walking MUBA. MUBA turns toward it; bench, puddle and yellow wall are visible.",
                "Same street moments later: MUBA runs full-body after the SAME folded paper as wind pushes it just beyond reach. MUBA splashes through the SAME puddle; the bench is behind.",
                "Same chase at the pale yellow wall: the paper lands at the base of the wall. MUBA dives and pins it with both tiny hands, cap crooked, exhausted but triumphant.",
                "Immediate payoff at the SAME wall: MUBA opens the caught paper and it is completely blank; a gust lifts MUBA's black cap into the air behind. MUBA twists around reaching for the flying cap while the blank paper stays under one hand."
            ],
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
    actions=ep["actions"]
    actions_tr=[
        "Kare 1 — Kurulum: geniş planda MUBA'nın hikâyedeki somut nesneyi belirtilen mekânda bulduğu an gösterilir.",
        "Kare 2 — Eylem: birkaç saniye sonrası; MUBA aynı nesneyle fiziksel olarak etkileşir ve ilk sonuç ortaya çıkar.",
        "Kare 3 — Dönüm: ikinci karenin sonucu devam eder; hikâyedeki somut sürpriz açığa çıkar ve MUBA belirgin tepki verir.",
        "Kare 4 — Final: olay hemen devam eder; aynı olay görsel espri ve tamamlanmış bir final kompozisyonuyla çözülür.",
    ]
    prompts=[
        panel_prompt(theme,ep["premise"],action)
        for action in actions
    ]
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
                 "visual_style":"living-story-true-2d-chibi-cloudflare-flux-v1","continuity":"canonical-face-architecture-plus-canonical-reference-plus-scene-state","frame_text_max_words":0,
                 "visual_layer":"muba_story_chibi","character_anchor_version":"muba-face-architecture-v1","reference_excludes":["purple-neon-ring","crown","background"]},
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