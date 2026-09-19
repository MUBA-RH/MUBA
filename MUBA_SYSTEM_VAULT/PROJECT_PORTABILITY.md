# Project Portability / Clone & Rebrand
Purpose: allow this architecture to seed a separate project (example: XXX) without modifying MUBA production.

The receiving AI must first ask whether DEV wants:
A) RESTORE CURRENT MUBA
B) BUILD MUBA V2 / AUTONOMY
C) CREATE A NEW PROJECT FROM THIS ARCHITECTURE

For C, create a new isolated repository/deployment/profile. Do not rename MUBA in-place and do not reuse MUBA production credentials.

Collect and verify the new project's configuration one item at a time:
- project display name and canonical project key/slug
- GitHub owner/repository destination
- Telegram DEV numeric user ID
- Telegram bot username and bot ID
- Telegram bot token, requested only when needed and entered into provider secret/environment storage, never Vault/Git
- Telegram authorized main group ID
- Telegram official channel username/ID/link as applicable
- website repository/domain/public URL
- X account handle and X account/user ID
- X API credentials/tokens if automated X actions are requested and the current official API requires them; store only in secret/environment storage
- deployment/runtime destination and required credentials
- media/AI provider credentials if Studio/media is enabled
- official links and protected truth values
- official CA/listing facts only when DEV explicitly provides and verifies them

Parameterize identity/IDs/URLs rather than blind search-and-replace. Tests must prove no MUBA IDs, URLs, credentials, authority IDs, official links or brand-specific protected truth leak into the new runtime.

Never place credential values in documentation, commits, PR bodies, logs or screenshots. Documentation may list required secret variable names and where DEV must configure them.

The new project follows the same STABLE -> branch -> tests -> PR -> green -> merge -> verify -> STABLE protocol. MUBA remains independently deployable throughout.