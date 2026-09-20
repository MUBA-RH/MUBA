# MUBA V3 — Termux-only build path

## Decision

Termux can be used as the command-line host for V3 development/build experiments, so a separate Android Studio application is not inherently required for every build step. However, this is an **experimental build path**, not a claim that Telegram Android officially supports Termux as its compilation environment.

Telegram's current official Android README specifies Android Studio 2025.1.4, Android SDK 36 and NDK 27.2.12479018. Its repository also contains a Linux Docker build path using command-line Gradle/Android SDK tooling. That supports the architectural conclusion that Android Studio is not the compiler itself, but it does **not** prove the upstream project builds unchanged under Android/Termux.

## Why Termux may fail

Telegram's Android build includes native code and upstream tooling that can assume a desktop Linux host (commonly x86_64). Termux runs on Android, typically arm64, with a different libc/userspace. SDK/NDK host binaries or build scripts may therefore fail even when Java/Gradle are present.

For that reason the safe order is:

1. Run `android-v3/termux_build_probe.sh`.
2. Install/verify command-line Java, Git, Android SDK 36, build-tools and NDK 27.2.12479018 in an isolated Termux workspace only if compatible packages/binaries are available.
3. Clone Telegram Android recursively into the isolated workspace.
4. Apply the MUBA V3 helper/gate/pipeline/bypass sources and the composer patch.
5. Supply private build configuration locally only.
6. Build a debug/internal APK first.
7. Install and run the official-channel/non-MUBA acceptance matrix.
8. Only after that create a release-signed APK.

## Hard boundary

Do not modify `telegram-bot/`, Render, Guardian, Assistant, Studio, webhook settings, or the current production bot to make the Android build work.

Do not commit API hash, Telegram auth/session, phone/login/2FA information, Firebase files, keystores, aliases or passwords.

If the current Telegram Android toolchain proves incompatible with Termux/arm64, stop the Termux build attempt and move the exact same isolated source/patch set to a supported Linux/Android Studio build host. That fallback changes the build host, not the V3 behavior.

## Phone replacement

A future phone does not need the production MUBA database copied into Telegram. The V3 client is an isolated client build. On a new phone, install the signed V3 APK, authorize the Telegram account, restore/provide the private V3 build/configuration as appropriate, and re-run the official-channel safety test. Never copy a live Telegram session secret into the public repository.
