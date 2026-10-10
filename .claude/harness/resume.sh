#!/usr/bin/env bash
# SessionStart hook: survives compaction / resume.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
[ -f .harness/STATUS.md ] || exit 0
grep -Eq '^[[:space:]]*State: COMPLETE' .harness/STATUS.md && [ ! -f .harness/active ] && exit 0
echo "Harness task in progress. Re-read .claude/harness/PROTOCOL.md, .harness/GOAL.md, .harness/PLAN.md before acting. Status:"
cat .harness/STATUS.md
