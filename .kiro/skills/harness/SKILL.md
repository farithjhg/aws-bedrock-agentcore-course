---
name: harness
description: Start a harnessed task — goal, plan, Definition-of-Done script, then stop for human approval. Use when the user says "/harness <goal>" or asks to start a harnessed task.
---
Start a harnessed task for the goal the user gave.

Follow .claude/harness/PROTOCOL.md, Phase 1 only.
- If .harness/STATUS.md exists and State is not COMPLETE: stop and ask the user instead.
- If this is not a git repo, stop and ask (the harness needs a Base sha and per-step commits).
- mkdir -p .harness. Write GOAL.md, PLAN.md, dod.sh (LF line endings, chmod +x), STATUS.md
  (State/Step lines at column 0, no indentation).
- Run bash .harness/dod.sh once and show that it FAILS. If it passes now, it tests nothing — fix it.
- Stop. Tell the user: "Review .harness/, then run in your terminal: bash .claude/harness/approve.sh"
