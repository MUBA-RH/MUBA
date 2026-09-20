#!/usr/bin/env bash
set -euo pipefail

# MUBA DEV Translator V3 bootstrap.
# Creates an isolated working copy of Telegram Android; never touches telegram-bot/.
ROOT="${1:-$HOME/muba-dev-android}"
UPSTREAM="https://github.com/DrKLO/Telegram.git"

if [ -e "$ROOT" ]; then
  echo "Refusing to overwrite existing path: $ROOT" >&2
  exit 2
fi

git clone --recursive --shallow-submodules "$UPSTREAM" "$ROOT"
mkdir -p "$ROOT/muba-v3"
cp "$(dirname "$0")/MubaDevTranslateBeforeSend.java" "$ROOT/muba-v3/"\ncp "$(dirname "$0")/MubaDevTranslationGate.java" "$ROOT/muba-v3/"\ncp "$(dirname "$0")/MubaDevSendPipeline.java" "$ROOT/muba-v3/"
cat > "$ROOT/muba-v3/README.txt" <<'EOF'
This directory is the isolated MUBA V3 integration staging area.
Do not copy Telegram auth/session files, API hashes, keystores, Firebase files,
phone numbers, login codes, or 2FA credentials into the MUBA production repo.

Integration target:
- call MubaDevTranslateBeforeSend.translate(...)
- only after explicit DEV Translation toggle is enabled
- on success, pass translated text/entities to Telegram's normal user send path
- on failure, keep the draft and do not send
EOF

echo "V3 upstream workspace ready: $ROOT"
echo "Next: configure your own Telegram api_id/build signing per upstream README."
