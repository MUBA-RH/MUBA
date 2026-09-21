#!/usr/bin/env bash
set -euo pipefail
: "${ANDROID_HOME:?ANDROID_HOME must point to the supported Android SDK}"
: "${ANDROID_NDK_HOME:?ANDROID_NDK_HOME must point to Android NDK 27.2.12479018}"

echo "=== MUBA V3 SUPPORTED HOST CHECK ==="
java -version
git --version
test -d "$ANDROID_HOME/platforms/android-36"
test -d "$ANDROID_NDK_HOME"
case "$ANDROID_NDK_HOME" in
  *27.2.12479018*) ;;
  *) echo "BLOCKED: expected NDK 27.2.12479018"; exit 2;;
esac
echo "SDK 36: OK"
echo "NDK 27.2.12479018: OK"
echo "PRIVATE INPUTS: not inspected"
echo "RESULT: HOST PREREQUISITES READY"
