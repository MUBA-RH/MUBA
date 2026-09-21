# V3 phone-only cloud build

The user-facing device may be Android-only. GitHub Actions provides the remote Linux runner; the phone only operates GitHub and later retrieves artifacts.

## Security

Required values are GitHub Actions repository secrets and are never committed:
- `MUBA_OFFICIAL_DIALOG_ID`
- `MUBA_V3_TELEGRAM_API_ID`
- `MUBA_V3_TELEGRAM_API_HASH`

Do not reuse the production bot token or the V2 StringSession for the Android APK.

GitHub documents repository Actions secrets under Settings → Secrets and variables → Actions. Secrets are referenced through the `secrets` context; unset secrets evaluate to an empty string. The workflow therefore fails closed when required values are absent.

## Current workflow boundary

`.github/workflows/muba-v3-android-cloud-build.yml` provisions Java, Android SDK 36 and NDK 27.2.12479018 on an Ubuntu runner, then executes the V3 supported-host staging package.

It intentionally does **not** publish a fake or incomplete APK. Telegram upstream requires developer-owned BuildVars values and, before publishing, replacement signing/Firebase files. The actual composer hook must also be integrated and compiled first.

## Next gate

Once the three scalar Actions secrets above exist, run **MUBA V3 Android Cloud Build** manually from the Actions tab. The first run validates the remote build host and source staging without exposing secret values.

The later APK job may only be enabled after:
1. composer hook is applied to the pinned/current upstream source;
2. private BuildVars/signing/Firebase inputs are injected without repository exposure;
3. Gradle task is confirmed against that upstream tree;
4. resulting APK passes the device acceptance matrix.
