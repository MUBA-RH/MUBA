# MUBA V3 — Supported Android build host handoff

## Verified boundary

The phone/Termux probe reached Telegram's real Gradle configuration and failed because no Android SDK location was configured. The Termux experiment therefore remains a useful source/test workspace, but it is not the release APK build host.

Current upstream Telegram Android requirements (verified 2026-09-20):
- Android Studio 2025.1.4
- Android SDK 36
- Android NDK 27.2.12479018
- recursive Telegram source checkout
- developer-owned api_id
- developer-owned release keystore/passwords
- developer-owned Firebase google-services.json
- developer-owned BuildVars values

Telegram also requires custom clients not to present themselves as the official Telegram app and to publish source in accordance with the repository licence.

## Build-host contract

Use a supported Windows/macOS/Linux/ChromeOS Android development host. Android's official download page does not support the current Android phone as an Android Studio host. Keep the phone Termux tree as a disposable/isolated probe workspace only.

## V3 integration order

1. Clone official Telegram recursively at the upstream commit selected for the V3 patch.
2. Verify SDK 36 and NDK 27.2.12479018 before changing source.
3. Add the MUBA V3 gate, translation-before-send pipeline and one-shot bypass.
4. Patch only the interactive chat composer send boundary; never globally intercept SendMessagesHelper.
5. Official MUBA numeric dialog ID is private/local build configuration. Missing/zero disables translation.
6. Successful translation resumes the same stock Telegram send path exactly once.
7. Translation failure does not publish the Turkish draft.
8. Non-MUBA chats/groups/channels remain stock Telegram.
9. Build debug/internal APK first.
10. Run device acceptance tests before any release signing.

## Private inputs — never commit

Do not commit or print:
- Telegram API hash
- Telegram authorization/session material
- phone/login/2FA codes
- release keystore or passwords/aliases
- Firebase google-services.json
- private BuildVars values

## Production boundary

Do not modify telegram-bot, Guardian, Assistant, Studio, Render, website, webhook, production environment variables, or existing Telegram user sessions to make Android V3 compile.

## Device acceptance matrix

PASS requires all of the following:
- official MUBA channel + Turkish + toggle ON => recipient/channel receives English
- no bot invocation and no via-bot attribution
- private chat => unchanged stock behavior
- other group => unchanged stock behavior
- other channel => unchanged stock behavior
- translation failure => no accidental Turkish send
- translated send occurs once (no recursion/duplicate)
- toggle OFF => stock behavior
- multiline/URL/mention/reply/entity cases preserve expected send semantics
- app restart/re-login does not broaden translation scope
- official Telegram app/session remains unaffected

No APK may be called stable until this matrix passes on-device.
