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
`muba_history.json` is the canonical append-only record of verified user-facing MUBA developments.

**MUBA Updates** in the private Assistant is the single user-facing ecosystem change center: every canonical change appears there once, related units show badges that resolve to the same history record, and MUBA Daily does not maintain a duplicate general update feed. Website Development Log and MUBA Daily Development Log continue to provide public/technical historical views from the same canonical source.

A user-facing code change must add a new History entry. CI fails when that rule is broken or when an established history record is silently rewritten.

## Stability model

Production baseline is `main`.

Development follows:

**START 🔥 MERGE 🟢 PROTECT SYSTEM 🛡️ STABLE 🔒**

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

Gallery production storage supports a private **Cloudflare R2** backend so Studio creations survive Render restarts and redeploys even when the web service runs without a persistent disk. When R2 credentials are configured, Gallery uses R2 as its durable archive and does not silently downgrade to temporary local storage.

Runtime state separately prefers:
1. explicit `MUBA_MEMORY_FILE`;
2. persistent storage associated with `MUBA_GALLERY_DIR`;
3. an existing Render `/var/data` persistent-disk mount;
4. safe in-memory fallback.

`/health/state` reports persistence plus the non-secret Gallery backend label without exposing credentials or filesystem paths.

## Recovery / Vault

MUBA System Vault is intentionally passive and isolated from production. It exists for source recovery, continuity, handover and optional future architecture work. Vault must never auto-replace current MUBA or auto-activate V2.

After every `main` update, **MUBA Vault Auto Sync** independently runs the pinned Telegram regression suite, public website smoke check and canonical History validation. Only after those checks pass does it synchronize the passive `vault/system-vault-final` snapshot, update its stable-main metadata and create a new ZIP + SHA256 artifact. A failed validation leaves the previous Vault snapshot untouched.

Restoring the official MUBA system remains a recovery path. Creating or adapting a **different project** from the MUBA Vault/architecture is a protected reuse path: it requires prior written authorization from the MUBA Developer and must pass the deny-by-default permission gate.

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

## License / source availability

**MUBA is publicly viewable, not freely reusable.**

This repository is **source-available and permission-required**. Public access is provided for transparency, review and continuity; it does not grant permission to deploy, reproduce, adapt, rebrand, redistribute, commercialize, port, or use the MUBA implementation, Vault, or original project-specific architectural arrangement in another project.

Prior written authorization from the **MUBA Founder / Developer** is required for protected reuse.

The supported Vault new-project path is **deny-by-default**. A permission document must match an active SHA-256 approval fingerprint recorded in the official `muba_authorizations.json` registry; otherwise installation must stop.

Third-party libraries, platforms, APIs and assets remain subject to their own licenses and rights.

See:
- `LICENSE.md` — MUBA Source-Available License v1.0;
- `docs/MUBA_PERMISSION_MODEL.md` — authorization model and supported Vault gate;
- `MUBA_PERMISSION_TEMPLATE.json` — permission grant template.
