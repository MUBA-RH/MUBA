"""MUBA Daily Story Director.

Builds one four-scene visual story draft per Istanbul calendar day from the
canonical MUBA history. Drafting is deterministic and read-only. Publishing is
DEV-controlled and stores only approval state; image generation remains a
separate Studio operation so the production baseline is never auto-published.
"""
from __future__ import annotations
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from muba_brain import STORE
from muba_story_visual import story_identity_prompt, VISUAL_STYLE, REFERENCE_ROLE

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

def _previous_story_context(day):
    """Return yesterday's immutable published/draft story state as today's canon."""
    if not STORE.get("story_v3_origin_started","muba",False):
        return {"day":"origin","theme":"Before MUBA","story":"The story has not started yet.","ending":"MUBA has not yet entered the story world."}
    current=datetime.fromisoformat(str(day)).date()
    previous=(current-timedelta(days=1)).isoformat()
    saved=STORE.get("story_canon",previous,None)
    if isinstance(saved,dict) and saved.get("story"):
        return saved
    # Backfill deterministically so continuity survives deployments/restarts.
    ep=_episode_for_day(previous)
    return {"day":previous,"theme":ep["title"],"story":ep["story"],"ending":ep["actions"][-1]}

def _continuity_bridge(previous):
    return (
        "CONTINUITY FROM YESTERDAY: "+previous["ending"]+" "
        "Today's opening must visibly begin from this exact resolved state before a new event starts. "
        "Do not reset MUBA, teleport to an unrelated situation, or contradict yesterday's ending."
    )

def _summary_100(text):
    """Website summary: at most 100 Unicode characters, deterministic and readable."""
    clean=" ".join(str(text or "").split())
    if len(clean)<=100: return clean
    return clean[:97].rstrip(" ,.;:-")+"..."

def _episode_for_day(day):
    """Concrete deterministic episode seed; avoids vague 'something happened' plots."""
    options=[
        {
            "title":"I'm MUBA","title_tr":"Ben MUBA",
            "premise":"MUBA's first beginning: an ordinary quiet city street at early morning. No mysterious box, no cookie, no pre-built legend and no other mascot. MUBA simply appears in the world for the first time. Keep the same street and morning light across all four images.",
            "actions":[
                "Wide establishing shot: an ordinary nearly empty street at first light. MUBA enters the frame alone for the first time, small against the environment, looking around with open curiosity. Nothing magical happens; this is simply the beginning.",
                "Same street moments later: MUBA stops at a shop window and sees the reflection of the SAME MUBA. MUBA studies the reflection with a puzzled but amused expression. Preserve exact face, cap, hoodie and body identity.",
                "Immediate continuation on the SAME street: MUBA turns from the reflection and notices a few ordinary people farther down the street looking back with curiosity. MUBA gives a small casual wave. No crowd, hype or signs.",
                "Payoff in the SAME morning street: MUBA keeps walking forward with relaxed confidence while the street wakes up behind. MUBA is now simply part of the place. End on a lived-in beginning, not a grand reveal."
            ],
            "premise_tr":"MUBA'nın ilk başlangıcı: sabahın ilk ışıklarında sıradan ve sakin bir şehir sokağı. Gizemli kutu, kurabiye, önceden yazılmış efsane veya başka maskot yok. MUBA dünyada ilk kez yalnızca ortaya çıkar.",
            "labels":["","","",""],
            "story":"There was no grand entrance and no legend waiting to be told. One morning, MUBA simply appeared on an ordinary street. MUBA looked around, caught a reflection in a window, and kept walking. A few people noticed. A few looked twice. MUBA gave a small wave and carried on. Nothing had been announced, promised or explained. There was only a character, a street, and the first moment of a story that would be lived one day at a time.",
            "story_tr":"Büyük bir giriş yoktu; anlatılmayı bekleyen bir efsane de yoktu. Bir sabah MUBA sıradan bir sokakta öylece ortaya çıktı. Etrafına baktı, bir vitrinde yansımasını gördü ve yürümeye devam etti. Birkaç kişi fark etti. Bazıları dönüp bir daha baktı. MUBA küçük bir selam verdi ve yoluna devam etti. Hiçbir şey duyurulmamış, vaat edilmemiş veya açıklanmamıştı. Yalnızca bir karakter, bir sokak ve gün gün yaşanacak bir hikâyenin ilk anı vardı."
        },
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
    # Bootstrap the living story with MUBA's own emergence. Later days use the
    # existing story pool and yesterday's canon for continuity.
    if not STORE.get("story_v3_origin_started","muba",False):
        return options[0]
    return options[1 + (sum(ord(x) for x in str(day)) % (len(options)-1))]

def draft(day=None):
    day=day or datetime.now(TZ).date().isoformat()
    change=_public_change(day)
    truth=((change.get("text") or {}).get("en") if change else None) or "No public ecosystem development is required for this episode."
    truth_tr=((change.get("text") or {}).get("tr") if change else None) or "Bu bölüm için herkese açık bir ekosistem gelişmesi gerekmiyor."
    previous=_previous_story_context(day)
    ep=_episode_for_day(day)
    continuity=_continuity_bridge(previous)
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
        story_identity_prompt()+" EPISODE: "+theme+". STORY CONTEXT: "+continuity+" "+ep["premise"]+" CURRENT BEAT: "+action
        for action in actions
    ]
    if ep["title"]=="I'm MUBA":
        raw_summary="MUBA appears. Looks around. Sees a reflection. Waves. Keeps walking."
        raw_summary_tr="MUBA ortaya çıkar. Etrafına bakar. Yansımasını görür. Selam verir. Yürür."
    elif ep["title"]=="The Runaway Paper":
        raw_summary="A paper escapes. MUBA chases it. The paper stops. The cap flies away."
        raw_summary_tr="Bir kâğıt kaçar. MUBA peşine düşer. Kâğıt durur. Şapka uçar."
    else:
        raw_summary="MUBA finds a box. It knocks back. The lid opens. A small surprise appears."
        raw_summary_tr="MUBA bir kutu bulur. Kutu karşılık verir. Kapak açılır. Küçük bir sürpriz çıkar."
    reference=reference_for_day(day)
    item={
        "day":day,"status":"published" if is_published(day) else "draft",
        "theme":theme,"theme_tr":theme_tr,"source_truth":truth,"source_truth_tr":truth_tr,
        "scenes":actions,"scenes_tr":actions_tr,"frame_labels":labels,"prompts":prompts,
        "story":_summary_100(raw_summary),"story_tr":_summary_100(raw_summary_tr),
        "summary":_summary_100(raw_summary),
        "summary_tr":_summary_100(raw_summary_tr),
        "previous_day":previous["day"],"previous_theme":previous["theme"],
        "twt":_summary_100(raw_summary),"twt_tr":_summary_100(raw_summary_tr),
        "images":image_ids(day),
        "image_reference":_image_batch(day).get("reference"),
        "rules":{"frames":4,"human_approval_required":True,"auto_publish":False,"character_anchor":REFERENCE_ROLE,
                 "visual_style":VISUAL_STYLE,"continuity":"fresh-dev-reference-plus-scene-state","frame_text_max_words":0,
                 "visual_layer":"muba_story_visual","character_anchor_version":"daily-story-reference-first-v3","reference_sha256":(reference or {}).get("sha256"),
                 "aspect_ratio":"16:9","reference_excludes":["purple-neon-ring","crown","background","example-props","fixed-pose"]},
    }
    STORE.set("story_canon",str(day),{"day":day,"theme":theme,"story":ep["story"],"ending":actions[-1],"digest":hashlib.sha256(ep["story"].encode()).hexdigest()[:16]})
    if ep["title"]=="I'm MUBA":
        STORE.set("story_v3_origin_started","muba",True)
    return item

