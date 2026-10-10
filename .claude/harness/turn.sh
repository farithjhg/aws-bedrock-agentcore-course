#!/usr/bin/env bash
# Kiro UserPromptSubmit hook: a new human prompt is a fresh turn → reset the retry counter
# and remind the agent of the gate (Kiro's Stop hook cannot block on its own).
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
[ -f .harness/active ] || exit 0
echo 0 > .harness/attempts
echo "HARNESS ARMED. Follow .claude/harness/PROTOCOL.md. Before ending your turn run:"
echo "  bash .claude/harness/gate.sh < /dev/null"
echo "If it exits non-zero, keep working or set 'State: BLOCKED: <reason>' in .harness/STATUS.md."
grep -E '^[[:space:]]*(State|Step):' .harness/STATUS.md 2>/dev/null
[ -f .harness/gate.last ] && echo "Last gate: $(cat .harness/gate.last)"
exit 0
