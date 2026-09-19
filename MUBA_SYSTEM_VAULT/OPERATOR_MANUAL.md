# Operator Manual

Audience: non-specialist DEV assisted by an AI/developer.

To hand off: provide the complete Vault and instruct the receiver to read START_HERE.md and change nothing until current state is reconstructed and the DEV chooses a path.

The AI speaks Turkish to DEV unless requested otherwise; canonical technical material remains English.

For recovery choose RESTORE CURRENT MUBA and follow RECOVERY.md one verified step at a time.
For V2 choose BUILD MUBA V2 / AUTONOMY; first prove stable recovery, then build phases independently. Never begin with a giant rewrite.

Human status target:
GREEN = healthy/no action.
YELLOW = degraded but safe/review needed.
RED = external action paused/failed/DEV action needed.
Daily report = what system did -> what it will do -> failures -> DEV action required.

Never place credentials in repository/Vault. If exposed, rotate them. Every production change that alters documented facts should update current state/release records through the same controlled protocol.