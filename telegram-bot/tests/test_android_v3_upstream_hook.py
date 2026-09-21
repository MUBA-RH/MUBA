from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BYPASS=ROOT/"android-v3"/"MubaDevSendBypass.java"
MAP=ROOT/"docs"/"MUBA_DEV_TRANSLATOR_V3_UPSTREAM_HOOK.md"

def test_bypass_is_one_shot_and_not_global_static_state():
    text=BYPASS.read_text()
    assert "boolean bypassNextSend" in text
    assert "public void arm()" in text
    assert "public boolean consume()" in text
    assert "bypassNextSend = false" in text
    assert "static boolean" not in text

def test_upstream_hook_is_composer_scoped_not_global_send_helper():
    text=MAP.read_text()
    assert "ChatActivityEnterView.ChatActivityEnterViewDelegate.onMessageSend" in text
    assert "Do not hook global" in text
    assert "one-shot bypass" in text
    assert "OFFICIAL_MUBA_CHANNEL_DIALOG_ID" in text
    assert "9552e5541e1274b9557c9832b204dbfcaf44b3dc" in text

def test_private_android_build_inputs_are_not_committed():
    text=MAP.read_text()
    assert "never committed here" in text
    assert "keystore/passwords" in text
