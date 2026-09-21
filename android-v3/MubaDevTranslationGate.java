/*
 * MUBA DEV Translator V3 — official-channel safety gate.
 *
 * Credential-free source for the isolated Telegram Android fork.
 * Translation must NEVER become a global Telegram behavior.
 */
package org.muba.devtranslator;

public final class MubaDevTranslationGate {
    private MubaDevTranslationGate() {}

    /**
     * Telegram channel dialog ids use the -100... form. The exact official
     * channel id is supplied by the isolated Android build configuration.
     * A missing/zero id fails closed.
     */
    public static boolean shouldTranslate(
            long currentDialogId,
            long officialMubaChannelDialogId,
            boolean devTranslationEnabled
    ) {
        return devTranslationEnabled
                && officialMubaChannelDialogId != 0L
                && currentDialogId == officialMubaChannelDialogId;
    }
}
