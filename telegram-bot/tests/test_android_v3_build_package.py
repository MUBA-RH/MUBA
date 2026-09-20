from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=(ROOT/"android-v3"/"stage_supported_build.sh").read_text()
DOC=(ROOT/"docs"/"MUBA_DEV_TRANSLATOR_V3_BUILD_PACKAGE.md").read_text()

def test_build_package_pins_verified_toolchain_and_upstream():
    assert "9552e5541e1274b9557c9832b204dbfcaf44b3dc" in SCRIPT
    assert "platforms/android-36" in SCRIPT
    assert "27.2.12479018" in SCRIPT
    assert "git submodule update --init --recursive" in SCRIPT

def test_build_package_stages_all_helpers():
    for name in ("MubaDevTranslateBeforeSend.java","MubaDevTranslationGate.java","MubaDevSendPipeline.java","MubaDevSendBypass.java"):
        assert name in SCRIPT

def test_no_private_inputs_embedded():
    assert "API_HASH=" not in SCRIPT
    assert "SESSION=" not in SCRIPT
    assert "PHONE=" not in SCRIPT
    assert "2FA=" not in SCRIPT

def test_global_send_hook_remains_forbidden():
    assert "never hook global" in DOC
    assert "SendMessagesHelper.sendMessage" in DOC
    assert "V3 is not declared live/stable" in DOC
