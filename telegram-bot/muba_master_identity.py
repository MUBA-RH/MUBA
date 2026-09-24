"""Canonical MUBA identity lock for Daily Story."""
from __future__ import annotations
import json
from pathlib import Path
from muba_story_fingerprint import build as build_fingerprint

_PROFILE=json.loads((Path(__file__).with_name("muba_master_identity.json")).read_text(encoding="utf-8"))

def profile()->dict:
    return dict(_PROFILE)

def reference_state(reference_bytes:bytes)->dict:
    fp=build_fingerprint(reference_bytes)
    return {"master":profile(),"incoming":fp,"is_exact_master":fp["source_sha256"]==_PROFILE["source_sha256"]}

def identity_prompt()->str:
    boxes=_PROFILE["landmarks_norm"]
    rules="; ".join(_PROFILE["identity_rules"])
    body=_PROFILE.get("body_master",{})
    return (
      "MASTER MUBA IDENTITY LOCK. Preserve these immutable identity traits: "+rules+". "
      "Canonical normalized geometry anchors from the master portrait: "
      +"; ".join(f"{k}={v}" for k,v in boxes.items())+". "
      "The daily reference may change pose, camera, environment and lighting, but must not redefine MUBA identity. "
      "BODY LOCK: "+json.dumps(body,sort_keys=True)+". "
      "Frame the character as a complete full-body subject from cap to bare feet whenever the scene permits; do not crop into a face-only portrait. "
      "When the daily reference conflicts with the master identity, the master identity wins."
    )
