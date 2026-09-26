"""Daily Story: one connected 150–170 character episode and one 16:9 scene."""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from muba_brain import STORE
from muba_story_visual import REFERENCE_ROLE, VISUAL_STYLE, story_identity_prompt

TZ = ZoneInfo("Europe/Istanbul")
START = date(2026, 9, 26)
SCENE_REFERENCE = Path(__file__).with_name("assets") / "muba_daily_story_scene_reference.jpg"

# Each beat begins with the outcome of the preceding beat. The last beat leads
# back into the first as another ordinary day in the same living neighborhood.
BEATS = (
    ("A New Street", "Yeni Bir Sokak",
     "MUBA follows a handwritten arrow from the square into a quiet side street. At its end, a tiny open door reveals a secret garden nobody had noticed before.",
     "MUBA meydandaki el çizimi oku izleyip sakin bir sokağa girer. Sokağın sonunda aralık bir kapı, kimsenin daha önce fark etmediği küçük bir bahçeye açılır.",
     "sunlit side street, small open garden door, MUBA following a handwritten arrow"),
    ("The Garden", "Bahçe",
     "Beyond yesterday's door, MUBA finds a neglected garden and a watering can. One curious neighbor joins in; together they bring the first drooping flower back to life.",
     "Dünkü kapının ardında MUBA bakımsız bir bahçe ve bir sulama kabı bulur. Meraklı bir komşu yanına gelir; birlikte solgun bir çiçeği yeniden canlandırırlar.",
     "warm neighborhood garden, watering can, MUBA and a neighbor tending one flower"),
    ("A Small Invitation", "Küçük Bir Davet",
     "The revived flower draws more neighbors into the garden. MUBA leaves an invitation by the gate, and someone returns with seeds and a wonderfully crooked little sign.",
     "Canlanan çiçek bahçeye başka komşuları da çeker. MUBA kapıya küçük bir davet bırakır; biri tohumlarla ve eğri büğrü, sevimli bir tabelayla geri döner.",
     "garden gate, simple invitation, seeds and crooked handmade sign, MUBA welcoming neighbors"),
    ("A Shared Corner", "Ortak Köşe",
     "After the seeds arrive, MUBA helps turn an empty corner into a place to sit. A passing stranger stops to laugh at the crooked sign and stays to share a story.",
     "Tohumlar geldikten sonra MUBA boş bir köşeyi oturulacak bir yere dönüştürür. Yoldan geçen biri eğri tabelaya güler, sonra kalıp kendi hikâyesini anlatır.",
     "cozy garden corner, handmade bench and crooked sign, MUBA listening to a visitor"),
    ("The First Drawing", "İlk Çizim",
     "The visitor's story gives MUBA an idea. They draw a small scene together and pin it beside the garden gate; by evening, another drawing has appeared next to theirs.",
     "Misafirin hikâyesi MUBA'ya yeni bir fikir verir. Birlikte küçük bir sahne çizip bahçe kapısına asarlar; akşama doğru yanına başka bir çizim daha eklenmiştir.",
     "garden gate with two handmade drawings, MUBA pinning up a new picture, gentle evening light"),
    ("More Stories", "Yeni Hikâyeler",
     "Seeing the second drawing, MUBA puts out blank paper for anyone who passes. Soon the gate fills with funny little scenes, and every picture has its own voice.",
     "İkinci çizimi gören MUBA, yoldan geçenler için boş kâğıtlar bırakır. Bahçe kapısı kısa sürede komik sahnelerle dolar; her resim kendi hikâyesini anlatır.",
     "bright garden gate covered in playful drawings, blank paper nearby, MUBA looking at community art"),
    ("An Open Path", "Açık Bir Yol",
     "With the garden gate full of stories, MUBA spots a new handwritten arrow pointing toward the square. They follow it, carrying a fresh idea into the next day.",
     "Bahçe kapısı hikâyelerle dolunca MUBA meydana uzanan yeni bir el çizimi ok görür. Yeni ve güzel bir fikri de yanında taşıyarak okun gösterdiği yolu izler.",
     "sunny path from the garden toward the square, handwritten arrow, MUBA walking with a new idea"),
)


