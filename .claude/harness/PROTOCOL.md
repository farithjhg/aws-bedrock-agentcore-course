# Harness Protocol (task-agnostic)
State lives in ./.harness/: GOAL.md, PLAN.md, STATUS.md, dod.sh. Files are truth; your memory is not.
Project CLAUDE.md / .kiro/steering still govern stack and conventions.
Scripts live in .claude/harness/ (shared by Claude Code and Kiro).

## Phase 1 — Plan (gate disarmed)
1. Read the relevant code/docs first. No deliverable work in this phase.
2. GOAL.md: one-sentence goal; scope (may change / must not change); non-goals;
   3–6 acceptance criteria, each checkable.
3. PLAN.md: 3–8 steps. Each: what, files, how it is verified (command or reviewer check).
4. dod.sh: mechanical Definition of Done. Must FAIL now and PASS when done. Under ~2 min.
   Write it with LF line endings (no \r), or bash will fail on Windows.
5. STATUS.md: State: PLANNING, Base: <branch>@<sha>. Then STOP for human approval.

## Phase 2 — Execute (gate armed)
- One step at a time. Verify-first: make the check fail before the change where possible.
- Paste the last lines of each verify run into STATUS.md.
- After each step: git add -A → review step N with the reviewer
  (Claude Code: "Use the reviewer subagent to review step N"; Kiro: the harness-reviewer agent).
  Commit only after APPROVE: git commit -m "step N: …".
- REJECT → fix → re-review. 3rd REJECT on one step → State: BLOCKED: <reason>, stop.
- Plan assumption proven false → update PLAN.md first, log it in STATUS.md.
- Scope change needed → BLOCKED.
- Never edit dod.sh or GOAL.md after approval. If they're wrong → BLOCKED.
- Never create .harness/active, touch .harness/.approved or .harness/attempts, or run approve.sh.
- Final: reviewer on the full diff vs Base.
  COMPLETE only if dod.sh is green AND the verdict is APPROVE (quote it in STATUS.md).

## dod.sh and review focus by task type
| Task     | dod.sh checks                                   | Reviewer judges                                       |
|----------|-------------------------------------------------|-------------------------------------------------------|
| feature  | lint, typecheck, tests                          | each AC has a test seen failing first; none weakened  |
| bug fix  | repro test + full suite                         | repro failed before fix; root cause, not symptom      |
| refactor | full suite; public API surface unchanged        | no behavior change; diff is structural only           |
| dbt/data | dbt build -s <changed models>+ ; data tests     | grain, join fan-out, nulls, contract changes          |
| document | required headings present; no TODO/TBD/<<FILL;  | audience fit, accuracy, every AC addressed            |
|          | word-count bounds                               |                                                       |
| research | every claim line carries [S#]; every S# exists  | re-fetch 3 random sources; claims actually appear     |
|          | in sources.md                                   |                                                       |

## STATUS.md format
Write these lines at the start of the line (column 0, no indentation): the hooks match `State:` literally.

    State: PLANNING | IN_PROGRESS | BLOCKED: <reason> | COMPLETE
    Step: N/M — Base: <branch>@<sha>
    Last verify (step N): …
    Reviewer (step N): APPROVE | REJECT — rejections n/3 — …
    Next action: …
