#!/usr/bin/env bash
# Claude Code status line for the Lighthouse Arcade workshop.
# Prints one line, for example:
#   Opus 5.5 (medium) | cache 52:14 | 🧠 ██░░░░░░░░ 23% | 💰 $0.62
# This is the output of the prompt on the status line slide:
#   /statusline Show model with effort | prompt cache countdown (green, yellow under
#   20% left, red "cache cold" when expired) | 🧠  context bar (green <50%, yellow <80%,
#   red) |💰 cost, refresh every second.
# Claude Code sends the session data as JSON on stdin. The script runs on your
# computer and uses no tokens. Needs jq. Works with bash 3.2 (macOS) and later.
# On Windows, jq can print CRLF line ends. The script removes each \r.
# Set STATUSLINE_ASCII=1 if your terminal shows boxes instead of the two icons.
#
# No "set -e" here on purpose: a status line must always print one line,
# also when a field is missing or jq fails.
set -uo pipefail

input=$(cat)
now=$(date +%s)

IFS='|' read -r model effort warm ttl expires pct cost < <(
  jq -r '[
      (.model.display_name // .model.id // "?"),
      (.effort.level // ""),
      (.prompt_cache.warm // false),
      (.prompt_cache.ttl // ""),
      ((.prompt_cache.expires_at // "") | if type == "number" then floor else . end),
      ((.context_window.used_percentage // 0) | floor),
      (.cost.total_cost_usd // 0)
    ] | map(tostring) | join("|")' <<<"$input" 2>/dev/null | tr -d '\r'
)

# Safe defaults if the input was not valid JSON.
model=${model:-?}
effort=${effort:-}
num() { case "${1:-}" in ''|*[!0-9]*) echo 0 ;; *) echo "$1" ;; esac; }
pct=$(num "${pct:-}"); expires=$(num "${expires:-}")
if [ "$pct" -gt 100 ]; then pct=100; fi

# Colors: VS Code terminal bright green, yellow and red (ANSI 92, 93, 91). Grey text, dim separators.
G=$'\033[38;5;246m'; D=$'\033[38;5;242m'; GR=$'\033[92m'; Y=$'\033[93m'; R=$'\033[91m'; X=$'\033[0m'
SEP="${D} | ${X}"

# 1. Model with effort: "Opus 5.5 (medium)". No effort field: the model name only.
seg_model="${G}${model}${effort:+ ($effort)}${X}"

# 2. Prompt cache countdown in mm:ss. Green; yellow under 20% of the TTL left
#    (1 h TTL: under 12:00; 5 min TTL: under 1:00); red "cache cold" after it expires.
#    Before the first reply Claude Code sends no prompt_cache object: "cache n/a".
case "${ttl:-}" in 5m) ttl_s=300 ;; 1h) ttl_s=3600 ;; *) ttl_s=3600 ;; esac
if [ "$expires" -eq 0 ] && [ "${warm:-false}" != "true" ] && [ -z "${ttl:-}" ]; then
  seg_cache="${G}cache n/a${X}"
elif [ "${warm:-false}" = "true" ] && [ "$expires" -gt "$now" ]; then
  left=$((expires - now))
  if [ $((left * 5)) -lt "$ttl_s" ]; then CC=$Y; else CC=$GR; fi
  seg_cache="${CC}$(printf 'cache %02d:%02d' $((left / 60)) $((left % 60)))${X}"
else
  seg_cache="${R}cache cold${X}"
fi

# 3. Context bar: 10 steps, one per 10 percent. Green under 50, yellow under 80, red from 80.
filled=$((pct / 10)); bar=""; i=0
while [ "$i" -lt 10 ]; do
  if [ "$i" -lt "$filled" ]; then bar="${bar}█"; else bar="${bar}░"; fi
  i=$((i + 1))
done
if [ "$pct" -ge 80 ]; then BC=$R; elif [ "$pct" -ge 50 ]; then BC=$Y; else BC=$GR; fi
seg_ctx="${BC}${bar}${X} ${G}${pct}%${X}"

# 4. Cost: an estimate at list price, two decimals.
seg_cost="${G}$(LC_ALL=C printf '$%.2f' "${cost:-0}" 2>/dev/null || echo '$0.00')${X}"

if [ "${STATUSLINE_ASCII:-0}" = "1" ]; then I1="ctx "; I2=""; else I1="🧠 "; I2="💰 "; fi
echo "${seg_model}${SEP}${seg_cache}${SEP}${I1}${seg_ctx}${SEP}${I2}${seg_cost}"

# Lab 1 stretch task: add the hit ratio and the last miss cause.
# Read them with these jq expressions (the miss cause needs Claude Code 2.1.260 or later):
#   .prompt_cache.hit_ratio
#   (.prompt_cache.last_miss_cause.causes // []) | join(",")
