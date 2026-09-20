from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs"/"MUBA_DEV_TRANSLATOR_V3_SUPPORTED_BUILD_HOST.md"
CHECK=ROOT/"android-v3"/"supported_host_probe.sh"

def test_supported_host_contract_preserves_production():
    t=DOC.read_text()
    assert "Do not modify telegram-bot" in t
    assert "No APK may be called stable until this matrix passes on-device." in t
    assert "never globally intercept SendMessagesHelper" in t

def test_acceptance_matrix_is_official_channel_only():
    t=DOC.read_text()
    assert "official MUBA channel + Turkish + toggle ON" in t
    assert "private chat => unchanged stock behavior" in t
    assert "other group => unchanged stock behavior" in t
    assert "other channel => unchanged stock behavior" in t
    assert "translation failure => no accidental Turkish send" in t
    assert "no recursion/duplicate" in t

def test_host_probe_requires_exact_sdk_ndk_without_secrets():
    t=CHECK.read_text()
    assert "platforms/android-36" in t
    assert "27.2.12479018" in t
    assert "MUBA_DEV_SESSION" not in t
    assert "TELEGRAM_API_HASH" not in t
    assert "PRIVATE INPUTS: not inspected" in t
