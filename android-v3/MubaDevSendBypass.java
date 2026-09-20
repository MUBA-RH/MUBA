/*
 * One-shot recursion guard for the V3 Android composer hook.
 *
 * A successful translation resumes Telegram's normal send path. That resumed
 * call must bypass translation exactly once, otherwise the hook can recurse.
 * Keep one instance scoped to the chat composer; do not make this global.
 */
package org.muba.devtranslator;

public final class MubaDevSendBypass {
    private boolean bypassNextSend;

    public void arm() {
        bypassNextSend = true;
    }

    public boolean consume() {
        if (!bypassNextSend) {
            return false;
        }
        bypassNextSend = false;
        return true;
    }

    public void clear() {
        bypassNextSend = false;
    }
}
