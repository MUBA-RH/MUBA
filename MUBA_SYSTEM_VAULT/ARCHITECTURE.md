# Architecture
Current: GitHub Pages + Telegram webhook runtime containing integration/router, Guardian, private Assistant, Studio and layered local brain.

Future V2 is an orchestration plane above stable modules:
DEV -> Truth Registry -> Core/Orchestrator -> Persistent Memory + Story Engine + Scheduler/Jobs + Studio/Validator + Publisher adapters.
An independent Watchdog/Health plane observes the system.

Safety invariants:
1. Stable production remains runnable while V2 is built.
2. Vault is never imported at runtime.
3. Creative AI cannot authoritatively set CA, listing time, official links, partnership status, DEV authority or security policy.
4. External actions use explicit states: PLANNED -> PREPARED -> VALIDATED -> QUEUED -> SENT -> VERIFIED; failures are recorded.
5. Provider acknowledgement is not silently assumed.
6. Component failures are isolated.
7. Retries are bounded; repeated failure opens a circuit breaker.
8. Watchdog is independent of the decision engine.
9. Production never self-edits/self-merges.
10. Credentials remain outside source control.

Blue/Green: BLUE is verified production. GREEN is candidate V2. GREEN gets external authority only after tests, shadow/canary verification and explicit promotion. BLUE remains recoverable.