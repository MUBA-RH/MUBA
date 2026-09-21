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
This Vault refresh is based on main commit:
`602ebffe23de7373e7ee513af33dea219fe6deba`

The source tree in this Vault refresh was created from that exact main state before Vault documentation was added.

## Separation rule
Production lives on main. The Vault lives on a dedicated vault branch. Updating the Vault does not mean modifying production.

## Recovery authority
Vault documents procedures and preserves source. Only the DEV may authorize a restore, migration, V2 activation or project clone.
