"""Read and write dated Daily Story drafts in a separate private GitHub repository.

The main MUBA repository is public. A draft image must never be committed there.
The story and image are written together logically: scene first, manifest last.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import date, datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from muba_story_visual import normalize_ready_image


def configured():
    return bool(os.getenv("MUBA_STORY_GITHUB_REPO") and os.getenv("MUBA_STORY_GITHUB_TOKEN"))


def _settings():
    repo = os.getenv("MUBA_STORY_GITHUB_REPO", "").strip()
    token = os.getenv("MUBA_STORY_GITHUB_TOKEN", "").strip()
    branch = os.getenv("MUBA_STORY_GITHUB_BRANCH", "main").strip()
    if not repo or not token or len(repo.split("/")) != 2 or not branch:
        raise RuntimeError("Private Daily Story GitHub repository/token/branch is not configured")
    if repo.lower() == "muba-rh/muba":
        raise RuntimeError("Daily Story drafts must not enter the public MUBA repository")
    return repo, token, branch


def _api(path, method="GET", body=None):
    repo, token, _ = _settings()
    url = "https://api.github.com/repos/" + quote(repo, safe="/") + path
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, headers=headers, method=method, data=body)
    try:
        with urlopen(request, timeout=25) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 404 and method == "GET":
            return None
        # Keep the failing route visible without ever logging the token or URL query.
        raise RuntimeError(f"Daily Story GitHub {method} {path.split('?', 1)[0]} failed ({exc.code})") from exc


def _private():
    result = _api("")
    if not result or result.get("private") is not True:
        raise RuntimeError("Daily Story GitHub storage must be a private repository")


def _path(day, filename, test=False):
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError("Invalid Daily Story date")
    if filename not in ("story.json", "scene.png"):
        raise ValueError("Invalid Daily Story file")
    root = "tests/" + day + "-01" if test else "days/" + day
    return "/contents/daily-story/" + root + "/" + filename


def _get(day, filename, test=False):
    _, _, branch = _settings()
    result = _api(_path(day, filename, test) + "?ref=" + quote(branch, safe=""))
    if result is None:
        return None, None
    # GitHub omits inline content for files larger than 1 MB. The Git blob
    # endpoint still returns their base64 bytes using the same read-only token.
    if result.get("encoding") == "none" or not result.get("content"):
        sha = result.get("sha", "")
        if not sha or not all(char in "0123456789abcdef" for char in sha.lower()):
            raise RuntimeError("Daily Story GitHub file has no valid blob SHA")
        blob = _api("/git/blobs/" + sha)
        if not blob or blob.get("encoding") != "base64" or not blob.get("content"):
            raise RuntimeError("Daily Story GitHub blob content is unavailable")
        return base64.b64decode(blob["content"]), sha
    return base64.b64decode(result["content"]), result["sha"]


def read_day(day):
    """Return a complete private draft, or None; reject torn/corrupt records."""
    _private()
    raw, _ = _get(day, "story.json")
    if raw is None:
        return None
    item = json.loads(raw)
    if item.get("day") != day or item.get("version") != 1:
        raise RuntimeError("Daily Story GitHub manifest date/version mismatch")
    image, _ = _get(day, "scene.png")
    if image is None or hashlib.sha256(image).hexdigest() != item.get("image_sha256"):
        raise RuntimeError("Daily Story GitHub image is missing or changed")
    if normalize_ready_image(image) != image:
        raise RuntimeError("Daily Story GitHub image must be an exact 1024x576 PNG")
    return item, image


def read_test_day(day):
    """A separate live test record can never be mistaken for the canonical day."""
    _private()
    raw, _ = _get(day, "story.json", test=True)
    if raw is None:
        return None
    item = json.loads(raw)
    if (item.get("day") != day or item.get("version") != 1 or
            item.get("test_id") != day + "-01" or item.get("status") != "test"):
        raise RuntimeError("Daily Story test manifest is invalid")
    image, _ = _get(day, "scene.png", test=True)
    if image is None or hashlib.sha256(image).hexdigest() != item.get("image_sha256"):
        raise RuntimeError("Daily Story test image is missing or changed")
    if normalize_ready_image(image) != image:
        raise RuntimeError("Daily Story test image must be an exact 1024x576 PNG")
    return item, image


def request_chatgpt_test(day):
    """Commit an isolated request to the pre-opened private PR test queue."""
    date.fromisoformat(day)
    _private()
    if read_test_day(day):
        return "ready"
    ident = day + "-01"
    head = "daily-story-test-queue"
    path = "/contents/daily-story/requests/test-" + ident + ".json"
    existing = _api(path + "?ref=" + quote(head, safe=""))
    if existing is not None:
        return "queued"
    request = {"version": 1, "day": day, "test_id": ident, "source": "telegram-dev-test",
               "requested_at": datetime.now(timezone.utc).isoformat()}
    payload = {"message": "Daily Story: test ChatGPT bridge for " + ident,
               "content": base64.b64encode(json.dumps(request).encode("utf-8")).decode("ascii"),
               "branch": head}
    _api(path, "PUT", json.dumps(payload).encode("utf-8"))
    # A new commit on the open private PR emits synchronize for ChatGPT.
    return "queued"


def _put(day, filename, data, previous_sha):
    _, _, branch = _settings()
    payload = {"message": f"Daily Story {day}: private {filename}",
               "content": base64.b64encode(data).decode("ascii"), "branch": branch}
    if previous_sha:
        payload["sha"] = previous_sha
    _api(_path(day, filename), "PUT", json.dumps(payload).encode("utf-8"))


def write_day(day, episode, image):
    """CLI/agent handoff: refuse a public destination and publish manifest last."""
    from muba_story import START, _length_checked
    if date.fromisoformat(day) < START:
        raise ValueError("Daily Story date precedes its first episode")
    _private()
    for field in ("title", "title_tr", "scene"):
        if not isinstance(episode.get(field), str) or not episode[field].strip():
            raise ValueError("Daily Story episode is incomplete")
    for field in ("story", "story_tr"):
        _length_checked(episode[field])
    if date.fromisoformat(day) > START:
        previous_day = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        previous = read_day(previous_day)
        if not previous:
            raise RuntimeError("Previous Daily Story GitHub episode is missing: " + previous_day)
        if episode["story"] == previous[0]["episode"]["story"] or episode["story_tr"] == previous[0]["episode"]["story_tr"]:
            raise ValueError("Daily Story must advance the previous day's episode")
    image = normalize_ready_image(image)
    current = read_day(day)
    if current and current[0].get("status") == "published":
        raise ValueError("Published Daily Story cannot be replaced")
    image_sha = hashlib.sha256(image).hexdigest()
    manifest = {"version": 1, "day": day, "status": "draft", "episode": episode,
                "image_sha256": image_sha, "image": "scene.png"}
    _, old_image_sha = _get(day, "scene.png")
    _, old_manifest_sha = _get(day, "story.json")
    _put(day, "scene.png", image, old_image_sha)
    _put(day, "story.json", json.dumps(manifest, ensure_ascii=False).encode("utf-8"), old_manifest_sha)
    return manifest
