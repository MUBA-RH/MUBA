# MUBA DEV Translator V3 — Android architecture

Status: isolated design baseline. This document does not change the production MUBA Bot API runtime, Guardian, Assistant, Studio, or existing Telegram webhook.

## User experience target

The DEV writes Turkish in a Telegram conversation and sends an English message from the DEV's own Telegram user account. The recipient must see a normal user message, with no inline-bot attribution and no need to type `@MUBA_RH_AI_Bot` or a recipient username in Termux.

## Verified Telegram primitives

- Telegram's `messages.translateText` translates text and is a **user-only** MTProto method.
- A user-authorized MTProto client can send the translated text as that user.
- The V2 live test established this repository's user-session path can translate Turkish and send a normal user message without inline-bot attribution.
- Telegram's Android client is open source and Telegram permits developers to build clients using their own `api_id`, subject to Telegram's API terms, branding requirements, security guidance, and the Android client's GPL license.

## Architectural decision

The exact target UX must live in a Telegram **user client**, not in the existing Bot API webhook.

A bot cannot silently replace the text typed into the official Telegram Android composer and then make Telegram's normal Send button send the replacement as the human user. Inline mode also has bot attribution. Therefore V3 must not attempt to solve this with Guardian, Assistant, inline mode, accessibility automation, or a hidden bot.

The supported exact architecture is an isolated Android Telegram client fork/variant based on Telegram's published Android source:

1. DEV composes Turkish in the chat composer.
2. The client intercepts the local send action before the outgoing message is created.
3. If DEV Translation is enabled, the client calls `messages.translateText(text=..., to_lang="en")` using the already-authorized Telegram user session.
4. The translated `TextWithEntities` replaces the outgoing composer payload locally.
5. The client invokes the normal Telegram user-message send path.
6. The recipient receives a normal message from the DEV account. No Bot API or inline bot participates.

## Safety boundaries

- V3 is a separate client build. It must never import, start, stop, replace, or mutate the production MUBA Bot API runtime.
- Existing MUBA bot token, Guardian authority, group ID, webhook secret, Studio, Assistant, and production Render service remain outside V3.
- `TELEGRAM_API_HASH`, user auth keys/sessions, phone numbers, login codes, and 2FA credentials must never be committed.
- V3 must use the DEV's own Telegram API application credentials.
- Translation is opt-in and visibly enabled in the client. No background mass messaging.
- On translation failure, the client must fail closed: do not silently send the original Turkish text. Show an error and leave the draft intact.
- Preserve message entities where Telegram returns them; Telegram documents that styled entities are preserved only for Premium users.
- Do not use Android Accessibility Service to click Send or scrape composer text. That design is brittle, over-privileged, and unnecessary when the client source is available.
- Do not use a custom keyboard as the canonical V3 solution: an IME can alter text, but it does not own Telegram's send pipeline and cannot guarantee the exact send-time behavior.

## Isolation plan

V3 development lives outside `telegram-bot/bot_mention.py` and outside production requirements.

Recommended source layout for the Android fork:

```
muba-dev-android/
  upstream/                  # Telegram Android source/submodule or fork
  patches/
    0001-dev-translation-toggle.patch
    0002-translate-before-send.patch
  docs/
    SECURITY.md
    UPSTREAM_SYNC.md
```

Do not vendor Telegram's full Android source into the production bot package. Keep the Android build lifecycle independent from Render.

## Send-state machine

```
DRAFT
  -> SEND_PRESSED
  -> if translation disabled: NORMAL_TELEGRAM_SEND
  -> if enabled:
       TRANSLATING
       -> success: REVIEW/translated payload -> NORMAL_TELEGRAM_SEND
       -> failure: DRAFT_RESTORED + ERROR (no send)
```

The first implementation should include a per-client master toggle and an optional preview/confirm mode. Automatic send after successful translation can be enabled only after the preview path passes live tests.

## Acceptance tests

V3 is not STABLE until all of these pass on a real Android device:

1. Turkish private-chat draft -> English recipient message.
2. No `via @...bot` attribution on recipient device.
3. No `@MUBA_RH_AI_Bot` typed in composer.
4. No Termux interaction for normal use.
5. No recipient username entered outside the selected Telegram chat.
6. Translation failure leaves original draft unsent.
7. Toggle OFF preserves stock Telegram send behavior.
8. Reply, emoji, URL, mention, multiline, and entity tests.
9. App restart and Telegram reauthorization behavior.
10. Existing official Telegram app/session remains unaffected.
11. MUBA production bot/Guardian/Assistant regression tests remain green.

## Build prerequisites

Telegram's current Android source README specifies Android Studio 2025.1.4, Android NDK 27.2.12479018, Android SDK 36, a developer-owned `api_id`, and project-specific signing/configuration. Follow the upstream README at build time because these requirements can change.

## Deployment rule

The Android client is never deployed to Render. Render remains the production host for the existing MUBA bot. V3 is built and installed as an Android APK on the DEV device after source review and device testing.

## Rollback

Uninstall/disable the V3 client and continue using the official Telegram app. No rollback of MUBA production is required because V3 is isolated.

## Current boundary

V2 proves the MTProto translation/send primitive. V3 architecture removes Termux and inline-bot UX by moving the same user-only translation operation into the Android client send pipeline. A production APK still requires the isolated Android fork to be implemented, built, signed, installed, and device-tested; this architecture document must not be represented as that APK.
