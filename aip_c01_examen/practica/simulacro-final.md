# Final Mock & Readiness Gate

This is your dress rehearsal and the honest go/no-go decision for the Dec 15, 2026 exam. Do it in Week 8 (see the W8 checkpoint in [PLAN-ESTRATEGICO.md](../PLAN-ESTRATEGICO.md)).

Back to [course home](../README.md).

## Mock protocol

Simulate the real thing as closely as possible:

- **75 questions in 180 minutes**, timer running, no notes, no pausing.
- **Source mix:** combine the **official AWS practice question set** (the best proxy for real difficulty — see [recursos.md](../recursos.md)) with this course's [question bank](./banco-preguntas.md). The official set matters most; do not judge readiness on this course's bank alone.
- **~2.4 min/question.** Flag anything over ~3 minutes and move on.
- **Leave nothing blank** — unanswered counts as wrong, and there is no guessing penalty.
- After finishing, review **every** wrong answer and trace it back to the relevant [blueprint](../blueprint/00-vision-examen.md) section and the [master constraint table](../tablas-decision/decision-por-restriccion.md).

## Domain-by-domain readiness checklist

Mark a domain "confident" only if you can explain the discriminators out loud without notes.

| Domain | Confident? | Weak areas (fill in) | Review link |
|---|---|---|---|
| D1 — Foundation, Data & Compliance (31%) | - [ ] | | [dominio-1](../blueprint/dominio-1-fundacion-datos.md) |
| D2 — Implementation & Integration (26%) | - [ ] | | [dominio-2](../blueprint/dominio-2-implementacion.md) |
| D3 — AI Safety, Security & Governance (20%) | - [ ] | | [dominio-3](../blueprint/dominio-3-seguridad.md) |
| D4 — Operational Efficiency & Optimization (12%) | - [ ] | | [dominio-4](../blueprint/dominio-4-optimizacion.md) |
| D5 — Testing, Validation & Troubleshooting (11%) | - [ ] | | [dominio-5](../blueprint/dominio-5-testing.md) |

Must-know discriminators to self-quiz (cover the answer, say it aloud):

- [ ] RAG vs fine-tuning; PEFT/LoRA vs full fine-tuning
- [ ] The five vector stores and their decisive keyword each
- [ ] The five deployment modes and their decisive keyword each
- [ ] AgentCore five components (Runtime/Gateway/Memory/Observability/Identity)
- [ ] Guardrails' four layers; ANONYMIZE vs BLOCK; `ApplyGuardrail`
- [ ] PrivateLink + `aws:SourceVpce` for "stay private"
- [ ] Cost levers (caching/routing/cascading/Batch) and latency levers (streaming/Provisioned)
- [ ] RAGAS four metrics and the fix lever for each
- [ ] Exponential backoff with jitter; schema enforcement for JSON
- [ ] Out-of-scope traps (AWS Batch, Lightsail, Transit Gateway, Direct Connect, from-scratch training)

## Scoring self-assessment

You cannot compute your exact scaled score from a practice set — AWS uses a scaled model and 10 unscored items. Use practice **percent correct** as a rough proxy only.

| What you see | How to read it |
|---|---|
| Pass bar | **750 / 1,000 scaled.** Roughly ~70%+ of scored items is a common informal target, but scaling varies — treat it as approximate *(confirm nothing official exists for this mapping)* |
| Compensatory scoring | No per-domain minimum; your **total** is what passes. Shore up the heaviest domains (D1+D2 = 57%) |
| Practice % caveat | A practice percentage is an **estimate**, not the scaled score. Build a margin above the bar, don't aim to just scrape it |
| Per-domain % | Use it to find weak spots, not to predict the result (compensatory) |

**Build a margin:** because practice % is only an estimate and real items can be harder, aim to be **comfortably above** the bar on mixed full-length practice, not exactly at it.

## The honest readiness gate (~Dec 8 decision)

Around **Dec 8, 2026** (one week out), make a deliberate go/no-go call. The $300 and the attempt are real costs — don't gamble them on a coin flip.

| Signal | Decision |
|---|---|
| Consistently scoring **~75%+** on mixed full-length practice (incl. the official set) | **Keep Dec 15.** You have margin above the ~70% proxy bar. |
| Hovering **~65–74%**, trending up week over week | **Borderline.** Keep Dec 15 only if the trend is clearly upward and D1+D2 are solid; otherwise consider a short push. |
| Below **~65%**, or D1/D2 still shaky, or scores flat/declining | **Seriously consider rescheduling.** Burning the attempt now is poor value; a 1–3 week push to close gaps is usually the better bet. |
| Have not completed a full timed 75q/180min mock yet | **Not ready to decide.** Do the full mock first, then re-apply this table. |

Rescheduling is a strategy, not a failure. A later pass beats an on-time fail. Record your decision and, if pushing, pick the new date and re-enter the plan at the weakest domain.

Related: W8 checkpoint in [PLAN-ESTRATEGICO.md](../PLAN-ESTRATEGICO.md) · all [blueprints](../blueprint/00-vision-examen.md) · [resources](../recursos.md).
