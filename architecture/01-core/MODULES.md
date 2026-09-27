# 01 — CORE

Runtime foundation and shared contracts.

## Modules
- identity — MUBA master identity and character rules
- configuration — environment/configuration boundaries
- authority — DEV authority and permissions
- language — shared language routing
- knowledge — official knowledge and source policy
- memory-context — user/group memory, context and timeline layers
- risk-policy — shared risk/conflict policy
- updates — ecosystem update state
- continuity — shared conversation/system continuity

## Current implementation map
- telegram-bot/muba_core/
- telegram-bot/muba_master_identity.py + .json
- telegram-bot/layers/01_authority ... 18+
- telegram-bot/muba_updates.py
- telegram-bot/conversation_continuity.py
