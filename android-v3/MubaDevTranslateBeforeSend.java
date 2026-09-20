/*
 * MUBA DEV Translator V3 integration helper.
 *
 * Staging source for the isolated Telegram Android fork. This file is not loaded
 * by the production MUBA bot and deliberately contains no credentials.
 *
 * Telegram Android is GPL-2.0-or-later. When integrated into the fork, keep the
 * fork source available and comply with upstream licensing/branding requirements.
 */
package org.muba.devtranslator;

import org.telegram.messenger.AccountInstance;
import org.telegram.tgnet.ConnectionsManager;
import org.telegram.tgnet.TLObject;
import org.telegram.tgnet.TLRPC;

import java.util.ArrayList;
import java.util.function.Consumer;

public final class MubaDevTranslateBeforeSend {
    private MubaDevTranslateBeforeSend() {}

    public static void translate(
            int account,
            CharSequence draft,
            String targetLanguage,
            Consumer<TLRPC.TL_textWithEntities> onSuccess,
            Consumer<String> onFailure
    ) {
        if (draft == null || draft.toString().trim().isEmpty()) {
            onFailure.accept("EMPTY_DRAFT");
            return;
        }
        if (targetLanguage == null || targetLanguage.trim().isEmpty()) {
            onFailure.accept("EMPTY_TARGET_LANGUAGE");
            return;
        }

        TLRPC.TL_messages_translateText request = new TLRPC.TL_messages_translateText();
        request.flags |= 2;
        request.text = new ArrayList<>();

        TLRPC.TL_textWithEntities input = new TLRPC.TL_textWithEntities();
        input.text = draft.toString();
        input.entities = new ArrayList<>();
        request.text.add(input);
        request.to_lang = targetLanguage;

        ConnectionsManager.getInstance(account).sendRequest(request, (response, error) -> {
            if (error != null) {
                onFailure.accept(error.text == null ? "TRANSLATE_FAILED" : error.text);
                return;
            }
            if (!(response instanceof TLRPC.TL_messages_translateResult)) {
                onFailure.accept("UNEXPECTED_TRANSLATE_RESPONSE");
                return;
            }
            TLRPC.TL_messages_translateResult result = (TLRPC.TL_messages_translateResult) response;
            if (result.result == null || result.result.isEmpty()) {
                onFailure.accept("EMPTY_TRANSLATION");
                return;
            }
            onSuccess.accept(result.result.get(0));
        });
    }
}
