# MUBA Android V3 / APK — Purpose and Architecture

## Why this exists
The Android V3 client exists for a DEV-specific Telegram workflow that a normal Bot API bot cannot provide.

Target experience:
1. DEV writes Turkish inside Telegram.
2. Translation happens before the normal user send path.
3. The recipient/channel receives English from the DEV's own Telegram user account.
4. The outgoing message is a normal user message, without inline-bot attribution.
5. Normal use does not require typing @MUBA_RH_AI_Bot or using Termux.

This is why the solution was moved into an isolated Telegram Android user-client path rather than trying to force the production MUBA bot to impersonate the DEV.

## Isolation boundary
Android V3 must not replace or mutate:
- production Bot API webhook;
- Guardian;
- private Assistant;
- MUBA Studio;
- production bot token;
- production group authority.

If Android V3 is removed or fails, production MUBA must continue normally.

## Translation gate
Translation is intentionally restricted to the configured official MUBA Telegram dialog numeric ID. Other chats use normal Telegram behavior.

The system fails closed when required configuration is missing or the dialog does not match.

## Historical development sequence
PR #79:
- introduced persistent V2 DEV chat mode so the recipient could be selected once and DEV could type Turkish without repeating an inline-bot prefix.

PR #80:
- locked the V2 translation path to the official MUBA channel numeric ID;
- made destination mismatch fail closed.

PR #89:
- normalized Android dialog-ID comparison used by V3.

PR #90:
- preserved Telegram's native whole-chat translation entry point in the exact MUBA dialog;
- preserved normal behavior elsewhere;
- did not remove the outgoing translate-before-send path.

## Current V3 source
The repository contains:
- android-v3/MubaDevSendBypass.java
- android-v3/MubaDevSendPipeline.java
- android-v3/MubaDevTranslateBeforeSend.java
- android-v3/MubaDevTranslationGate.java
- android-v3/apply_v3_patch.sh
- android-v3/bootstrap_upstream.sh
- android-v3/stage_supported_build.sh
- supporting build probes

## GitHub cloud build
Workflow:
`.github/workflows/muba-v3-android-cloud-build.yml`

Required sensitive values are GitHub Actions secrets and must not be committed.

The workflow uses pinned Telegram source, applies MUBA V3 helpers/patching, validates the target gate, builds a standalone APK with the Telegram toolchain, and uploads the APK as an artifact.

Verified GitHub record captured for this Vault:
- workflow run #18: SUCCESS
- head SHA: `5e61d984e772108299de0beadb386b248609c09c`
- artifact: `MUBA-V3-Android-APK`
- artifact SHA-256 digest: `c69e3edbeb422c4376a66d495c0aeeb60dd022081a678f5a73896b6dc8048971`

Later PR-triggered build runs #19 and #20 also completed successfully on subsequent repository states.

## Security
Never commit:
- Telegram API hash;
- auth/session material;
- phone number/login code;
- 2FA credentials;
- signing keys;
- Firebase/private BuildVars values.

## Recovery
Android V3 can be rebuilt from the source/workflow snapshot when required credentials are re-supplied securely. It is not required to restore the production Telegram bot.
