# Preserved Current MUBA System

## Recovery anchor
Repository: MUBA-RH/MUBA
Pre-Vault production commit: `d09aad85380ac87586e3656f796fc27967d75856` (`d09aad8`)
Default branch: `main`
Public site: GitHub Pages from this repository.
Runtime: Python Telegram webhook service deployed externally; current code expects Render environment values.

This document describes the repository state inspected at the recovery anchor. The Vault itself must never be imported by production code.

## Current production surfaces
### Website
- Root `index.html` is the GitHub Pages site.
- Official links in inspected HTML include X `@MUBA_RH` and Telegram `t.me/MUBA_RH`.
- CA value is not configured in the inspected page; the CA copy value is empty.

### Telegram runtime
Primary integration file: `telegram-bot/bot_mention.py`.
- Webhook-based Python Telegram bot.
- Required runtime variables visible in code: `TELEGRAM_BOT_TOKEN`, `RENDER_EXTERNAL_URL`; optional explicit `MUBA_WEBHOOK_SECRET` with token-derived fallback.
- Duplicate Telegram message guard: bounded in-memory OrderedDict, six-hour TTL, 4096 entries.
- Main group and DEV authority are enforced by Guardian/core code.
- Dedicated `#MUBA ASSISTANT` group-call handler has priority and is exact after whitespace/case normalization.
- Non-DEV group calls: 7 successful calls per Europe/Istanbul calendar day, minimum 7200 seconds between successful calls, per Telegram user ID.
- DEV bypasses that quota/interval.
- Call quota is RAM-only and resets on process restart.
- Group call wait/limit responses support EN/TR/ZH/AR/HI, using saved Assistant language when available and Telegram language fallback.

### Assistant
Relevant files include `assistant_mode.py`, `human_catalog.py`, `natural_chat.py`, `muba_daily.py`, `assistant_extras.py`, and the MUBA brain/core/layers.
- Private-chat Assistant uses explicit language selection and supports English, Turkish, Chinese, Arabic and Hindi.
- Guided topics, natural/colloquial matching, MUBA Daily, Story Mode, Content Lab, Community Guide, Security Check and Studio entry exist in the inspected runtime.
- Private Assistant is MUBA-domain constrained; unrelated input receives the configured outside-domain response.
- Group normal conversation is not the private Assistant; Guardian owns group policy.

### Guardian
Relevant file: `telegram-bot/guardian.py`, integrated by `bot_mention.py`.
- Authorized management commands include START, STOP, STATUS/GUARDIAN, SECURITY, LOCKDOWN, NORMAL, WARN, MUTE, UNMUTE, BAN, UNBAN, DELETE, HELP.
- Non-DEV control attempts are rejected/cleaned according to Guardian logic.
- START/STOP can change Telegram chat permissions. The current START implementation enables text and invite permission in code while disabling media/polls/previews/admin-like member permissions; Telegram UI behavior for invite permission may still require manual setting.
- Security inspection covers official-link policy, fake/unverified CA candidates, suspicious wallet/credential lures, external links and flood/risk enforcement.
- Security/strike/lockdown state that is in process memory is not durable across restarts unless explicitly persisted elsewhere.
- Official CA is not configured at this recovery anchor; never invent one.

### Studio
Relevant file: `telegram-bot/muba_studio.py`, wired through `bot_mention.py`.
- Studio is available from Assistant and has a web UI/endpoint surface.
- Cloudflare AI configuration is supplied by environment, not repository secrets.
- Reference identity URL and AI image workflow are part of the Studio implementation.
- Non-DEV daily generation quota exists; DEV bypass is supported.
- Generated output registry and quota are process-memory based and therefore restart-sensitive.
- Generated output links are ephemeral.
- Never put Cloudflare tokens or other credentials in Git.

### Brain / knowledge
- `muba_brain.py` is the stable adapter into the layered system.
- `muba_core/registry.py` dynamically loads specialist layers under `telegram-bot/layers`.
- The current semantic system is local/rule/frame based. Do not falsely describe it as an LLM, embeddings system, or true RAG.
- Repository contains legacy/source knowledge artifacts under `codex-input` and `telegram-bot/data`; do not assume every historical artifact is a live runtime dependency.

### Tests / CI
Workflow: `.github/workflows/telegram-bot-tests.yml`.
The inspected repository contains tests for layered brain, semantic exams, Assistant, natural chat, Guardian authority/security/risk, MUBA Daily, Studio, conversation context and related behavior.

## Known operational limitations to preserve in handoff
- Render/free-runtime cold starts can delay the first request after idle.
- Several counters/state stores are RAM-only.
- External APIs/services can fail independently.
- Secrets are external and are deliberately absent from this Vault.
- A Git commit alone cannot recreate external account ownership, secrets or provider settings. Recovery requires the operator to possess those accounts/credentials.

## Preservation rule
If this Vault is deleted, current production must continue unchanged. Nothing under `MUBA_SYSTEM_VAULT/` may be required by runtime imports, startup, deployment, website rendering, webhook handling or tests.