# MUBA Development Protocol

Permanent DEV command:
BAŞLA 🔥 MERGE 🟢 SİSTEMİ KORU 🛡️ STABİL 🔒

## Mandatory flow
CURRENT STABLE
-> verify GitHub repository reality
-> isolate requested work on a branch from the exact stable SHA
-> preserve unrelated working behavior
-> make the smallest required change
-> compile/static validation
-> unit/integration/regression tests
-> pull request
-> CI GREEN
-> merge with expected head SHA when possible
-> verify resulting main/runtime when applicable
-> record new stable state
-> STABLE

## Rules
- Never merge red/failed unknown work.
- Do not claim live success without evidence.
- Do not opportunistically refactor unrelated modules.
- Do not silently activate V2.
- Do not modify production directly for normal development.
- Preserve original working behavior and rollback.
- Use GitHub as the canonical source/development record.
- Vault updates target the Vault branch, not production main.

## Scope discipline
If the request concerns Assistant, do not alter Guardian unless required.
If the request concerns Guardian reports, do not redesign Assistant.
If the request concerns Android V3, do not inject it into Bot API runtime.

## Current stable captured by this Vault
`602ebffe23de7373e7ee513af33dea219fe6deba`
