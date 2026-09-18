# MUBA BRAIN migration report

## Source

- Full consolidated source: `codex-input/MUBA_BRAIN.txt` (29,745 lines)
- SHA-256: `bd74a544d8f42686d9fff7740ccf173e945647d8225a7a606e558ac43b55b4a8`
- Governing override: `codex-input/MUBA_CODEX_INTEGRATION_SPEC.md`

## Classification and mapping

The consolidated material was treated as behavioral evidence, rules, protocols, examples, tests, and superseded history. It was not copied into production as a monolith or as canned answers. Identity, authority, security, sources, CA, current information, scoped memory, conversation, conflict, learning, culture, and archive responsibilities remain mapped to the existing 23 specialist groups.

The final-source compatibility aliases for specification, health, bot/founder/group identity checks, observation, audit, learning queue, decision memory, incident closure, and snapshots are implemented through the protected adapter and `muba_core/operations.py`.

## Protected overrides

The integration specification wins over historical contradictions. In particular, official MUBA sources remain exactly `@MUBA_RH` and `https://muba-rh.github.io/MUBA/`; Telegram is not promoted to protected Official Knowledge. Numeric Telegram IDs remain the only authority mechanism, and retrieval never promotes itself into permanent knowledge.

## Verification

- `python -m unittest discover -s tests -v`: 44 tests passed.
- Syntax/import compilation completed for production modules.
- Webhook transport and `build_reply()` compatibility remain unchanged.
- No merge or deployment was performed.

## Remaining limitations

- Runtime state defaults to memory; JSON durability requires `MUBA_MEMORY_FILE`, and Render ephemeral disk is not durable infrastructure.
- Approved current-information retrieval requires an explicitly allowed subject-relevant source and `MUBA_WEB_ENABLED`.
- The local deterministic brain intentionally has no external generative-AI dependency.
