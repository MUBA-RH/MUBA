# MUBA Operator Manual

Audience: a future AI/developer assisting a non-specialist DEV.

## First behavior
Speak Turkish to DEV by default.
Keep code and canonical technical documentation in English.

## Never begin by rebuilding
First inspect:
- main SHA;
- Vault SHA;
- open/merged PRs;
- workflows/tests;
- current provider/runtime evidence.

Then ask DEV which path is wanted.

## Normal maintenance
Follow:
BAŞLA 🔥 MERGE 🟢 SİSTEMİ KORU 🛡️ STABİL 🔒

Report facts, not assumptions.

## Telegram maintenance
Preserve:
- numeric DEV authority;
- authorized group boundary;
- START/STOP semantics;
- Assistant/Guardian separation;
- five-language Assistant behavior;
- CA non-invention rule.

## Android maintenance
Treat Android V3 as an isolated client project. Never solve Android translation by modifying production Guardian/Assistant unless DEV explicitly requests a separate integration and safety review.

## Vault maintenance
Vault remains on its dedicated branch and is refreshed automatically after green `main` updates by MUBA Vault Auto Sync. It is documentation/recovery/source snapshot, not a deployment target.

## New-project authorization
If the requested path is CREATE A NEW PROJECT FROM THIS ARCHITECTURE, do not begin setup from a public Vault copy alone.

Require `MUBA_PERMISSION.json` and run:

```bash
python scripts/muba_permission_gate.py verify --permission MUBA_PERMISSION.json
```

A failed or missing authorization is a hard stop. Do not collect secrets, create infrastructure or adapt MUBA for the new project until the gate succeeds.

## Secret handling
Never write secrets into:
- source files;
- Vault docs;
- commit messages;
- PR descriptions;
- logs/screenshots.
