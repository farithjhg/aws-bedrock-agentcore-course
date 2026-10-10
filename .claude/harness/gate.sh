#!/usr/bin/env bash
# Stop hook. Inert unless .harness/active exists in the project.
# Claude Code: exit 2 blocks the stop and feeds stderr back to the agent.
# Kiro: Stop hooks cannot block, so this only refreshes .harness/gate.last (shown by turn.sh)
#       and the steering rule tells the agent to run it itself before ending a turn.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
input=$(cat 2>/dev/null || true)
H=.harness; MAX=${HARNESS_MAX_RETRIES:-3}
[ -f $H/active ] || exit 0
h() { if command -v sha256sum >/dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }

if grep -Eq '^[[:space:]]*State: BLOCKED' $H/STATUS.md 2>/dev/null; then   # handing back is always allowed
  echo "blocked (handed back)" > $H/gate.last; exit 0
fi
# Fresh Claude Code turn (stop_hook_active=false) → reset counter. Kiro resets it in turn.sh.
printf '%s' "$input" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*false' && echo 0 > $H/attempts
n=$(cat $H/attempts 2>/dev/null || echo 0)

fail() {
  n=$((n+1)); echo "$n" > $H/attempts
  echo "red ($n/$MAX): $(printf '%s' "$1" | head -n 1)" > $H/gate.last
  [ "$n" -ge "$MAX" ] && { echo "harness: gate failed ${MAX}x, handing back to human" >&2; exit 0; }
  { echo "HARNESS GATE ($n/$MAX): $1"
    echo "Keep working, or set 'State: BLOCKED: <reason>' in .harness/STATUS.md."; } >&2
  exit 2
}

h -c $H/.approved >/dev/null 2>&1 || fail "dod.sh or GOAL.md changed after approval."
bash $H/dod.sh > $H/dod.log 2>&1 || fail "dod.sh is red:
$(tail -n 30 $H/dod.log)"

echo "green" > $H/gate.last
if grep -Eq '^[[:space:]]*State: COMPLETE' $H/STATUS.md; then         # green + COMPLETE → disarm
  rm -f $H/active; echo "green, COMPLETE, disarmed" > $H/gate.last
fi
exit 0
