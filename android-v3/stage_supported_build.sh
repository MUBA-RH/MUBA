#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_COMMIT="${MUBA_V3_UPSTREAM_COMMIT:-9552e5541e1274b9557c9832b204dbfcaf44b3dc}"
ROOT="${1:-$PWD/Telegram}"
HERE="$(cd "$(dirname "$0")" && pwd)"

fail(){ echo "BLOCKED: $*" >&2; exit 2; }

command -v git >/dev/null || fail "git missing"
command -v java >/dev/null || fail "Java missing"
if [ "${MUBA_V3_SKIP_HOST_SDK_CHECK:-0}" != "1" ]; then
  : "${ANDROID_HOME:?ANDROID_HOME is required}"
  test -d "$ANDROID_HOME/platforms/android-36" || fail "Android SDK 36 missing"
  test -d "$ANDROID_HOME/ndk/27.2.12479018" || fail "NDK 27.2.12479018 missing"
fi

if [ ! -d "$ROOT/.git" ]; then
  git clone --recursive --shallow-submodules https://github.com/DrKLO/Telegram.git "$ROOT"
fi
cd "$ROOT"
git fetch origin "$UPSTREAM_COMMIT" --depth=1
git checkout --detach "$UPSTREAM_COMMIT"
git submodule update --init --recursive --depth=1

DEST="TMessagesProj/src/main/java/org/muba/devtranslator"
mkdir -p "$DEST"
cp "$HERE"/MubaDevTranslateBeforeSend.java "$DEST/"
cp "$HERE"/MubaDevTranslationGate.java "$DEST/"
cp "$HERE"/MubaDevSendPipeline.java "$DEST/"
cp "$HERE"/MubaDevSendBypass.java "$DEST/"

cat <<EOF
=== MUBA V3 BUILD PACKAGE STAGED ===
UPSTREAM=$UPSTREAM_COMMIT
SDK=36
NDK=27.2.12479018
HELPERS=$DEST
NEXT=apply composer hook with private official dialog id, then compile/test
EOF
