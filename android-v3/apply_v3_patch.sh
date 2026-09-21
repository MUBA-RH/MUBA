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
bot_api_dialog_id, api_id, api_hash = sys.argv[2:5]
# GitHub secret uses the Bot API supergroup/channel form (-100...).
# Telegram Android internally addresses a channel dialog as -channel_id.
# Convert once at build time so the runtime gate compares like-for-like IDs.
bot_api_dialog_id_int = int(bot_api_dialog_id)
if bot_api_dialog_id_int <= -1000000000001:
    channel_id = -bot_api_dialog_id_int - 1000000000000
    dialog_id = str(-channel_id)
else:
    dialog_id = bot_api_dialog_id
buildvars = root / "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java"
composer = root / "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java"
translate_controller = root / "TMessagesProj/src/main/java/org/telegram/messenger/TranslateController.java"

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

tc = translate_controller.read_text()
tc_anchor = """        if (!isTranslatable(messageObject)) {
            return;
        }

        if (!isTranslatingDialog(dialogId)) {
"""
tc_hook = f"""        if (!isTranslatable(messageObject)) {{
            return;
        }}

        // MUBA V3: preserve Telegram's native whole-chat translation entry point
        // for the exact MUBA dialog. Premium/translation availability and the
        // server-side hidden flag are still respected; other dialogs are untouched.
        if (dialogId == {dialog_id}L
                && isFeatureAvailable(dialogId)
                && !isTranslateDialogHidden(dialogId)
                && !translatableDialogs.contains(dialogId)) {{
            translatableDialogs.add(dialogId);
            detectedDialogLanguage.put(dialogId, "en");
            AndroidUtilities.runOnUIThread(() ->
                    NotificationCenter.getInstance(currentAccount)
                            .postNotificationName(NotificationCenter.dialogIsTranslatable, dialogId), 50);
        }}

        if (!isTranslatingDialog(dialogId)) {{
"""
if tc_anchor not in tc:
    raise SystemExit("TranslateController translatable anchor missing")
tc = tc.replace(tc_anchor, tc_hook, 1)
translate_controller.write_text(tc)
PY

echo "MUBA V3 composer hook, native chat-translation compatibility patch, and private build inputs applied."
