#!/usr/bin/env bash
# Usage: tools/open-game.sh          Opens your Lab 2 game: games/snake/index.html
#        tools/open-game.sh <SEAT>   Opens the game of a race.sh run (optional path)
set -euo pipefail

seat="${1:-}"
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"

if [ -z "$seat" ]; then
  game="$root/games/snake/index.html"
  if [ ! -f "$game" ]; then
    echo "There is no games/snake/index.html. Claude did not write the game file." >&2
    echo "Score 0 and write playable: no." >&2
    exit 1
  fi
  what="Your Lab 2 game"
else
  pathfile="$root/results/$seat.path"
  [ -f "$pathfile" ] || { echo "No race.sh result for $seat. For your Lab 2 game, type tools/open-game.sh with no seat ID." >&2; exit 1; }
  game="$(tr -d '\r' < "$pathfile")"
  if [ ! -f "$game" ]; then
    echo "The race.sh run $seat did not make a game file:" >&2
    echo "  $game" >&2
    echo "Score this run 0 and write playable: no." >&2
    exit 1
  fi
  what="The game of race.sh run $seat"
fi

case "$(uname -s)" in
  Darwin)
    open "$game" ;;
  MINGW*|MSYS*)
    MSYS_NO_PATHCONV=1 cmd.exe /c start "" "$(cygpath -w "$game")" ;;
  CYGWIN*)
    cygstart "$game" ;;
  *)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      if command -v wslview >/dev/null 2>&1; then wslview "$game"
      else explorer.exe "$(wslpath -w "$game")" || true; fi
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$game" >/dev/null 2>&1 &
    else
      echo "Open this file in your browser:"
      echo "  $game"
      exit 0
    fi ;;
esac

echo "$what is open in your browser. Score it with labs/scoring-checklist.md."
