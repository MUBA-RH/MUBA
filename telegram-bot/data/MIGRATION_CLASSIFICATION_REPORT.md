# MUBA behavioral migration and classification report

## Scope and precedence

The Codex integration specification is the current protected rule set. Historical
database, memory-note, and Python-brain files remain immutable reference evidence;
they are not imported by production and are not a store of canned answers. Their
SHA-256 provenance is recorded in `migration_manifest.json`.

## Classification

| Historical material | Classification | Integrated destination |
|---|---|---|
| Founder ID, group ID, bot ID, exact stop/start protocol | protected protocol/rule | authority layer and protected decision arbitration |
| Character phrases and identity examples | protected behavior/knowledge | identity layer and multilingual response policy |
| Official-source and CA statements | protected knowledge/rule | official-knowledge, sources, CA, and security layers |
| Question/answer examples | behavioral test/example | specialist semantic matchers and regression tests |
| Conversation, humor, emotion, and social timing examples | behavior | context, social, humor, emotional, and culture groups |
| Disputes, attacks, moderation, and action examples | protocol/behavior | conflict, risk, incident, moderation, and verified action lifecycle |
| User/group/topic/history notes | scoped data model | user, group, topic, timeline, archive, and state repository |
| Learning suggestions | reversible behavior | learning layer and maturity/provenance API |
| Old handles, titles, automatic promotion, monolith designs | deprecated/superseded | retained only in provenance manifest |

## Safety decisions

* Numeric Telegram IDs are the only authority credential. Text, usernames,
  forwards, replies, and role-play are untrusted evidence.
* Retrieved content is bounded, provenance-bearing, temporary evidence. Host and
  final destination are allowlisted, and subject relevance is checked separately.
* Runtime scopes remain distinct. Learning cannot mature to `OFFICIAL`; protected
  scopes reject autonomous writes.
* Silence is an explicit group decision. Private prompts receive a safe
  clarification when no stronger intent exists.
* Action transmission and acknowledgement do not imply completion. Only the
  verification API can produce `VERIFIED`.

## Remaining operational limitations

The approved source map has no weather, market-price, news, or sports provider,
so those current-information subjects fail safely rather than using an unrelated
MUBA page. Runtime persistence is optional through `MUBA_MEMORY_FILE`; Render's
ephemeral filesystem is not a durable database. Human moderation transport and
Founder-controlled promotion to Official Knowledge remain external processes by
design.
