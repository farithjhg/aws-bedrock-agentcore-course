#!/usr/bin/env bash
# Human-only: arms the gate. Run it yourself, never let the agent run it.
set -euo pipefail
cd "${CLAUDE_PROJECT_DIR:-$PWD}"
[ -x .harness/dod.sh ] || [ -f .harness/dod.sh ] || { echo "no .harness/dod.sh"; exit 1; }
[ -f .harness/GOAL.md ] || { echo "no .harness/GOAL.md"; exit 1; }
if ! tr -d '\r' < .harness/dod.sh | cmp -s - .harness/dod.sh; then   # not grep: Git for Windows grep strips \r
  echo "dod.sh has CRLF line endings; bash will fail on it. Convert to LF and re-run approve.sh."; exit 1
fi
chmod +x .harness/dod.sh
h() { if command -v sha256sum >/dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }
h .harness/dod.sh .harness/GOAL.md > .harness/.approved
echo 0 > .harness/attempts
rm -f .harness/gate.last
sed -i.bak -E 's/^[[:space:]]*State: PLANNING/State: IN_PROGRESS/' .harness/STATUS.md && rm -f .harness/STATUS.md.bak
grep -Eq '^State: IN_PROGRESS' .harness/STATUS.md || echo "warning: no 'State: PLANNING' line found in STATUS.md"
touch .harness/active
echo "Harness armed. Tell the agent: go."
