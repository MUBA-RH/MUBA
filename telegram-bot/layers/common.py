"""Small layer primitives. Layers never import one another."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from muba_core.contracts import Message, Signal


Matcher = Callable[[Message, Mapping[str, Any]], Optional[Signal]]


@dataclass
class SpecialistLayer:
    name: str
    priority: int
    matcher: Matcher

    def evaluate(self, message: Message, context: Mapping[str, Any]) -> Optional[Signal]:
        return self.matcher(message, context)


def signal(layer: str, intent: str, confidence: float, reason: str, **data: Any) -> Signal:
    return Signal(layer=layer, intent=intent, confidence=confidence, reason=reason, data=data)
