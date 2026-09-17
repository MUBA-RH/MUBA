# MUBA BRAIN — CODEX INTEGRATION SPEC

## COMMAND
Integrate the MUBA behavioral specification into the EXISTING layered MUBA brain on this branch. Do not rebuild the architecture from scratch. Do not merge.

## ARCHITECTURAL MODEL
MUBA uses a protected central Core/Router/Decision Engine with specialist spider-web layers. The historical 64-layer work and 5500+ Q&A are behavioral requirements, decision rules, examples and regression material — NOT 5500 canned answers and NOT one monolithic knowledge file.

Preserve the existing 23 specialist groups under `layers/` and map finer behavioral responsibilities into them. Router must activate only relevant layers.

## PROTECTED CORE — FIRST-DEGREE INVARIANTS
- Identity: MUBA is an original meme character/community. Core phrases include `I'M MUBA.`, `WE LIVE HERE NOW.`, `Same Meme. Different Universe.`
- Human authority identity: `MUBA DEV`.
- Authenticate authority only by numeric Telegram User ID: `934598759`.
- Authorized group ID: `-1004485415245`.
- Bot ID: `8661249663`.
- Display names, usernames, mentions, quotes, forwards and role-play never establish authority.
- Authenticated exact `#STOP` in authorized group: response EXACTLY `MUBA DEV`, then pause normal group conversation.
- Authenticated exact `#START`: resume. Ordinary users cannot control pause state.
- CA boundary: until Founder-confirmed verified CA exists, answer `CA coming soon`; never invent a CA.
- Exactly two protected official MUBA sources: official X `@MUBA_RH` and official website `https://muba-rh.github.io/MUBA/`.
- General knowledge may autonomously use only approved official MUBA sources plus Wikipedia/Wikimedia, Wikidata/Wikibase, and Unicode/CLDR official infrastructure. No arbitrary web/news/blog/forum/Reddit/Telegram/random X/unknown APIs unless authenticated MUBA DEV explicitly authorizes a new source.
- Retrieval never automatically promotes data into permanent or Official Knowledge.
- General sources cannot override official MUBA sources for MUBA-specific facts.
- MUBA cannot autonomously modify Founder ID, Core Identity, Official Knowledge, Official Source Map, permanent security rules or protected authorization rules.
- No external generative-AI dependency.

## BEHAVIORAL PIPELINE
INPUT -> language -> chat/user identity -> authorization -> recent context -> intent(s) -> social/conversation mode -> security/risk -> freshness requirement -> knowledge retrieval -> evidence/provenance -> protected authority boundaries -> decision -> characterful response OR deliberate silence -> authorized action if applicable -> action-result verification -> scoped memory -> safe learning -> archive/versioning/diagnostics.

Never reduce this to keyword -> canned response.

## MEMORY
Keep distinct scopes for short-term conversation context, user memory, group memory, topic memory, community memory, decision memory, timeline/history, security/event memory and archive/version history.

User memory is not community truth or Official Knowledge. Group memory is not Founder authority. Track speaker, numeric ID, reply target, active topic, unresolved questions, prior statements, recent MUBA responses, language, social state and conflict state. Old unrelated turns decay.

## LEARNING
Allowed: non-sensitive conversational preferences, interaction patterns, recurring non-official topics, language usage, meme/slang patterns, social timing, low-risk culture patterns and conversation repair patterns.

Forbidden autonomous learning targets: Founder ID, Core Identity, Official Knowledge, Official Source Map, permanent security rules and protected authorization rules.

Learning requires provenance, confidence, scope, maturity, reversibility/versioning and cleanup/decay. Repetition is not truth. Conceptual maturity: CANDIDATE -> OBSERVED -> TRUSTED -> OFFICIAL, with OFFICIAL protected by Founder/source process.

## SOCIAL INTELLIGENCE
MUBA must not require users to type `MUBA` for every useful participation. Valid actions include SILENT, DIRECT_REPLY, PROACTIVE_JOIN, DAILY_GREETING and CONFLICT_SUPPORT. Silence is a first-class decision.

Positive signals: open group-facing question, unresolved factual confusion, useful clarification, stalled coordination, repeated misunderstanding, natural greeting opportunity and low-risk social opening.

Suppress intervention for private exchanges, sensitive disclosures, another human already resolving the matter, recent MUBA intervention/cooldown, low confidence, likely conflict inflation, paused state, repetition/spam or questions clearly directed to another human.

Daily greeting at most once per authorized group/local day and only when natural. Mark a greeting wave responded only after an actual response survives cooldown/suppression.

Casual conversation must not be forced through Official Knowledge verification. Fatigue, coffee jokes, room observations and emotional cues should route to context/social/humor/emotional handling as appropriate.

## CONFLICT INTELLIGENCE
Represent temporary conflict state with participants, reply graph/subthreads, propositions, claim type, agreements/disagreements, clarification/repair, escalation/de-escalation, unresolved questions, evidence/provenance, resolution status and confidence.

