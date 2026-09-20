from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BOOT=ROOT/"android-v3"/"bootstrap_upstream.sh"
HELPER=ROOT/"android-v3"/"MubaDevTranslateBeforeSend.java"

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

def test_no_secret_values_are_embedded():
    combined=BOOT.read_text()+HELPER.read_text()
    for forbidden in ("MUBA_DEV_SESSION=", "TELEGRAM_API_HASH=", "TELEGRAM_API_ID="):
        assert forbidden not in combined
