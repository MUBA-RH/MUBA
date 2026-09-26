"""Prepare a new Daily Story episode from the previous saved story text."""
from __future__ import annotations

import json
import os

import aiohttp

from muba_story import BEATS, START, _previous_state, draft, save_episode
from datetime import date

MODEL = os.getenv("MUBA_STORY_TEXT_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8").strip()


async def prepare(day):
    """Draft once and persist; failed generation never repeats an old episode."""
    if (date.fromisoformat(day) - START).days < len(BEATS):
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
        "Return ONLY a JSON object with string fields title, title_tr, story, story_tr, scene. "
        "story is English, story_tr is its natural Turkish translation. EACH is 150–170 Unicode characters "
        "including spaces. scene is an English description of ONE visible 16:9 moment from today's story "
        "with the setting, action and important object. No panel divisions, visible caption or text overlay."
    )
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    headers={"Authorization": "Bearer "+token}
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            async with session.post(url, json={"messages": [
                {"role": "system", "content": "Write concise original stories. Follow JSON and character limits precisely."},
                {"role": "user", "content": prompt if attempt == 0 else prompt + " Check both exact lengths carefully before answering."},
            ], "max_tokens": 420}, headers=headers, timeout=aiohttp.ClientTimeout(total=70)) as response:
                if response.status != 200:
                    raise RuntimeError(f"Daily Story text provider unavailable ({response.status})")
                payload=await response.json()
            raw=payload.get("result", {}).get("response", "")
            try:
                episode=json.loads(raw[raw.index("{"):raw.rindex("}")+1])
                return save_episode(day, episode)
            except (ValueError, KeyError, TypeError):
                continue
    raise RuntimeError("Daily Story could not produce a valid connected 150–170 character episode")
