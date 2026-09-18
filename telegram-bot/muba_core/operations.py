"""Observable, reversible operational helpers for the protected brain."""
from __future__ import annotations

import copy
import time
import uuid

PROTECTED = (
    "core_identity", "official_knowledge", "official_sources", "authority",
    "permanent_security", "ca",
)


def specification(version: str, layer_names) -> dict:
    return {
        "version": version,
        "architecture": "protected core/router/decision engine with specialist layers",
        "specialist_layers": list(layer_names),
        "protected_scopes": list(PROTECTED),
        "supported_languages": ["en", "tr", "zh", "ar", "hi"],
        "official_sources": ["@MUBA_RH", "https://muba-rh.github.io/MUBA/"],
        "external_generative_ai": False,
    }


def health(repository, version: str, layer_names) -> dict:
    spec = specification(version, layer_names)
    return {
        "ok": len(spec["specialist_layers"]) == 23,
        "version": version,
        "layer_count": len(spec["specialist_layers"]),
        "protected_scopes": len(PROTECTED),
        "external_generative_ai": False,
        "checked_at": time.time(),
    }


def observe(repository, message, decision) -> str:
    event_id = uuid.uuid4().hex
    repository.append("observations", str(message.chat_id), {
        "id": event_id, "chat_id": message.chat_id, "user_id": message.user_id,
        "language": decision.language, "intents": list(decision.intents),
        "action": decision.action.value, "at": time.time(),
    }, 500)
    return event_id


def audit(repository, category: str, actor_id=None, chat_id=0, evidence=None) -> str:
    audit_id = uuid.uuid4().hex
    repository.set("audit", audit_id, {
        "id": audit_id, "category": category, "actor_id": actor_id,
        "chat_id": int(chat_id or 0), "evidence": copy.deepcopy(evidence),
        "at": time.time(),
    })
    return audit_id


def remember_decision(repository, chat_id, decision, provenance="decision_engine") -> str:
    decision_id = uuid.uuid4().hex
    repository.append("decision_memory", str(chat_id), {
        "id": decision_id, "action": decision.action.value,
        "intents": list(decision.intents), "winner": decision.trace.winning_rule,
        "confidence": decision.trace.confidence, "provenance": provenance,
        "at": time.time(),
    }, 500)
    return decision_id


def close_incident(repository, incident_id: str, actor_id: int, resolution: str) -> bool:
    item = repository.get("incidents", incident_id)
    if not item or actor_id != 934598759:
        return False
    item.update({"status": "closed", "resolution": resolution,
                 "closed_by": actor_id, "closed_at": time.time()})
    repository.set("incidents", incident_id, item)
    return True


def snapshot(repository) -> dict:
    # Repository snapshots are copies and never expose implementation locks.
    data = getattr(repository, "_data", {})
    return {"schema": 1, "created_at": time.time(), "state": copy.deepcopy(data)}
