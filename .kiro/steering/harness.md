# Harness

- If ./.harness/STATUS.md exists and State is not COMPLETE, read .claude/harness/PROTOCOL.md and the status before doing anything else.
- Only the human arms the gate: never create .harness/active, edit .harness/.approved or .harness/attempts, or run approve.sh. A PreToolUse guard hook blocks these; do not try to work around it.
- Start a harnessed task with the `harness` skill (/harness <goal>).

## Kiro specifics
- Kiro's Stop hook cannot block you, so you enforce the gate yourself. While `.harness/active` exists, before ending any turn run:
  `bash .claude/harness/gate.sh < /dev/null`
  Exit 0 → you may stop. Non-zero → keep working, or set `State: BLOCKED: <reason>` in .harness/STATUS.md and stop.
- Reviews: delegate to the `harness-reviewer` custom agent (e.g. run_workflow with `agent://harness-reviewer`), never review your own step. Commit only after its VERDICT: APPROVE.
- Harness tasks run in this session; do not delegate the harness steps themselves to workflows, because the gate and STATUS.md belong to this session.
