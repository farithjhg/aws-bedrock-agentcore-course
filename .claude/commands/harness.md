---
description: Start a harnessed task — goal, plan, Definition-of-Done script, then stop for approval
argument-hint: <goal in one sentence>
---
Start a harnessed task for: $ARGUMENTS

Follow .claude/harness/PROTOCOL.md, Phase 1 only.
- If .harness/STATUS.md exists and State is not COMPLETE: stop and ask me instead.
- If this is not a git repo, stop and ask me (the harness needs a Base sha and per-step commits).
- mkdir -p .harness. Write GOAL.md, PLAN.md, dod.sh (LF line endings, chmod +x), STATUS.md
  (State/Step lines at column 0, no indentation).
- Run bash .harness/dod.sh once and show that it FAILS. If it passes now, it tests nothing — fix it.
- Stop. Tell me: "Review .harness/, then run: ! bash .claude/harness/approve.sh"
