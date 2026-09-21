# MUBA — WE LIVE HERE NOW

MUBA is an original meme character, a culture and a community.

**I'M MUBA.**  
**WE LIVE HERE NOW.**

This repository contains the current public MUBA system: website, Telegram Assistant, Guardian, MUBA Studio, Gallery, multilingual local brain, DEV translation tooling, tests and recovery-oriented documentation.

## Official public spaces

- Website: https://muba-rh.github.io/MUBA/
- X: https://x.com/MUBA_RH
- Telegram: https://t.me/MUBA_RH

## Current system

### Website
The GitHub Pages site is MUBA's public hub. It contains the living knowledge area, Development Log, Web Studio, MUBA Gallery and MUBA TWT.

### MUBA Assistant
Private Telegram Assistant with five supported languages: English, Turkish, Chinese, Arabic and Hindi. It provides MUBA knowledge, Story Mode, MUBA Daily, guides, update history and Studio access.

### Guardian
The protected security and management layer for the designated MUBA main group. Guardian is separate from ordinary Assistant conversation and follows DEV-only authority rules.

### MUBA Studio
Creates MUBA Meme, Image, Sticker and Reaction visuals. Web Studio and Telegram Studio use the same protected generation backend. Visible text is off by default unless the user explicitly requests writing.

### MUBA Gallery
Successful Studio creations can enter the shared Gallery archive. Public Gallery metadata contains the image label, format, source and creation time—not usernames, Telegram IDs or raw prompts. DEV moderation supports public, hidden and rejected states.

### MUBA History
`muba_history.json` is the canonical append-only record of verified user-facing MUBA developments. Website Development Log, Assistant Updates and MUBA Daily read from this shared history.

A user-facing code change must add a new History entry. CI checks this rule and prevents existing history records from being silently rewritten.

## Stability model

Production baseline is `main`.

Development follows:

**BAŞLA 🔥 MERGE 🟢 SİSTEMİ KORU 🛡️ STABİL 🔒**

Meaning: isolate the requested work, preserve the current stable system, test, merge only when green, validate after merge and retain rollback/recovery capability.

The production runtime does not automatically activate experimental V2/autonomy work.

## Tests

The repository contains regression coverage for:
- layered multilingual brain behavior;
- Assistant routing and conversation continuity;
- Guardian authority and security;
- Studio generation and text policy;
- Gallery archive and moderation;
- canonical History continuity;
- persistent state selection;
- Android V3 isolation/build behavior;
- public website smoke checks.

GitHub Actions run Telegram/runtime tests, the MUBA Continuity Gate and website smoke checks on relevant changes.

## Persistence

Runtime state automatically prefers:
1. explicit `MUBA_MEMORY_FILE`;
2. persistent storage associated with `MUBA_GALLERY_DIR`;
3. an existing Render `/var/data` persistent-disk mount;
4. safe in-memory fallback.

`/health/state` reports whether runtime state and Gallery storage are currently backed by a persistent path without exposing filesystem paths.

## Recovery / Vault

MUBA System Vault is intentionally passive and isolated from production. It exists for source recovery, continuity, handover and optional future architecture work. Vault must never auto-replace current MUBA or auto-activate V2.

Secrets are not stored in the repository or Vault.

## Security

Do not commit:
- Telegram bot tokens;
- Telegram API hash/session/phone/2FA data;
- Cloudflare credentials;
- signing keys;
- local environment files;
- other private credentials.

## Dependency baseline

Runtime dependency versions are pinned from a known-green CI baseline so deployments do not silently move to new package versions.

## License

No software license is currently declared in this repository. Public source visibility and an open-source reuse license are not the same thing. If reuse/distribution rights are intended, the DEV should choose and add an explicit license.
