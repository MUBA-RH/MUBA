# 05 — DAILY STORY

Daily narrative generation, approval and publication lifecycle.

## Modules
- story-engine
- story-text
- story-state/continuity
- visual-generation
- identity/fingerprint continuity
- master-reference
- provider adapters — OpenAI/HF/Kaggle/ZeroGPU/Cloudflare/fallback
- archive bridge — GitHub
- worker/job contract
- Telegram approval
- web publication handoff
- X sharing handoff

## Current implementation map
- telegram-bot/muba_story*.py
- daily-story-worker/
- MUBA_DAILY_STORY_KAGGLE.ipynb
- kaggle/muba_daily_story_gpu_setup.ipynb
- .github/workflows/muba-daily-story-prepare.yml
- MUBA-RH/MUBA-DAILY-STORY (external archive/runtime boundary)
