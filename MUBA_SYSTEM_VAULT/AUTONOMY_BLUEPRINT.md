# MUBA V2 / Autonomy Blueprint

Do not implement because this document exists. Begin only after DEV explicitly chooses BUILD MUBA V2 / AUTONOMY and authorizes the scoped protocol.

Goal: DEV supplies authoritative facts MUBA cannot independently know. MUBA safely performs routine plan -> create -> validate -> schedule -> publish -> verify -> remember -> continue.

Build order:
0. Continuity: preserve BLUE, release manifest, recovery, rollback rehearsal.
1. Persistent Memory: durable database for truth_records, story_state, jobs, publication_records, media_records, health_events, system_events, daily_snapshots, schema_migrations. Use idempotency keys.
2. Truth Registry: protected versioned facts with provenance, authorization and effective/expiry times. Creative AI cannot write protected truth.
3. Core/Orchestrator: deterministic coordinator reading truth/state and creating jobs; does not absorb Guardian/Assistant/Studio internals.
4. Scheduler/Job Engine: durable jobs, leases/locks, idempotency, attempts, next-attempt and terminal states. Restart cannot lose work; parallel workers cannot duplicate external actions.
5. Story Engine: persistent narrative state, theme, episode, previous/next hooks, reuse history and constraints.
6. Media Pipeline: Core request -> Studio -> validator -> accepted media record; bounded retry.
7. Publisher adapters: independent X/Telegram/future prepare-send-verify adapters with provider IDs. External API access is never assumed permanently available/free.
8. Watchdog/Health: independent checks; DEGRADED/circuit-open states; DEV notification; never rewrites production.
9. Reporting: daily machine snapshot plus concise Turkish DEV report.
10. Shadow: compute without external side effects.
11. Canary: one narrow real capability, verify, expand gradually.
12. Blue/Green: promote only after tests, evidence, rollback rehearsal and DEV authorization.

Failure engineering: network timeouts, bounded retry/backoff, circuit breakers, idempotent publish/send, durable before/after checkpoints, failed/dead-letter state, safe pause and DEV emergency stop.

AI boundary: AI may draft story/posts/humor/visual concepts. Deterministic code owns authority, truth, scheduling, quotas, validation gates, retries, security and release state.

Self-protection: MUBA never autonomously edits/merges production source. Repairs use STABLE -> branch -> test -> PR -> green -> merge -> verify.

Infrastructure choices must be re-verified at implementation time. Do not hard-code a future provider solely because it was discussed earlier.