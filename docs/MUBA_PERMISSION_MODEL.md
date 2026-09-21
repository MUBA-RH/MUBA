# MUBA Permission Model

## Status
MUBA is **source-available, permission-required**.

The public repository exists for transparency, review, continuity and community understanding. Public access is not a general reuse license.

## Ownership boundary
The MUBA Rights Holder reserves rights in MUBA's original project-specific material, including original source code, original selection/arrangement/implementation of the architecture, module organization, integration logic, MUBA System Vault design, documentation and owned project identity material.

Third-party libraries, platforms, APIs, services, trademarks and other third-party materials remain owned and licensed by their respective rights holders.

The policy does not claim ownership of general programming ideas, public standards or third-party technology.

## Allowed without a reuse grant
- View and inspect the public repository.
- Review the implementation for transparency, evaluation and security understanding.
- Use rights that GitHub itself necessarily provides under its platform terms.

## Prior permission required
A separate written MUBA authorization is required before using protected MUBA material to:
- create another project from the MUBA architecture or Vault;
- deploy or operate a separate project based on the MUBA implementation;
- rebrand, port, adapt or repurpose MUBA code/architecture for another project;
- redistribute or commercialize protected MUBA material;
- integrate substantial project-specific MUBA implementation into another system.

## Vault enforcement
The supported new-project path is deny-by-default.

A new-project operator must possess a `MUBA_PERMISSION.json` grant whose canonical SHA-256 fingerprint is listed as an active approval in `muba_authorizations.json` from the official MUBA repository.

Verification command:

```bash
python scripts/muba_permission_gate.py verify --permission MUBA_PERMISSION.json
```

When permission is absent, expired, altered, inactive or not recorded in the official registry, the command exits non-zero and the installation must stop.

The permission template is `MUBA_PERMISSION_TEMPLATE.json`.

## Issuing an authorization
The MUBA Developer controls authorization.

A normal authorized flow is:
1. prepare a permission document from `MUBA_PERMISSION_TEMPLATE.json`;
2. define grantee, project, scope, date and approval reference;
3. calculate its canonical fingerprint:
   ```bash
   python scripts/muba_permission_gate.py fingerprint --permission MUBA_PERMISSION.json
   ```
4. add that exact grant ID + fingerprint to `muba_authorizations.json` with `status: "active"` through the official MUBA repository;
5. preserve the written approval reference;
6. only then run the protected Vault new-project path.

The registry starts empty. Therefore no third-party/new-project use is currently pre-authorized.

## Restore is different
Restoring the official MUBA system from its own recovery snapshot is not a third-party/new-project use and must not be blocked by the new-project permission gate.

V2/autonomy remains a separate explicit DEV choice and still cannot activate automatically.

## Security limit
Because the repository is public, no source-code gate can make copying technically impossible for a determined person who modifies the code.

The gate is therefore designed to:
- make the official supported path fail closed;
- create an explicit permission boundary;
- anchor approved grants to the official repository history;
- make accidental or unapproved supported reuse clearly invalid.

Bypassing or deleting the gate does not create permission under `LICENSE.md`.

## No repository secrets
The permission model deliberately stores no private signing key or other secret in Git/Vault.

If a future public-key signature layer is added, the private signing key must remain outside the repository and Vault.
