from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BOOT=ROOT/"android-v3"/"bootstrap_upstream.sh"
HELPER=ROOT/"android-v3"/"MubaDevTranslateBeforeSend.java"
GATE=ROOT/"android-v3"/"MubaDevTranslationGate.java"
PIPELINE=ROOT/"android-v3"/"MubaDevSendPipeline.java"

def test_v3_is_isolated_from_production_runtime():
    text=BOOT.read_text()
    assert "telegram-bot/" in text
    assert "DrKLO/Telegram.git" in text

def test_helper_has_fail_closed_translation_flow():
    text=HELPER.read_text()
    assert "TL_messages_translateText" in text
    assert "onFailure" in text
    assert "onSuccess" in text
    assert "sendMessage" not in text

def test_official_channel_gate_is_exact_and_fail_closed():
    text=GATE.read_text()
    assert "officialMubaChannelDialogId != 0L" in text
    assert "currentDialogId == officialMubaChannelDialogId" in text
    assert "devTranslationEnabled" in text
    assert "@MUBA_RH" not in text

def test_pipeline_only_translates_after_gate():
    text=PIPELINE.read_text()
    assert "MubaDevTranslationGate.shouldTranslate" in text
    assert "MubaDevTranslateBeforeSend.translate" in text
    assert '"en"' in text
    assert "sendMessage" not in text
    assert "return false" in text

def test_no_secret_values_are_embedded():
    combined="".join(p.read_text() for p in (BOOT,HELPER,GATE,PIPELINE))
    for forbidden in ("MUBA_DEV_SESSION=", "TELEGRAM_API_HASH=", "TELEGRAM_API_ID=", "-1004485415245"):
        assert forbidden not in combined
