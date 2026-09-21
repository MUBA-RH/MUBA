# MUBA Architecture and Safety Boundaries

## Current architecture
Public website -> GitHub Pages.

Telegram Bot API runtime -> bot_mention.py -> Guardian + private Assistant + Studio + layered local MUBA brain.

DEV translator path -> separate MTProto tooling.

Android V3 -> isolated Telegram Android user client fork/patch path for translate-before-send in the authorized official MUBA dialog.

Vault -> passive branch only; never runtime.

## Authority hierarchy
1. DEV numeric authority.
2. Deterministic security/truth rules.
3. Verified official project facts.
4. Product interaction/content layers.
5. Creative generation.

Creative systems never override DEV authority, CA truth, official links or security policy.

## Failure isolation
A failure in Android V3 must not stop the Bot API bot.
A Studio failure must not disable Guardian.
An Assistant content update must not weaken Guardian.
A Vault update must not change production.
A V2 experiment must not replace BLUE/current stable MUBA.

## Future V2 / Autonomy
Future autonomy is an orchestration plane above stable modules, not permission to rewrite them automatically.

BLUE = current verified production.
GREEN = isolated candidate.
Promotion requires tests, evidence and explicit DEV authorization.
