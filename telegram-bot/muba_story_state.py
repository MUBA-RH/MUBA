"""Durable private state for Daily Story only, using the existing R2 archive."""
from __future__ import annotations

import copy
import json
import threading

from muba_gallery import _r2_enabled, _r2_request


class StoryState:
    def __init__(self, fallback):
        self.fallback = fallback
        self._cache = {}
        self._lock = threading.RLock()

    @staticmethod
    def _key(namespace, key):
        if not namespace.startswith("story_"):
            raise ValueError("Daily Story state cannot access another namespace")
        if not str(key) or "/" in str(key) or ".." in str(key):
            raise ValueError("Invalid Daily Story state key")
        return f"daily-story/state/{namespace}/{key}.json"

    def get(self, namespace, key, default=None):
        if not _r2_enabled():
            return self.fallback.get(namespace, key, default)
        path = self._key(namespace, key)
        with self._lock:
            if path not in self._cache:
                response = _r2_request("GET", path, allow_missing=True)
                self._cache[path] = (json.loads(response.content)["value"] if response else
                                     self.fallback.get(namespace, key, None))
            value = self._cache[path]
            return copy.deepcopy(default if value is None else value)

    def set(self, namespace, key, value):
        if not _r2_enabled():
            return self.fallback.set(namespace, key, value)
        path = self._key(namespace, key)
        payload = json.dumps({"value": value}, ensure_ascii=False).encode("utf-8")
        with self._lock:
            _r2_request("PUT", path, body=payload, content_type="application/json")
            self._cache[path] = copy.deepcopy(value)
            self.fallback.set(namespace, key, value)
