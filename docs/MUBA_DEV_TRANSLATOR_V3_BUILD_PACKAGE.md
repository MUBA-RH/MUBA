# MUBA DEV Translator V3 — fast build package

This package converts the completed V3 architecture into a reproducible staging step on a supported Android build host.

## Official build baseline

Telegram's current compilation guide requires Android Studio 2025.1.4, Android SDK 36 and Android NDK 27.2.12479018. Telegram also requires a developer-owned api_id and replacement private release/Firebase/BuildVars inputs before publishing an APK.

The Android Studio host itself must be a supported Windows/macOS/Linux/ChromeOS environment. The phone/Termux experiment is not the release build host.

## One-command staging

On the supported build host:

```bash
bash android-v3/stage_supported_build.sh /path/to/Telegram
```

The script verifies SDK 36 + NDK 27.2.12479018, pins the inspected upstream Telegram commit, initializes submodules and stages the four credential-free MUBA V3 helper classes into the upstream Java tree.

It does **not** read, print or commit API hashes, sessions, phone codes, 2FA, keystores, Firebase files or private BuildVars.

## Remaining build-host-only integration

The composer patch is intentionally not applied blindly from this repository. At build time, re-check the pinned/current upstream `ChatActivityEnterView.ChatActivityEnterViewDelegate.onMessageSend(...)` surface and wire it to `MubaDevSendPipeline.prepare(...)`.

Required behavior remains:
- exact official numeric MUBA dialog id + toggle ON => translate Turkish to English before stock send;
- success => arm one-shot bypass and resume the same stock send once;
- failure => no send, keep/restore draft;
- every other dialog => untouched stock Telegram;
- never hook global `SendMessagesHelper.sendMessage`.

## Stable boundary

The production MUBA bot, Guardian, Assistant, Studio, Render/webhook, V1/V2 translator and existing Telegram sessions are outside this build package and must not be changed.

V3 is not declared live/stable until an APK is compiled, installed and the full device acceptance matrix passes.
