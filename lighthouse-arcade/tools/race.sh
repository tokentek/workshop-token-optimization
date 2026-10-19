#!/usr/bin/env bash
# Usage: tools/race.sh <haiku|sonnet|opus> <low|medium|high> [SEAT]
# Example: tools/race.sh sonnet medium B3
# Optional extra for Lab 2: run more cells headless. The main Lab 2 path is interactive (labs/LAB2.md).
#
# Optional environment variables:
#   RACE_PROMPT=<file>        Use another prompt (challenge column). Default: stories/snake-race-prompt.md
#   RACE_CAP_SECONDS=<n>      Wall clock cap in seconds. Default: 480 (8 minutes).
#   RACE_TIMER=<name>         Force the timer: timeout, gtimeout, perl or none. Default: first that works.
#   RACE_NO_PULL=1            Do not run "git pull" before the race.
#   RACE_REFERENCE=1          Presenter only: also allow fable and the efforts xhigh and max (reference runs).
#                             Fable bills usage credits on Standard Team seats. Use a Premium seat.
#
# One run = one new git worktree in ../lighthouse-runs/<run>, one "claude -p" call, and one tab separated board line:
#   seat model effort cost_usd minutes output_tokens
# Then two info lines that start with "#": the run details and the path to the game.
#
# On Windows, jq can print CRLF line ends. The script removes each \r.
# No "set -e" on purpose: "claude -p" exits non-zero when it reaches --max-turns
# or a budget limit. The script must still print the result line.
set -uo pipefail

die() { echo "$*" >&2; exit 2; }

model="${1:-}"; effort="${2:-}"; seat="${3:-PRE}"
if [ -n "${RACE_REFERENCE:-}" ]; then
  # Presenter only: reference runs before the workshop (fable medium, opus xhigh).
  case "$model"  in haiku|sonnet|opus|fable) ;; *) die "With RACE_REFERENCE, model must be haiku, sonnet, opus or fable." ;; esac
  case "$effort" in low|medium|high|xhigh|max) ;; *) die "With RACE_REFERENCE, effort must be low, medium, high, xhigh or max." ;; esac
else
  case "$model"  in haiku|sonnet|opus) ;; *) die "Usage: tools/race.sh <haiku|sonnet|opus> <low|medium|high> [SEAT]. Model must be haiku, sonnet or opus." ;; esac
  case "$effort" in low|medium|high)   ;; *) die "Usage: tools/race.sh <haiku|sonnet|opus> <low|medium|high> [SEAT]. Effort must be low, medium or high." ;; esac
fi
case "$seat"   in ''|*[!A-Za-z0-9_-]*) die "Seat ID must use only letters, digits, - and _. Example: B3" ;; esac
[ -n "${CLAUDE_CODE_EFFORT_LEVEL:-}" ] && die "Unset CLAUDE_CODE_EFFORT_LEVEL first. Type: unset CLAUDE_CODE_EFFORT_LEVEL"

cap_s="${RACE_CAP_SECONDS:-480}"
case "$cap_s" in ''|*[!0-9]*) die "RACE_CAP_SECONDS must be a number of seconds." ;; esac

for tool in git jq claude; do
  command -v "$tool" >/dev/null 2>&1 || die "$tool is not installed or not on your PATH. Run tools/precheck.sh."
done

here="$(cd "$(dirname "$0")" && pwd)"
# The repo root is the parent of tools/. Do not use "git rev-parse --show-toplevel":
# on Windows it can print a C:/ path.
root="$(cd "$here/.." && pwd)"
git -C "$root" rev-parse --git-dir >/dev/null 2>&1 \
  || die "lighthouse-arcade is not a git repository. Clone it with git, or unzip the full zip file (with the .git folder)."

# Get kit updates from the facilitator, if this clone has an upstream. Never ask for a password.
if [ -z "${RACE_NO_PULL:-}" ] && git -C "$root" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
  GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes}" \
    git -C "$root" pull --ff-only -q >/dev/null 2>&1 \
    || echo "Note: git pull did not work. The race uses your local copy." >&2
fi

# Read the prompt now, before we change directory (RACE_PROMPT can be a relative path).
prompt_file="${RACE_PROMPT:-$root/stories/snake-race-prompt.md}"
[ -f "$prompt_file" ] || die "Prompt file not found: $prompt_file"
prompt="$(tr -d '\r' < "$prompt_file")"
[ -n "$prompt" ] || die "Prompt file is empty: $prompt_file"

# The worktree starts from the last commit. Uncommitted edits (for example to CLAUDE.md) are not in it.
if [ -n "$(git -C "$root" status --porcelain --untracked-files=no 2>/dev/null)" ]; then
  echo "Note: you have uncommitted changes. The run uses your last commit. Commit first to include them." >&2
