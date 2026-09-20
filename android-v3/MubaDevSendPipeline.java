/*
 * MUBA DEV Translator V3 — translate-before-send coordinator.
 *
 * This class deliberately does not send messages. The Telegram Android send
 * hook calls prepare(), and only the success callback may continue through
 * Telegram's existing normal user-message send path.
 */
package org.muba.devtranslator;

import org.telegram.tgnet.TLRPC;

import java.util.function.Consumer;

public final class MubaDevSendPipeline {
    private MubaDevSendPipeline() {}

    public static boolean prepare(
            int account,
            long currentDialogId,
            long officialMubaChannelDialogId,
            boolean devTranslationEnabled,
            CharSequence draft,
            Consumer<TLRPC.TL_textWithEntities> continueNormalTelegramSend,
            Consumer<String> keepDraftAndShowError
    ) {
        if (!MubaDevTranslationGate.shouldTranslate(
                currentDialogId,
                officialMubaChannelDialogId,
                devTranslationEnabled
        )) {
            return false;
        }

        MubaDevTranslateBeforeSend.translate(
                account,
                draft,
                "en",
                continueNormalTelegramSend,
                keepDraftAndShowError
        );
        return true;
    }
}
