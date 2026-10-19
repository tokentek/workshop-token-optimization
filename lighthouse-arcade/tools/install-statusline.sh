#!/usr/bin/env bash
# Install the workshop status line for Claude Code.
# 1. Backs up ~/.claude/settings.json (if it exists).
# 2. Copies tools/statusline.sh to ~/.claude/statusline.sh.
# 3. Merges the statusLine setting into ~/.claude/settings.json with jq.
# You can run it again. A second run changes nothing.
# On Windows, jq can print CRLF line ends. The script removes each \r.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
src="$here/statusline.sh"
dir="$HOME/.claude"
settings="$dir/settings.json"
target="$dir/statusline.sh"
stamp="$(date +%Y%m%d-%H%M%S)"

filter='.statusLine = {"type":"command","command":"~/.claude/statusline.sh","padding":0,"refreshInterval":1}'

fail() { echo "ERROR: $*" >&2; exit 1; }

command -v jq >/dev/null 2>&1 || fail "jq is not installed. Install jq, then run this script again."
[ -f "$src" ] || fail "Cannot find $src. Run this script from your lighthouse-arcade folder."

mkdir -p "$dir"

# Make a backup name that does not exist yet.
backup_name() {
  local base="$1.bak-$stamp" name n=1
  name="$base"
  while [ -e "$name" ]; do name="$base-$n"; n=$((n + 1)); done
  echo "$name"
}

# Step 1: build the new settings in a temp file.
tmp="$(mktemp "$dir/settings.json.tmp.XXXXXX")"
trap 'rm -f "$tmp"' EXIT

if [ -f "$settings" ]; then
  if ! jq -e 'type == "object"' "$settings" >/dev/null 2>&1; then
    fail "$settings is not a valid JSON object. Nothing changed. Ask a helper."
  fi
  jq "$filter" "$settings" | tr -d '\r' > "$tmp"
else
  echo '{}' | jq "$filter" | tr -d '\r' > "$tmp"
fi

# Step 2: copy the status line script.
if [ -f "$target" ] && ! cmp -s "$src" "$target"; then
  old_script="$(backup_name "$target")"
  cp "$target" "$old_script"
  echo "Saved your old status line script: $old_script"
fi
cp "$src" "$target"
chmod +x "$target"

# Step 3: write settings.json only if it changes.
if [ -f "$settings" ] && [ "$(jq -S . "$settings" | tr -d '\r')" = "$(jq -S . "$tmp" | tr -d '\r')" ]; then
  echo "Your settings already have this status line. No backup was necessary."
  echo "Settings file: $settings"
else
  if [ -f "$settings" ]; then
    backup="$(backup_name "$settings")"
    cp "$settings" "$backup"
    if jq -e 'has("statusLine")' "$backup" >/dev/null 2>&1; then
      echo "Your old statusLine setting is in the backup."
    fi
    echo "Backup of your settings: $backup"
    # Write through the existing file: keeps its permissions and a symlink (dotfiles).
    cat "$tmp" > "$settings"
  else
    echo "No settings.json found. Created a new one: $settings"
    mv "$tmp" "$settings"
  fi
fi

echo "Status line installed. Start a new claude session."
