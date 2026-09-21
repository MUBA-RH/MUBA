# MUBA Telegram System

## System separation
MUBA Telegram has multiple roles that must not be collapsed into one generic bot.

### 1. Main group Guardian
Guardian protects and manages the designated MUBA main group.

DEV commands:
- #START
- #STOP
- #STATUS
- #GUARDIAN
- #SECURITY
- #LOCKDOWN
- #NORMAL
- #WARN
- #MUTE
- #UNMUTE
- #BAN
- #UNBAN <user_id>
- #DELETE
- #HELP

Only the configured numeric MUBA DEV ID is authorized to control Guardian. Unauthorized # control attempts are not accepted.

START/STOP meaning:
- #STOP = pause Guardian runtime protection after DEV command handling and close the group according to the current Telegram permission implementation.
- #START = resume Guardian protection and restore the configured community posting permissions.
- DEV management commands remain available while paused.
- Repeated transitions such as START → STOP → STOP → START must remain deterministic.

### 2. Private MUBA Assistant
The private Assistant is the MUBA knowledge, culture and interaction space. It is multilingual and MUBA-domain constrained.

Current five languages:
- English
- Turkish
- Chinese
- Arabic
- Hindi

The Assistant must not invent:
- team identities;
- exchange/listing facts;
- partnerships;
- secret plans;
- roadmap dates;
- CA values;
- price predictions.

### 3. Guardian violation reporting
Successful DEV commands should not spam the DEV with reports.

Actual user violations may be privately reported with:
- violation/event type;
- action applied;
- Telegram username/display name when resolvable;
- numeric user ID;
- strike count when applicable;
- timestamp/detail.

Violation history is categorized and can be browsed with previous/next buttons.

Persistence warning: the history is stored through the MUBA state repository. If production uses MemoryRepository, a process restart clears it. Durable history requires a verified persistent `MUBA_MEMORY_FILE`/storage configuration. Never claim cross-restart durability without verifying that configuration.

### 4. MUBA Studio
Studio is entered from Assistant and supports content/media creation. It does not own security authority or official truth.

### 5. Main-group Assistant separation
Normal group chatter is not the same as private Assistant interaction. Guardian owns main-group policy. Private Assistant is the intended place for MUBA knowledge exploration.

## Source locations
- telegram-bot/bot_mention.py
- telegram-bot/guardian.py
- telegram-bot/assistant_mode.py
- telegram-bot/assistant_extras.py
- telegram-bot/muba_daily.py
- telegram-bot/muba_studio.py
- telegram-bot/muba_brain.py
- telegram-bot/muba_core/
- telegram-bot/layers/
- telegram-bot/state/
- telegram-bot/tests/

## Development rule
Telegram changes follow the same permanent protocol:
BAŞLA 🔥 → isolated branch → relevant tests → green PR → merge → production verification → STABİL 🔒.
