from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/"android-v3"/"termux_build_probe.sh"
DOC=ROOT/"docs"/"MUBA_DEV_TRANSLATOR_V3_TERMUX_BUILD.md"

def test_probe_is_non_installing_and_secret_safe():
    text=PROBE.read_text()
    assert "pkg install" not in text
    assert "apt install" not in text
    assert "MUBA_DEV_SESSION" not in text
    assert "TELEGRAM_API_HASH" not in text
    assert "Private build inputs are intentionally NOT inspected or printed" in text

def test_probe_checks_required_toolchain():
    text=PROBE.read_text()
    assert "sdkmanager" in text
    assert "Android SDK 36" in text
    assert "Android NDK 27.2.12479018" in text

def test_termux_plan_has_safe_fallback_and_production_boundary():
    text=DOC.read_text()
    assert "experimental build path" in text
    assert "does **not** prove" in text
    assert "Do not modify" in text
    assert "supported Linux/Android Studio build host" in text