fi

runs="$(dirname "$root")/lighthouse-runs"
run="$seat-$model-$effort-$(date +%H%M%S)"
n=2
while [ -e "$runs/$run" ] || [ -e "$root/results/$run.json" ]; do
  run="$seat-$model-$effort-$(date +%H%M%S)-$n"; n=$((n + 1))
done
mkdir -p "$runs" "$root/results"
git -C "$root" worktree add -q --detach "$runs/$run" HEAD \
  || die "Could not make the worktree $runs/$run. Ask a helper."
out="$root/results/$run.json"

# Wall clock cap. macOS has no "timeout" by default, so perl is the fallback.
# On Windows, "timeout" can be the Windows wait command, so check for GNU timeout.
is_gnu() { "$1" --version 2>/dev/null | grep -qi -e 'GNU' -e 'coreutils'; }
timer="${RACE_TIMER:-}"
if [ -z "$timer" ]; then
  if command -v timeout >/dev/null 2>&1 && is_gnu timeout; then timer=timeout
  elif command -v gtimeout >/dev/null 2>&1 && is_gnu gtimeout; then timer=gtimeout
  elif command -v perl >/dev/null 2>&1; then timer=perl
  else timer=none; fi
fi
case "$timer" in
  timeout|gtimeout) cap=("$timer" -k 10 "$cap_s") ;;
  # perl: like GNU timeout. Run the command in its own process group. After the cap,
  # send TERM to the whole group (also to tool commands that claude started),
  # then KILL after 10 s, and exit 124.
  perl) cap=(perl -MPOSIX=:sys_wait_h -e '
      my $t = shift; my $p = fork; die "fork failed: $!\n" unless defined $p;
      if ($p == 0) { setpgrp(0, 0); exec @ARGV or die "exec failed: $!\n" }
      $SIG{ALRM} = sub { kill "TERM", -$p;
        for (1 .. 10) { if (waitpid($p, WNOHANG) > 0) { kill "KILL", -$p; exit 124 } sleep 1 }
        kill "KILL", -$p; waitpid($p, 0); exit 124 };
      alarm $t; waitpid($p, 0); exit($? & 127 ? 128 + ($? & 127) : $? >> 8)' "$cap_s") ;;
  none) cap=(); echo "Warning: no timeout, gtimeout or perl found. The run has no time cap." >&2 ;;
  *) die "RACE_TIMER must be timeout, gtimeout, perl or none." ;;
esac

# Keep a Mac awake during the break.
awake=()
command -v caffeinate >/dev/null 2>&1 && awake=(caffeinate -i)

if [ $((cap_s % 60)) -eq 0 ]; then cap_text="max $((cap_s / 60)) min"; else cap_text="max $cap_s s"; fi
echo "Race started: $seat $model $effort ($cap_text)"

start=$SECONDS
# ${arr[@]+"${arr[@]}"} avoids the "unbound variable" error of bash 3.2 with an empty array.
( cd "$runs/$run" \
  && export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
  && ${awake[@]+"${awake[@]}"} ${cap[@]+"${cap[@]}"} \
     claude -p "$prompt" \
       --model "$model" --effort "$effort" \
       --permission-mode acceptEdits --max-turns 40 \
       --output-format json < /dev/null > "$out" ) || true
elapsed=$((SECONDS - start))

if jq -e 'type == "object"' "$out" >/dev/null 2>&1; then
  line=$(jq -r --arg s "$seat" --arg m "$model" --arg e "$effort" \
    '[$s, $m, $e, ((.total_cost_usd // 0) * 1000 | round / 1000),
      ((.duration_api_ms // .duration_ms // 0) / 6000 | round / 10),
      (.usage.output_tokens // 0)] | @tsv' "$out" | tr -d '\r')
  detail=$(jq -r '"# Detail: subtype=\(.subtype // "unknown") turns=\(.num_turns // 0) input=\(.usage.input_tokens // 0) cache_read=\(.usage.cache_read_input_tokens // 0) cache_write=\(.usage.cache_creation_input_tokens // 0)"' "$out" | tr -d '\r')
else
  line=$(printf '%s\t%s\t%s\t0\t%s\t0' "$seat" "$model" "$effort" "$(awk -v s="$elapsed" 'BEGIN { printf "%.1f", s / 60 }')")
  detail="# Detail: subtype=timeout_or_crash"
fi

echo "$line" | tee "$root/results/$seat.tsv"
echo "$detail"
game="$runs/$run/games/snake/index.html"
echo "$game" > "$root/results/$seat.path"
echo "# Game: $game"
