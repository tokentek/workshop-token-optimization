#!/usr/bin/env bash
# Prework check for the Lighthouse Arcade workshop.
# Usage: tools/precheck.sh ["Your Name"]
# Prints hints for each problem, then one PRECHECK line. Submit that line in the form.
#
# Optional: PRECHECK_SKIP_NET=1 skips the network test (no Claude request).
#           The result is then PASS_NO_NET at best. Do not submit that line.
#
# No "set -e" on purpose: every check must run, also when one fails.
# On Windows, jq and claude can print CRLF line ends. The script removes each \r.
set -uo pipefail

nocr() { tr -d '\r'; }

MIN_VERSION="2.1.283"
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"
name="${1:-$(git config user.name 2>/dev/null | nocr || true)}"
name="${name:-${USER:-${USERNAME:-unknown}}}"
name="$(printf '%s' "$name" | tr '|' '/')"

fails=0
hint() { echo "  FIX: $*" >&2; }
bad() { fails=$((fails + 1)); hint "$*"; }

# Compare two versions a.b.c. Returns 0 if $1 >= $2. Works in bash 3.2.
version_ge() {
  local a1 a2 a3 b1 b2 b3
  IFS=. read -r a1 a2 a3 <<<"$1"
  IFS=. read -r b1 b2 b3 <<<"$2"
  a1=${a1:-0}; a2=${a2:-0}; a3=${a3:-0}; b1=${b1:-0}; b2=${b2:-0}; b3=${b3:-0}
  [ "$a1" -ne "$b1" ] && { [ "$a1" -gt "$b1" ]; return; }
  [ "$a2" -ne "$b2" ] && { [ "$a2" -gt "$b2" ]; return; }
  [ "$a3" -ge "$b3" ]
}

echo "Lighthouse Arcade precheck. This can take up to one minute." >&2

# 1. Claude Code version
cc="missing"
if command -v claude >/dev/null 2>&1; then
  cc="$(claude --version 2>/dev/null | nocr | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)"
  cc="${cc:-unknown}"
  if [ "$cc" = "unknown" ] || ! version_ge "$cc" "$MIN_VERSION"; then
    bad "Claude Code $cc is too old. You need $MIN_VERSION or later. Type claude update"
  fi
else
  bad "Claude Code is not installed or not on your PATH. Install it, then run this script again."
fi

# 2. Login method (a claude.ai login uses your Team seat; an API key does not)
auth="unknown"
if [ "$cc" != "missing" ]; then
  status_json="$( (claude auth status --json 2>/dev/null || claude auth status 2>/dev/null || true) | nocr)"
  if printf '%s' "$status_json" | jq -e . >/dev/null 2>&1; then
    logged_in="$(printf '%s' "$status_json" | jq -r '.loggedIn // false' | nocr)"
    method="$(printf '%s' "$status_json" | jq -r '.authMethod // "unknown"' | nocr)"
    provider="$(printf '%s' "$status_json" | jq -r '.apiProvider // "firstParty"' | nocr)"
    if [ "$logged_in" != "true" ]; then
      auth="none"; bad "You are not logged in. Type claude, then /login, and pick your claude.ai account."
    elif [ "$provider" != "firstParty" ]; then
      auth="$provider"; bad "Claude Code uses $provider. Use your claude.ai Team login for the workshop."
    else
      auth="$method"
      case "$method" in
        claude.ai|oauth_token) ;;
        *) bad "Login method is $method. Type /login in claude and pick your claude.ai account, not an API key." ;;
      esac
    fi
  else
    bad "Could not read claude auth status. Ask a helper in the setup clinic."
  fi
fi

# 3. ANTHROPIC_API_KEY must not be set
api_key_env="unset"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  api_key_env="set"; bad "ANTHROPIC_API_KEY is set. Remove it from your shell profile, then open a new terminal."
fi

