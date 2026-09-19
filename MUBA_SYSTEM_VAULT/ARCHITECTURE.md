# Architecture and Safety Boundaries

Current: GitHub Pages serves index.html. The Telegram runtime integrates Guardian, private Assistant, Studio and the local layered MUBA brain.

Future Autonomy is an orchestration plane above stable modules, not a rewrite.

Target:
DEV -> Truth Registry -> MUBA Core/Orchestrator -> Persistent Memory / Story Engine / Scheduler+Job Engine / Studio+Validator / Publisher adapters.
An independent Watchdog/Health plane observes the system.

Safety invariants:
1. Stable production remains runnable while V2 is built.
2. Vault documentation is never a runtime dependency.
3. Creative AI is never authoritative for CA, listing time, official links, partnership status, DEV authority or security policy.
4. External actions use state machines: PLANNED -> PREPARED -> VALIDATED -> QUEUED -> SENT -> VERIFIED, or FAILED.
5. Provider acknowledgement is required where possible; do not infer success.
6. Failures are isolated by component.
7. Retries are bounded with backoff and circuit breakers.
8. Watchdog is independent of the decision engine.
9. Production code never self-modifies or self-merges.
10. Credentials stay outside source control.

Blue/Green: BLUE is verified production. GREEN is V2 candidate. GREEN gains external authority only after tests, shadow, canary, health checks and explicit promotion. BLUE remains recoverable until rollback is exercised.