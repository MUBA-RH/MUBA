# Authorized Project Portability / Clone and Rebrand

This architecture may seed another isolated project, for example XXX, **only after explicit authorization** and without renaming or damaging MUBA production.

## Permission gate — mandatory
DEV must explicitly choose CREATE A NEW PROJECT FROM THIS ARCHITECTURE **and** provide prior written authorization for that reuse.

Before requesting any new-project IDs, tokens, credentials, repository destinations or deployment configuration, verify the authorization:

```bash
python scripts/muba_permission_gate.py verify --permission MUBA_PERMISSION.json
```

The permission file must match an active SHA-256 approval fingerprint in the official `muba_authorizations.json` registry.

If the command exits non-zero:
- stop immediately;
- do not create a repository;
- do not configure a bot, domain, provider or deployment;
- do not adapt/rebrand the MUBA implementation;
- do not request secret configuration;
- explain that prior written authorization from the MUBA Developer is required.

A public Vault ZIP, fork, clone or visible source tree is not authorization.

After a successful check, continue only within the project, grantee, scope and time limits of that approved permission grant.

## New project inputs
Request and verify, as applicable:
- new project display name and canonical slug;
- token/project information;
- GitHub repository destination;
- X handle/page and X account/user ID;
- Telegram DEV numeric user ID;
- Telegram bot username and numeric bot ID;
- Telegram bot token only at secret-configuration time;
- Telegram official channel ID/link;
- Telegram authorized group ID;
- website URL/domain/repository;
- runtime/deployment destination;
- media/AI provider configuration;
- official links and protected truth values;
- CA/listing facts only if explicitly supplied and verified by DEV.

## Isolation
- Create a separate repository/profile/deployment.
- Do not rename MUBA in place.
- Do not reuse MUBA production credentials.
- Do not allow MUBA IDs/links to leak into the new project.
- Preserve the MUBA Vault and baseline unchanged.

## Code standard
The new project should also use English as canonical source/technical language unless DEV explicitly establishes a different engineering standard.

## Testing
Tests must verify that project-specific IDs, official links, authority IDs and brand truth are parameterized and isolated.
