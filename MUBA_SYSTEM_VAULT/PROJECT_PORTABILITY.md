# Project Portability / Clone & Rebrand

Purpose: allow this architecture to seed a separate project (example: XXX) without modifying MUBA production.

The receiving AI must first ask whether DEV wants:
A) RESTORE CURRENT MUBA
B) BUILD MUBA V2 / AUTONOMY
C) CREATE A NEW PROJECT FROM THIS ARCHITECTURE

For C, create a new isolated repository, deployment and project profile. Do not rename MUBA in place. Do not reuse MUBA production credentials.

Collect and verify the new project's configuration one item at a time:
- project display name and canonical project key/slug
- GitHub owner/repository destination
- Telegram DEV numeric user ID
- Telegram bot username and bot numeric ID
- Telegram bot token, requested only when needed and entered directly into provider secret/environment storage; never store the value in Vault/Git
- Telegram authorized main group ID
- Telegram official channel username/ID/link as applicable
- website repository/domain/public URL
- X account handle and X account/user ID
- X API credentials/tokens when automated X actions are requested and the current official API requires them; request them only at the configuration step and store them only in secret/environment storage
- deployment/runtime destination and required credentials
- media/AI provider credentials when Studio/media is enabled
- official links and protected truth values
- official CA/listing facts only when DEV explicitly provides and verifies them

Identity, IDs and URLs must be parameterized through a project profile rather than blind search-and-replace. Tests must prove that MUBA-specific IDs, URLs, credentials, authority IDs, official links and protected brand truth do not leak into the new project's runtime.

Never place credential values in documentation, commits, PR bodies, logs or screenshots. The Vault may document required environment-variable names and where the DEV must configure them.

The new project follows the same STABLE -> branch -> tests -> PR -> green -> merge -> verify -> STABLE protocol. MUBA remains independently deployable throughout. V2 is never activated without its own tests, shadow/canary checks where applicable, and explicit DEV promotion.
