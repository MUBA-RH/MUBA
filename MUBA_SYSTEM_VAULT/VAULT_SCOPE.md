# Vault Scope and Isolation Contract

## Purpose
MUBA System Vault is the large passive backup and continuity package for the entire MUBA project.

It contains:
- the source snapshot present on this Vault branch;
- MUBA identity and official surfaces;
- website structure;
- Telegram Bot API architecture;
- private Assistant;
- Guardian security/management;
- MUBA Studio;
- layered brain/state architecture;
- DEV translator history;
- Android V3/APK architecture;
- GitHub CI/build workflows;
- recovery, handover and portability instructions;
- optional future V2/Autonomy blueprint.

## What the Vault must never do
- It must not run in production.
- It must not be imported by runtime modules.
- It must not alter the webhook.
- It must not change Telegram group permissions.
- It must not activate V2.
- It must not deploy an Android APK.
- It must not overwrite the stable MUBA baseline.
- It must not contain secret values.

## Snapshot rule
The canonical stable-main SHA for the current Vault snapshot is recorded in `RELEASE_MANIFEST.json` and refreshed by **MUBA Vault Auto Sync** after green main validation.

Do not rely on a hard-coded historical SHA elsewhere in the Vault.

## Separation rule
Production lives on main. The Vault lives on a dedicated vault branch. Updating the Vault does not mean modifying production.

## Recovery authority
Vault documents procedures and preserves source. Only the DEV may authorize a restore, migration, V2 activation or project clone.

## Reuse boundary
The Vault is publicly inspectable but not a general reuse license. Creating or adapting a separate project from MUBA's protected implementation requires prior written DEV authorization and a passing permission-gate check. MUBA's own restore path remains separate from third-party/new-project reuse.
