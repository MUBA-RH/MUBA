# V3 upstream send-hook integration map

Pinned upstream inspection commit: `9552e5541e1274b9557c9832b204dbfcaf44b3dc`.

This map narrows the next Android fork change to Telegram's composer/send boundary without touching the MUBA production bot.

## Verified upstream surfaces

GitHub code inspection confirms Telegram Android currently exposes `ChatActivityEnterView.ChatActivityEnterViewDelegate.onMessageSend(...)` and uses `SendMessagesHelper` for normal outgoing user messages. The fork integration must remain upstream-aware: exact surrounding code must be re-checked at patch/build time rather than assuming line numbers remain stable.

## Hook contract

For the main chat composer only:

1. Read the current dialog id already owned by the chat screen.
2. Call `MubaDevSendPipeline.prepare(account, dialogId, OFFICIAL_MUBA_CHANNEL_DIALOG_ID, toggle, draft, success, failure)`.
3. If it returns `false`, continue the untouched stock Telegram send path immediately.
4. If it returns `true`, stop the original send attempt while translation is pending.
5. On success, continue the SAME stock send path once with translated English text/entities.
6. On failure, keep/restore the Turkish draft and surface an error. Never fall back to sending Turkish automatically.

## Recursion guard

The translated success callback must not re-enter the translation hook indefinitely. The fork patch must carry a one-shot bypass flag/token when it resumes the stock send path. The bypass is consumed immediately and must be scoped to that single send attempt.

## Scope exclusions

Do not hook global `SendMessagesHelper.sendMessage`: that would risk translating messages originating outside the interactive MUBA channel composer. Do not hook share sheets, bot webviews, popup notifications, scheduled/background flows, or other chats globally.

## Configuration

`OFFICIAL_MUBA_CHANNEL_DIALOG_ID` must come from private/local Android build configuration, not from a username and not from the production repository. Missing/zero value disables translation.

## Build-time blockers still external

A real APK requires the upstream Android build environment plus the DEV's private build inputs: own Telegram `api_id`, replacement signing keystore/passwords, Firebase `google-services.json`, and required `BuildVars.java` values. These are never committed here.

## Acceptance

The source patch is not called live until a signed APK is built and device-tested. Device tests must prove official channel translation, non-MUBA chat pass-through, failure-no-send, one-send-only recursion behavior, restart/re-login, and no regression to the production MUBA services.
