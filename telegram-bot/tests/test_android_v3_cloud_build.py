from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WF=(ROOT/".github/workflows/muba-v3-android-cloud-build.yml").read_text()
DOC=(ROOT/"docs"/"MUBA_DEV_TRANSLATOR_V3_PHONE_ONLY_CLOUD_BUILD.md").read_text()

def test_cloud_build_is_manual_and_read_only():
    assert "workflow_dispatch:" in WF
    assert "contents: read" in WF

def test_exact_android_baseline():
    assert "platforms;android-36" in WF
    assert "ndk;27.2.12479018" in WF
    assert "stage_supported_build.sh" in WF

def test_private_values_use_actions_secrets():
    for name in ("MUBA_OFFICIAL_DIALOG_ID","MUBA_V3_TELEGRAM_API_ID","MUBA_V3_TELEGRAM_API_HASH"):
        assert "secrets."+name in WF
    assert "::add-mask::" in WF

def test_no_session_or_bot_token_reuse():
    assert "MUBA_DEV_SESSION" not in WF
    assert "TELEGRAM_BOT_TOKEN" not in WF
    assert "Do not reuse the production bot token or the V2 StringSession" in DOC

def test_apk_publication_fail_closed():
    assert "does not publish a fake or incomplete APK" in DOC
    assert "composer hook" in DOC