# 4. CLAUDE_CODE_EFFORT_LEVEL must not be set (it overrides --effort and /effort)
effort_env="unset"
if [ -n "${CLAUDE_CODE_EFFORT_LEVEL:-}" ]; then
  effort_env="set"; bad "CLAUDE_CODE_EFFORT_LEVEL is set. Remove it from your shell profile, then open a new terminal."
fi

# 5. jq and git
jq_s="ok"; git_s="ok"
command -v jq  >/dev/null 2>&1 || { jq_s="missing";  bad "Install jq. macOS: brew install jq. Windows: use Git Bash or WSL and install jq."; }
command -v git >/dev/null 2>&1 || { git_s="missing"; bad "Install git."; }

# 6. A wall clock timer for the optional race.sh (not required)
timer="none"
is_gnu() { "$1" --version 2>/dev/null | grep -qi -e 'GNU' -e 'coreutils'; }
if command -v timeout >/dev/null 2>&1 && is_gnu timeout; then timer="timeout"
elif command -v gtimeout >/dev/null 2>&1 && is_gnu gtimeout; then timer="gtimeout"
elif command -v perl >/dev/null 2>&1; then timer="perl"
else hint "No timeout, gtimeout or perl found. Only the optional tools/race.sh needs one. macOS: brew install coreutils."; fi

# 7. The bundled /claude-api skill must be on (/doctor prompt-audit needs it)
audit_skill="ok"
if [ "$jq_s" = "ok" ]; then
  for f in "$HOME/.claude/settings.json" "$root/.claude/settings.json" "$root/.claude/settings.local.json"; do
    [ -f "$f" ] || continue
    if jq -e '(.disableBundledSkills == true) or ((.skillOverrides // {})["claude-api"] == "off")' "$f" >/dev/null 2>&1; then
      audit_skill="off"; bad "The bundled /claude-api skill is off in $f. Remove disableBundledSkills or the claude-api entry in skillOverrides."
    fi
  done
else
  audit_skill="unknown"
fi

# 8. No CLAUDE.md in a parent folder of lighthouse-arcade (it would load in every Lab 2 session)
parent_claude_md="none"
d="$(dirname "$root")"
while :; do
  for f in "$d/CLAUDE.md" "$d/CLAUDE.local.md" "$d/.claude/CLAUDE.md"; do
    if [ -f "$f" ]; then
      parent_claude_md="found"; bad "Found $f. Move lighthouse-arcade to your home folder, or rename that file for the workshop."
    fi
  done
  [ "$d" = "/" ] || [ "$d" = "$(dirname "$d")" ] && break
  d="$(dirname "$d")"
done

# 9. Network and seat: one small Haiku request
net="skipped"
if [ -n "${PRECHECK_SKIP_NET:-}" ]; then
  echo "  NOTE: network test skipped (PRECHECK_SKIP_NET is set)." >&2
elif [ "$cc" = "missing" ] || [ "$jq_s" != "ok" ]; then
  net="untested"
else
  reply="$(cd "$root" && claude -p "Reply OK" --model haiku --effort low --max-turns 1 --output-format json < /dev/null 2>/dev/null || true)"
  if printf '%s' "$reply" | jq -e 'has("total_cost_usd")' >/dev/null 2>&1; then
    net="ok"
  else
    net="fail"; bad "The test request to Claude failed. Check your network, proxy and login. Ask a helper in the setup clinic."
  fi
fi

if [ "$fails" -gt 0 ]; then result="FAIL"
elif [ "$net" = "ok" ]; then result="PASS"
else result="PASS_NO_NET"; fi

echo "PRECHECK|$name|cc=$cc|auth=$auth|api_key_env=$api_key_env|effort_env=$effort_env|jq=$jq_s|git=$git_s|timer=$timer|audit_skill=$audit_skill|parent_claude_md=$parent_claude_md|net=$net|RESULT=$result"
[ "$result" = "FAIL" ] && exit 1
exit 0