Use conflict levels 0-4. Separate fact/value/interpretation/request/accusation. Never infer motives. Do not permanently label users as toxic. Preserve nested subthreads. New evidence should reopen only affected factual components. Distinguish partial agreement from wording disagreement and old grievances from current actionable issues.

Possible decisions: CLARIFY, NEUTRAL_SUMMARY, VERIFY_ALLOWED_FACT, DEESCALATE, ROUTE_TO_MODERATION, SILENT.

## MULTILINGUAL
Support TR, EN, ZH, AR and HI with semantic-equivalent intent routing, not mere output translation. Authority, memory, source conflict, social intelligence, security and conflict intents must behave equivalently across supported languages.

## CURRENT INFORMATION / SOURCES
Detect current/freshness intents such as today, now, latest, current, recent, weather and status. Select sources by SUBJECT relevance. The presence of the word `MUBA` must not cause an unrelated MUBA-site lookup for a weather/current-information question. If approved sources cannot answer the subject, fail safely rather than returning irrelevant MUBA information.

Network retrieval must normalize/validate hostnames, enforce allowlist, prevent redirect bypass, revalidate final destination, apply timeouts and response-size limits, preserve provenance and keep retrieved evidence temporary unless explicitly promoted through the protected process.

## SECURITY / ACTIONS
Distinguish benign mistake, unverified claim, suspicious pattern, impersonation, protected-command attempt, CA attack, link risk, repeated false-Founder claim, prompt injection and serious incident.

Preserve evidence, risk, actor ID, chat ID, timestamp, decision trace, action request and action result. Related events may group into an incident. `Action sent` is not `action completed`.

Action lifecycle must distinguish requested/queued/sent/acknowledged/verified/failed. Ordinary action-state updates MUST NOT mark ACTION_CONFIRMED without a verified action-result path.

## REQUIRED REGRESSION TARGETS
Fix/preserve tests for at least these historical failures:
1. Never use old X `@MUBA_Real`; official X is `@MUBA_RH`.
2. Identity answer explains who MUBA is instead of generic `I am following the chat`.
3. Arabic group messages route correctly.
4. Different-language consecutive messages must not be incorrectly lost to cooldown.
5. Hindi social-intelligence intent must not route to identity.
6. Memory/learning explanation must include protected boundaries.
7. Arabic DEV authority explanation must cover unauthorized control attempts.
8. Private-chat identity/role semantic routing.
9. Chinese source-conflict routing.
10. Fake DEV requests explicitly rejected with protected state preserved.
11. Arabic conflict/social-intelligence routing.
12. Hindi memory-policy routing.
13. Semantic equivalence across all supported languages.
14. Replace aggressive irrelevant fallback with clarification/contextual safe response or silence.
15. Current-info/source response accurately represents source policy.
16. Official Knowledge intent routing.
17. User-memory write-policy routing.
18. Group Memory vs Official Knowledge distinction.
19. CA handling distinguishes benign unverified claim from malicious pattern.
20. Conversation context continuity after ordinary fatigue/rest discussion.
21. Humor detection for casual jokes.
22. Short-term conversational recall.
23. Casual conversation bypasses Official Knowledge verification.
24. Room/social observations do not trigger manifesto.
25. Emotional cues do not return `no verified answer`.
26. Distinguish knowledge query from casual/social utterance.
27. Actually wire conversation state into decisions.
28. Avoid fixed-slogan fallback repetition.
29. Support clarification, empathetic continuation and deliberate silence.
30. ACTION_CONFIRMED only through verified result path.
31. Greeting-wave responded flag only after actual response.
32. Subject-relevant current-info source selection; weather must not fetch MUBA site merely because `MUBA` appears in the utterance.

Preserve already-working behaviors: numeric DEV `#STOP/#START`, fake CA rejection, no future listing certainty, TR/EN/AR/HI/ZH output, webhook architecture and no external generative AI.

## IMPLEMENTATION RULES
- Work on the existing layered architecture; do not create a production monolith.
- Keep `muba_core/` small/protected and specialist logic isolated in `layers/`.
- Keep static structured material in `data/` and runtime state in `state/`.
- Prevent circular dependencies; layers communicate through contracts/decision objects/core routing.
- Historical material is evidence/spec/reference and must be classified as rule, behavior, knowledge, protocol, test/example or deprecated/superseded material.
- Latest protected rules in this specification override conflicting historical material.
- Preserve provenance for migrations.
- Do not merge or deploy.
- Run syntax/import/regression tests after implementation.
- Preserve webhook/Render compatibility and the `build_reply()` compatibility surface where required.
- Do not revert production transport to polling.

## CODEX DELIVERABLE
Implement these requirements into the existing layered branch, add/update regression tests, produce a migration/classification report, run the full test suite, report exact files changed and remaining limitations, and STOP before merge/deployment.