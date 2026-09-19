# MUBA V2 / Autonomy Blueprint
Implement only after DEV explicitly chooses BUILD MUBA V2 / AUTONOMY.

Goal: DEV supplies authoritative facts MUBA cannot independently know; MUBA safely executes routine plan -> create -> validate -> schedule -> publish -> verify -> remember -> continue.

Build order:
0 Continuity: preserve BLUE, recovery manifest and rollback.
1 Persistent Memory: durable DB for truth, story, jobs, publications, media, health, events, daily snapshots and migrations; use idempotency.
2 Truth Registry: protected authoritative facts with provenance/version/effective lifecycle; creative AI cannot write protected truth.
3 Core/Orchestrator: deterministic coordinator; does not absorb Guardian/Assistant/Studio internals.
4 Scheduler/Job Engine: durable jobs, leases/locks, idempotency keys, attempts, next-attempt and terminal states.
5 Story Engine: persistent narrative state, previous/next hooks, reuse history and constraints.
6 Media Pipeline: Core -> Studio -> validator -> accepted media record; bounded retries.
7 Publisher adapters: independent X, Telegram and future adapters implementing prepare/send/verify and storing provider IDs.
8 Watchdog: independent health checks and circuit state; never rewrites production code.
9 Reporting: machine daily snapshot plus concise Turkish DEV report.
10 Shadow: compute without external side effects.
11 Canary: grant one narrow real capability at a time.
12 Blue/Green: promote only after tests, shadow/canary evidence, rollback rehearsal and DEV authorization.

Failure engineering: timeouts, bounded retry/backoff, circuit breakers, idempotency, durable before/after checkpoints, failed/dead-letter jobs, DEV pause/emergency stop.

AI may draft stories/posts/humor/visual concepts. Deterministic code owns truth, authority, scheduling, quotas, validation, retries, security and release state. Infrastructure/provider choices must be re-verified at implementation time.