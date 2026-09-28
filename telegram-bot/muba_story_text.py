"""Prepare a new Daily Story episode from the previous saved story text."""
from __future__ import annotations

import json
import logging
import os

import aiohttp

from muba_story import ORIGIN_START, _previous_state, draft, save_episode
from datetime import date

MODEL = os.getenv("MUBA_STORY_TEXT_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8").strip()
logger = logging.getLogger(__name__)
STORY_FIELDS = ("story", "story_tr", "story_zh", "story_ar", "story_hi")
LANGUAGE_NAMES = {"story": "English", "story_tr": "Turkish", "story_zh": "Chinese",
                  "story_ar": "Arabic", "story_hi": "Hindi"}


def _clean_text(value):
    return " ".join(value.split()) if isinstance(value, str) else ""


async def _ask(session, url, headers, prompt, *, max_tokens):
    async with session.post(url, json={"messages": [
        {"role": "system", "content": "Write original connected stories. Follow the requested format and character limit precisely."},
        {"role": "user", "content": prompt},
    ], "max_tokens": max_tokens}, headers=headers,
        timeout=aiohttp.ClientTimeout(total=70)) as response:
        if response.status != 200:
            raise RuntimeError(f"Daily Story text provider unavailable ({response.status})")
        payload = await response.json()
    result = payload.get("result", {})
    return result.get("response", "") if isinstance(result, dict) else ""


async def _repair_field(session, url, headers, episode, field):
    """Repair only the invalid language without resetting the other translations."""
    candidate = _clean_text(episode.get(field))
    for _ in range(5):
        prompt = (
            f"Write ONLY the {LANGUAGE_NAMES[field]} version of this one short story. "
            f"Canonical English story: {episode['story'] if field != 'story' else episode.get('story', '')} "
            "Preserve its events, MUBA name and ending. Do not add a new event. "
            "The response must be exactly 150 to 170 Unicode characters including spaces; "
            "aim for 160 characters. Return the story alone, with no quotes, label or JSON. "
            f"Previous attempt had {len(candidate)} characters: {candidate}"
        )
        candidate = _clean_text(await _ask(session, url, headers, prompt, max_tokens=700)).strip('"“”')
        if 150 <= len(candidate) <= 170:
            episode[field] = candidate
            return
    raise RuntimeError(f"Daily Story {field} could not meet the 150–170 character limit")


async def prepare(day):
    """Draft once and persist; failed generation never repeats an old episode."""
    if date.fromisoformat(day) < ORIGIN_START:
        return draft(day)
    try:
        return draft(day)  # already prepared, including after service restart
    except RuntimeError as exc:
        if "awaiting a new connected episode" not in str(exc):
            raise
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    token = os.getenv("CLOUDFLARE_API_TOKEN")
    if not account or not token or not MODEL:
        raise RuntimeError("Daily Story text provider is not configured")
    previous = _previous_state(day)
    prompt = (
        f"Write the NEXT day in MUBA's continuous illustrated neighborhood story for {day}. "
        f"Prior day ({previous['day']}): {previous['story']} "
        "Keep established events and move the story forward with a new small action and outcome. "
        "Make the beginning, middle and ending understandable within ONE short episode. "
        "Friendly, light, airy, warm, playful; avoid invented product claims, token promises, prices, "
        "unrelated brands, and a repeated garden/arrow plot. "
        "Return ONLY a JSON object with string fields title, title_tr, story, story_tr, "
        "story_zh, story_ar, story_hi, scene. story is English; the other four are natural "
        "Turkish, Chinese, Arabic and Hindi translations respectively. Each story field "
        "must have 150–170 Unicode characters including spaces. "
        "scene is an English description of ONE visible 16:9 moment from today's story "
        "with the setting, action and important object. No panel divisions, visible caption or text overlay."
    )
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    headers={"Authorization": "Bearer "+token}
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            raw = await _ask(session, url, headers,
                             prompt if attempt == 0 else prompt + " Return a complete JSON object.",
                             max_tokens=1600)
            try:
                episode=json.loads(raw[raw.index("{"):raw.rindex("}")+1])
                if not isinstance(episode, dict) or any(not _clean_text(episode.get(field))
                    for field in (*STORY_FIELDS, "title", "title_tr", "scene")):
                    raise ValueError("Missing Daily Story field")
                break
            except (ValueError, KeyError, TypeError):
                continue
        else:
            raise RuntimeError("Daily Story text provider did not return a complete episode")
        for field in STORY_FIELDS:
            episode[field] = _clean_text(episode[field])
            if not 150 <= len(episode[field]) <= 170:
                logger.info("Daily Story %s initial character count: %s", field, len(episode[field]))
                await _repair_field(session, url, headers, episode, field)
        return save_episode(day, episode)
