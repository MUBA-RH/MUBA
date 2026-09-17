"""Replaceable state repositories; production defaults to safe in-memory state."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any


class MemoryRepository:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        with self._lock:
            return copy.deepcopy(self._data.get(namespace, {}).get(key, default))

    def set(self, namespace: str, key: str, value: Any) -> None:
        with self._lock:
            self._data.setdefault(namespace, {})[key] = copy.deepcopy(value)

    def append(self, namespace: str, key: str, value: Any, limit: int = 100) -> None:
        with self._lock:
            values = self._data.setdefault(namespace, {}).setdefault(key, [])
            values.append(copy.deepcopy(value))
            del values[:-limit]


class JSONRepository(MemoryRepository):
    """Portable backend. Render's ephemeral disk is not durable storage."""

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = Path(path)
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._data = {}

    def set(self, namespace: str, key: str, value: Any) -> None:
        super().set(namespace, key, value)
        self._flush()

    def append(self, namespace: str, key: str, value: Any, limit: int = 100) -> None:
        super().append(namespace, key, value, limit)
        self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=".muba-", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(self._data, stream, ensure_ascii=False, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
