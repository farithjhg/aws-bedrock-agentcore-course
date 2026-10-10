#!/usr/bin/env bash
# PreToolUse hook (Claude Code + Kiro). Exit 2 blocks the tool call and feeds stderr to the agent.
# - Always: the agent may not touch the gate state (.harness/active, .approved, attempts) or run approve.sh.
# - While armed: the agent may not edit, move or delete .harness/dod.sh or .harness/GOAL.md.
# A speed bump against accidents and shortcuts, not a sandbox: obfuscated shell can still get past it.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
input=$(cat 2>/dev/null || true)

# Only inspect path/command fields, never the content being written.
targets=$(printf '%s' "$input" | grep -oE '"(file_path|notebook_path|path|targetFile|sourcePath|destinationPath|command)"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"')
[ -n "$targets" ] || exit 0

block() {
  echo "HARNESS GUARD: $1 Only the human does this. If the harness is wrong, set 'State: BLOCKED: <reason>' in .harness/STATUS.md." >&2
  exit 2
}

D='\.harness[/\\]+'
printf '%s\n' "$targets" | grep -Eq "${D}(active|\.approved|attempts)([^A-Za-z0-9_.-]|$)|approve\.sh" \
  && block "Touching the gate state (.harness/active, .approved, attempts) or approve.sh is not allowed."

[ -f .harness/active ] || exit 0
F="${D}(dod\.sh|GOAL\.md)"
paths=$(printf '%s\n' "$targets" | grep -Ev '^"command"')
cmds=$(printf '%s\n' "$targets" | grep -E '^"command"')
[ -n "$paths" ] && printf '%s\n' "$paths" | grep -Eq "$F" \
  && block "dod.sh and GOAL.md are frozen after approval."
[ -n "$cmds" ] && printf '%s\n' "$cmds" | grep -Eq "(>>?|\btee\b|\bsed[[:space:]]+(-[a-zA-Z]*[[:space:]]+)*-i|\b(rm|mv|cp|truncate|chmod|perl|python3?)\b)[^|;&]*${F}" \
  && block "dod.sh and GOAL.md are frozen after approval."
exit 0
