#!/usr/bin/env bash
set -euo pipefail

# MUBA V3 Termux build readiness probe.
# Read-only except for an optional isolated workspace path supplied by the DEV.
# It does not install packages, change production MUBA, or expose credentials.

need=(git java javac)
missing=0
for cmd in "${need[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf 'OK   %-8s %s\n' "$cmd" "$(command -v "$cmd")"
  else
    printf 'MISS %-8s\n' "$cmd"
    missing=1
  fi
done

printf '\nARCH: %s\n' "$(uname -m)"
printf 'HOME: %s\n' "$HOME"

if [ -n "${ANDROID_HOME:-}" ]; then
  printf 'ANDROID_HOME: SET\n'
else
  printf 'ANDROID_HOME: NOT SET\n'
fi

if command -v sdkmanager >/dev/null 2>&1; then
  printf 'sdkmanager: OK\n'
else
  printf 'sdkmanager: NOT FOUND\n'
  missing=1
fi

if command -v gradle >/dev/null 2>&1; then
  printf 'gradle: OK\n'
else
  printf 'gradle: NOT FOUND (wrapper may still be used after clone)\n'
fi

printf '\nRequired Telegram Android toolchain target:\n'
printf '  Android SDK 36\n'
printf '  Android NDK 27.2.12479018\n'
printf '  JDK/Gradle compatible with current upstream\n'
printf '\nPrivate build inputs are intentionally NOT inspected or printed.\n'

if [ "$missing" -ne 0 ]; then
  printf '\nRESULT: NOT READY — prerequisites missing. No changes made.\n'
  exit 2
fi
printf '\nRESULT: BASE TOOLING PRESENT — SDK/NDK versions still require verification.\n'