def _episode(day):
    step = (date.fromisoformat(day) - START).days
    if step >= len(BEATS):
        saved = STORE.get("story_text", day, None)
        if not isinstance(saved, dict) or not saved.get("scene"):
            saved = STORE.get("story_canon", day, None)
        if not isinstance(saved, dict) or not saved.get("scene"):
            raise RuntimeError("Daily Story text is awaiting a new connected episode")
        return saved
    title, title_tr, story, story_tr, scene = BEATS[step % len(BEATS)]
    return {"title": title, "title_tr": title_tr, "story": story,
            "story_tr": story_tr, "scene": scene, "step": step}


def _length_checked(text):
    text = " ".join(text.split())
    if not 150 <= len(text) <= 170:
        raise ValueError(f"Daily Story must have 150–170 characters: {len(text)}")
    return text


def _previous_state(day):
    previous_date = date.fromisoformat(day) - timedelta(days=1)
    for gap in range(31):
        previous = (previous_date - timedelta(days=gap)).isoformat()
        saved = STORE.get("story_canon", previous, None) or STORE.get("story_text", previous, None)
        if isinstance(saved, dict) and saved.get("story"):
            return {"day": previous, "story": saved["story"],
                    "theme": saved.get("theme") or saved.get("title", "MUBA Daily Story")}
        if previous_date - timedelta(days=gap) <= START + timedelta(days=len(BEATS)-1):
            ep = _episode(previous)
            return {"day": previous, "story": ep["story"], "theme": ep["title"]}
    raise RuntimeError("Daily Story needs a prior approved episode to continue")


def draft(day=None):
    day = day or datetime.now(TZ).date().isoformat()
    ep = _episode(day)
    previous = _previous_state(day)
    reference = reference_for_day(day)
    archived = STORE.get("story_canon", day, None) if is_published(day) else None
    archived = archived if isinstance(archived, dict) else {}
    story = archived.get("story") or _length_checked(ep["story"])
    story_tr = archived.get("story_tr") or _length_checked(ep["story_tr"])
    prompt = (story_identity_prompt() + " CURRENT BEAT: " + ep["scene"] + ". "
              "Illustrate the meaningful moment of TODAY'S STORY: " + story + " "
              "One bright, airy, full-bleed 16:9 scene. No panels, collage, captions or oppressive dark atmosphere. "
              "Character identity comes from the master; the approved scene image guides warmth and composition, "
              "but its square and wall are not required. Do not copy a previous generated image.")
    images = image_ids(day)
    return {"day": day, "status": "published" if is_published(day) else "draft",
            "theme": ep["title"], "theme_tr": ep["title_tr"],
            "story": story, "story_tr": story_tr, "summary": story,
            "summary_tr": story_tr, "twt": story, "twt_tr": story_tr,
            "previous_day": previous["day"], "previous_theme": previous["theme"],
            "story_state": {"previous_story": previous["story"], "step": ep["step"]},
            "prompts": [prompt], "images": images, "image_ids": images,
            "image_reference": _image_batch(day).get("reference"),
            "rules": {"frames": 1, "story_characters": [150, 170], "aspect_ratio": "16:9",
                      "human_approval_required": True, "auto_publish": False,
                      "character_anchor": REFERENCE_ROLE, "visual_style": VISUAL_STYLE,
                      "reference_sha256": (reference or {}).get("sha256"),
                      "continuity": "text-story-state-only", "delivery": "one-scene"}}


def save_episode(day, episode):
    """Freeze validated daily text before rendering its image."""
    if is_published(day):
        raise ValueError("Published Daily Story text cannot be replaced")
    previous = _previous_state(day)
    story = _length_checked(episode["story"])
    story_tr = _length_checked(episode["story_tr"])
    forbidden = ("robinhood", "flap", "uniswap", "binance", "listing", "price prediction")
    if any(word in (story + " " + story_tr).casefold() for word in forbidden):
        raise ValueError("Daily Story includes an unrelated brand or promise")
    if story == previous["story"] or story in (beat[2] for beat in BEATS) or len(episode["scene"].strip()) < 15:
        raise ValueError("Daily Story must advance the prior scene")
    item = {"title": episode["title"].strip(), "title_tr": episode["title_tr"].strip(),
            "story": story, "story_tr": story_tr, "scene": episode["scene"].strip(),
            "step": (date.fromisoformat(day) - START).days}
    if not item["title"] or not item["title_tr"]:
        raise ValueError("Daily Story needs a title in both languages")
    STORE.set("story_text", day, item)
    return draft(day)


