# CREATE NEW PROJECT FROM MUBA ARCHITECTURE

Status: **LOCKED UNTIL AUTHORIZED**

This is the official Vault entry point for creating, cloning, adapting or rebranding a project from the MUBA architecture.

## Step 0 — authorization comes first

Do not begin installation or configuration.

Do not ask for:
- Telegram IDs or bot tokens;
- X account details;
- GitHub destinations;
- provider/API credentials;
- domains;
- deployment targets;
- token/CA data;
- branding replacements.

First require the approved permission file and run:

```bash
python scripts/muba_permission_gate.py verify --permission MUBA_PERMISSION.json
```

### Result
- **Exit 0 / AUTHORIZATION VERIFIED** → read `PROJECT_PORTABILITY.md` and continue only inside the approved grant scope.
- **Any other result** → **STOP. INSTALLATION MUST NOT PROCEED.**

No permission is bundled with this Vault by default.

Public access to the repository or Vault archive does not grant reuse rights.

For policy details read:
1. `PERMISSION_REQUIRED.md`
2. `/LICENSE.md`
3. `/docs/MUBA_PERMISSION_MODEL.md`
4. `PROJECT_PORTABILITY.md`