def set_reference(day,gallery_id,sha256,content_type,fingerprint=None):
    """Bind a fresh DEV-uploaded reference to one production day."""
    if is_published(day):
        raise ValueError("Published Daily Story reference cannot be replaced")
    metadata={"version":"daily-story-master-fingerprint-v4","role":REFERENCE_ROLE,"style":VISUAL_STYLE,
              "gallery_id":str(gallery_id),"sha256":str(sha256),"content_type":str(content_type)}
    if isinstance(fingerprint,dict): metadata["fingerprint"]=dict(fingerprint)
    STORE.set("story_v3_reference",str(day),metadata)
    STORE.set("story_image_batches",str(day),{})
    return metadata

def reference_for_day(day):
    value=STORE.get("story_v3_reference",str(day),None)
    return dict(value) if isinstance(value,dict) and value.get("gallery_id") and value.get("sha256") else None

def clear_reference(day):
    STORE.set("story_v3_reference",str(day),{})
    return True

def set_images(day,image_ids):
    if is_published(day):
        raise ValueError("Published Daily Story images cannot be replaced")
    # One state write binds images to their reference; a partial metadata write
    # must never relabel an older batch as the newly approved character.
    reference=reference_for_day(day)
    if not reference:
        raise ValueError("Fresh DEV reference required before Daily Story generation")
    STORE.set("story_image_batches",str(day),{"ids":list(image_ids)[:4],"reference":reference})
    return draft(day)

def _image_batch(day):
    batch=STORE.get("story_image_batches",str(day),{})
    return batch if isinstance(batch,dict) else {}

def image_ids(day):
    # Keep published history intact. Unapproved old-style batches need a fresh
    # review; never silently mark the old portrait output as the new style.
    batch=_image_batch(day)
    if not is_published(day) and batch.get("reference")!=reference_for_day(day):
        return []
    ids=batch.get("ids",[]) if batch else STORE.get("story_images",str(day),[])
    return list(ids or [])[:4]

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
