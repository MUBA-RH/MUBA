# Development Protocol

DEV command: BAŞLA 🔥 MERGE 🟢 STABİL 🔒

Mandatory flow:
CURRENT STABLE -> verify repository reality -> isolated branch from exact stable SHA -> requested scope only -> compile/static checks -> relevant unit/integration/regression tests -> PR -> CI GREEN -> merge with expected head SHA -> deployment/live verification when applicable -> record new stable/recovery state -> NEW STABLE.

Never merge red, cancelled, pending, unknown or unverified CI.

Successful closure must be exactly: Tamamlandı. 🔥🟢🔒

Do not claim an external live state unless actually observed. Preserve original working baselines. Before edits inspect the full affected integration chain, including handler ordering, Guardian, group filters, Assistant, cooldown/dedup, webhook, runtime and tests. No opportunistic refactor during scoped maintenance. If behavior breaks, rollback instead of stacking speculative production patches.