def worker_job(day=None, reference_path="muba-reference.jpg"):
    item = draft(day)
    reference = reference_for_day(item["day"])
    if not reference:
        raise ValueError("Daily Story reference required before worker job creation")
    return {"schema_version": 2, "job_id": "muba-daily-story-" + item["day"],
            "day": item["day"], "reference_path": str(reference_path),
            "reference_sha256": reference["sha256"], "story_state": item["story_state"],
            "seed": int(hashlib.sha256(item["day"].encode()).hexdigest()[:8], 16),
            "chapters": [{"index": 1, "title": item["theme"], "prompt": item["prompts"][0]}],
            "rules": {"images": 1, "aspect_ratio": "16:9", "previous_frame_conditioning": False,
                      "approval": "telegram-dev"}}


def reference_for_day(day):
    value = STORE.get("story_v3_reference", str(day), None)
    if isinstance(value, dict) and value.get("gallery_id") and value.get("sha256"):
        return dict(value)
    if SCENE_REFERENCE.is_file():
        return {"role": REFERENCE_ROLE, "gallery_id": "daily-story-bundled-scene",
                "sha256": hashlib.sha256(SCENE_REFERENCE.read_bytes()).hexdigest(),
                "content_type": "image/jpeg", "file": str(SCENE_REFERENCE)}
    return None


def set_reference(day, gallery_id, sha256, content_type, fingerprint=None):
    if is_published(day):
        raise ValueError("Published Daily Story reference cannot be replaced")
    metadata = {"role": REFERENCE_ROLE, "style": VISUAL_STYLE, "gallery_id": str(gallery_id),
                "sha256": str(sha256), "content_type": str(content_type)}
    if isinstance(fingerprint, dict):
        metadata["fingerprint"] = dict(fingerprint)
    STORE.set("story_v3_reference", str(day), metadata)
    STORE.set("story_image_batches", str(day), {})
    return metadata


def clear_reference(day):
    STORE.set("story_v3_reference", str(day), {})
    return True


def _image_batch(day):
    batch = STORE.get("story_image_batches", str(day), {})
    return batch if isinstance(batch, dict) else {}


def image_ids(day):
    batch = _image_batch(day)
    if is_published(day):
        ids = batch.get("ids", []) if batch else STORE.get("story_images", str(day), [])
        return list(ids or [])[:4]  # preserve already published four-image history
    if not is_published(day) and batch.get("reference") != reference_for_day(day):
        return []
    ids = batch.get("ids", []) if batch else STORE.get("story_images", str(day), [])
    return list(ids or [])[:1]


def set_images(day, image_ids):
    if is_published(day):
        raise ValueError("Published Daily Story images cannot be replaced")
    reference = reference_for_day(day)
    if not reference or len(image_ids) != 1:
        raise ValueError("Daily Story requires one image bound to its reference")
    STORE.set("story_image_batches", str(day), {"ids": list(image_ids), "reference": reference})
    return draft(day)


def is_published(day):
    return bool(STORE.get("story_publish", str(day), False))


def publish(day):
    if len(image_ids(day)) != 1:
        raise ValueError("Daily Story requires one approved image before publishing")
    item = draft(day)
    STORE.set("story_canon", str(day), {"day": day, "theme": item["theme"],
                                         "title": item["theme"], "title_tr": item["theme_tr"],
                                         "scene": _episode(day)["scene"], "step": _episode(day)["step"],
                                         "story": item["story"], "story_tr": item["story_tr"]})
    STORE.set("story_publish", str(day), True)
    return draft(day)


def unpublish(day):
    STORE.set("story_publish", str(day), False)
    return draft(day)


def public_story(day=None):
    day = day or datetime.now(TZ).date().isoformat()
    if not is_published(day):
        return None
    item = draft(day)
    return item if item["status"] == "published" and len(item["images"]) in (1, 4) else None
