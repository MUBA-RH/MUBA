# Development Protocol
DEV command: BAŞLA 🔥 MERGE 🟢 STABİL 🔒

Mandatory flow:
CURRENT STABLE -> verify repository reality -> isolated branch from exact stable SHA -> requested scope only -> compile/static checks -> relevant unit/integration/regression tests -> PR -> CI GREEN -> merge with expected head SHA -> deployment/live verification where applicable -> record new stable/recovery state -> NEW STABLE.

Never merge red, cancelled, pending, unknown or unverified CI.
Successful closure must be exactly: Tamamlandı. 🔥🟢🔒

Do not claim external live state unless actually verified. Search the whole integration chain before edits. Do not opportunistically refactor unrelated stable modules. Roll back rather than stack speculative production patches. Update Vault state when a new production stable changes documented facts, without making Vault a runtime dependency.