# PR #6 conflict-resolution report

## Resolution scope

The merge resolution preserves the layered MUBA implementation as the runtime
authority while retaining production webhook configuration and historical source
documents as non-runtime reference material. No legacy monolithic brain is
imported, copied into the core, or selected by either transport.

The resolved runtime boundaries are:

* `muba_core/` remains the protected Core, Router, Decision Engine, contracts,
  action lifecycle, and memory firewall.
* `layers/` remains the 23-layer specialist graph discovered only by the registry.
* `muba_brain.py` remains the stable `build_reply()` compatibility adapter.
* `bot_mention.py` remains the production webhook transport and retains the
  `TELEGRAM_BOT_TOKEN`, `RENDER_EXTERNAL_URL`, `PORT`, and
  `MUBA_WEBHOOK_SECRET` environment configuration.
* `bot.py` and `webhook.py` remain thin compatibility transport modules backed by
  the layered adapter; neither contains an AI client or monolithic brain.
* `codex-input/MUBA_BRAIN.txt`, when supplied on the target branch, is source and
  behavioral reference material only. It must never be imported by runtime code.

## Protected behavior retained

The resolution retains numeric MUBA DEV authentication, exact `#STOP`/`#START`,
authorized-group gating, the official-source map, the unverified-CA boundary,
scoped memory and learning protection, deliberate silence, multilingual routing,
structured conflict/security evidence, subject-relevant retrieval, and verified
action results. Architecture regressions now explicitly test these merge
boundaries and reject unresolved conflict markers in production files.

## Validation and merge readiness

The regression suite covers the layered architecture and the new conflict guards.
Syntax compilation, import smoke checks, the complete unit suite, and
`git diff --check` must all pass before the PR is merged. No merge or deployment is
part of this resolution commit.

## Rollback instructions

If this conflict-resolution commit causes a regression, revert only that commit:

```bash
git revert <conflict-resolution-commit-sha>
```

Then rerun:

```bash
python -m compileall -q telegram-bot
PYTHONPATH=telegram-bot python -c "import muba_brain; assert callable(muba_brain.build_reply)"
cd telegram-bot && python -m unittest discover -s tests -v
```

Do not restore `muba_brain_v1.py`, `muba_brain_v2*.py`, or
`MUBA_MASTER_BRAIN_FINAL.py` as production entry points. Do not roll back the
webhook environment configuration from the target branch.
