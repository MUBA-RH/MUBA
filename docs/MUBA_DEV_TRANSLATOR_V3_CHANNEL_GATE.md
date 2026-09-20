# MUBA DEV Translator V3 — official-channel integration contract

This is the implementation contract for the isolated Telegram Android client.

## Locked behavior

Translation is **not global**. It is eligible only when all three conditions are true:

1. DEV Translation is enabled.
2. The configured official MUBA channel dialog id is non-zero.
3. The currently open Telegram dialog id exactly equals that configured numeric id.

Every private chat, group, and other channel follows Telegram's untouched normal send path.

## Send hook

At the Telegram composer send boundary, call `MubaDevSendPipeline.prepare(...)` before creating the outgoing text message.

- Return `false`: do not translate; immediately continue Telegram's stock send path.
- Return `true`: the MUBA pipeline owns this send attempt. Do not send the original draft.
- Translation success callback: continue the same stock Telegram send path with the returned English `TL_textWithEntities`.
- Translation failure callback: keep/restore the Turkish draft, show an error, and do not send.

The coordinator itself intentionally contains no `sendMessage` call. This prevents a second parallel send implementation.

## Configuration

The official channel numeric dialog id must be supplied by the isolated Android build/configuration and must not be inferred from a mutable username. Zero/missing configuration fails closed.

API credentials, Telegram auth/session material, phone/login/2FA data, signing keys and Firebase credentials must never be committed to the MUBA production repository.

## Device acceptance

Do not call V3 live/stable until a signed APK has been built and a real Android device verifies:

- official MUBA channel: Turkish composer draft -> English outgoing message;
- another channel: unchanged;
- private chat: unchanged;
- group: unchanged;
- translation failure: Turkish draft remains unsent;
- no inline-bot attribution and no Termux during normal use;
- restart/re-login behavior;
- existing MUBA Bot/Guardian/Assistant remains unaffected.
