"""Typed contracts shared by the MUBA core and isolated specialist layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Sequence


class Action(str, Enum):
    SILENT = "SILENT"
    DIRECT_REPLY = "DIRECT_REPLY"
    PROACTIVE_JOIN = "PROACTIVE_JOIN"
    DAILY_GREETING = "DAILY_GREETING"
    CONFLICT_SUPPORT = "CONFLICT_SUPPORT"
    PROTECTED_COMMAND = "PROTECTED_COMMAND"


@dataclass(frozen=True)
class Message:
    text: str
    chat_id: int = 0
    user_id: Optional[int] = None
    language: Optional[str] = None
    reply_to_user_id: Optional[int] = None
    is_forwarded: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Signal:
    layer: str
    intent: str
    confidence: float
    reason: str
    data: Mapping[str, Any] = field(default_factory=dict)
    suppresses: Sequence[str] = field(default_factory=tuple)


@dataclass
class DecisionTrace:
    activated_layers: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    suppressed: list[str] = field(default_factory=list)
    winning_rule: str = ""
    confidence: float = 0.0
    state_changed: bool = False


@dataclass
class Decision:
    action: Action
    response: str = ""
    language: str = "en"
    intents: list[str] = field(default_factory=list)
    trace: DecisionTrace = field(default_factory=DecisionTrace)


class StateRepository(Protocol):
    def get(self, namespace: str, key: str, default: Any = None) -> Any: ...
    def set(self, namespace: str, key: str, value: Any) -> None: ...
    def append(self, namespace: str, key: str, value: Any, limit: int = 100) -> None: ...


class Layer(Protocol):
    name: str
    priority: int
    def evaluate(self, message: Message, context: Mapping[str, Any]) -> Optional[Signal]: ...
