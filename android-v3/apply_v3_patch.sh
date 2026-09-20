#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:?Telegram source root required}"
: "${MUBA_OFFICIAL_DIALOG_ID:?MUBA_OFFICIAL_DIALOG_ID required}"
: "${TELEGRAM_API_ID:?TELEGRAM_API_ID required}"
: "${TELEGRAM_API_HASH:?TELEGRAM_API_HASH required}"

[[ "$MUBA_OFFICIAL_DIALOG_ID" =~ ^-?[0-9]+$ ]] || { echo "::error::Invalid MUBA_OFFICIAL_DIALOG_ID"; exit 2; }
[[ "$TELEGRAM_API_ID" =~ ^[0-9]+$ ]] || { echo "::error::Invalid TELEGRAM_API_ID"; exit 2; }
[[ "$TELEGRAM_API_HASH" =~ ^[0-9a-fA-F]+$ ]] || { echo "::error::Invalid TELEGRAM_API_HASH"; exit 2; }

python3 - "$ROOT" "$MUBA_OFFICIAL_DIALOG_ID" "$TELEGRAM_API_ID" "$TELEGRAM_API_HASH" <<'PY'
from pathlib import Path
import re, sys

root = Path(sys.argv[1])
dialog_id, api_id, api_hash = sys.argv[2:5]
buildvars = root / "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java"
composer = root / "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java"

bv = buildvars.read_text()
bv2, n1 = re.subn(r'public static int APP_ID = \d+;', f'public static int APP_ID = {api_id};', bv, count=1)
bv3, n2 = re.subn(r'public static String APP_HASH = "[^"]*";', f'public static String APP_HASH = "{api_hash}";', bv2, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit("BuildVars API placeholders not found exactly once")
buildvars.write_text(bv3)

src = composer.read_text()
field_anchor = "    public boolean sendMessage() {"
field = """    private final org.muba.devtranslator.MubaDevSendBypass mubaDevSendBypass = new org.muba.devtranslator.MubaDevSendBypass();

"""
if field_anchor not in src:
    raise SystemExit("composer sendMessage anchor missing")
src = src.replace(field_anchor, field + field_anchor, 1)

anchor = """            if (checkPremiumAnimatedEmoji(currentAccount, dialog_id, parentFragment, null, message)) {
                return;
            }
"""
hook = f"""            if (!mubaDevSendBypass.consume()) {{
                final CharSequence mubaOriginalDraft = message;
                if (org.muba.devtranslator.MubaDevSendPipeline.prepare(
                        currentAccount,
                        dialog_id,
                        {dialog_id}L,
                        true,
                        mubaOriginalDraft,
                        translated -> org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> {{
                            if (messageEditText == null) {{
                                return;
                            }}
                            messageEditText.setText(translated.text);
                            messageEditText.setSelection(messageEditText.length());
                            mubaDevSendBypass.arm();
                            sendMessageInternal(notify, scheduleDate, scheduleRepeatPeriod, payStars, false);
                        }}),
                        error -> org.telegram.messenger.AndroidUtilities.runOnUIThread(() ->
                                android.widget.Toast.makeText(getContext(), "MUBA translation failed. Message not sent.", android.widget.Toast.LENGTH_SHORT).show())
                )) {{
                    return;
                }}
            }}
{anchor}"""
if anchor not in src:
    raise SystemExit("composer text-send anchor missing")
src = src.replace(anchor, hook, 1)
composer.write_text(src)
PY

echo "MUBA V3 composer hook and private build inputs applied."
