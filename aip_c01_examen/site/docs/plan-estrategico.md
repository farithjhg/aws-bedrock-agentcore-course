---
id: plan-estrategico
sidebar_position: 2
title: 8-Week Strategy Plan
---

Week-by-week roadmap at **5h/week ≈ 40h total**, **Tue Oct 21 → Mon Dec 15, 2026**. 40 hours from a basic base is a **stretch goal**, weighted to spend the most time where the points are (D1 + D2 = 57%), with a **readiness gate ~Dec 8** ([final mock](/practica/simulacro-final)).

Each week you **work through a teach-by-example chapter** (Concept → Example → Implementation → When/Why) following the Northwind Support Assistant build, then rehearse with the question bank. Run this course as your **base layer** and the **AWS Skill Builder** official practice set as the parallel/next track — see [resources](/recursos).

Back to [course home](/).

## How this plan is weighted

Hours track domain weight, plus fixed time for orientation and mocks.

| Block | Weeks | Hours | Exam weight | Files |
|---|---|---|---|---|
| Orientation + mocks | W1 (≈2.5h) + W8 (≈2.5h) | ~5h | n/a | [home](/), [exam strategy](/blueprint/vision-examen), [final mock](/practica/simulacro-final) |
| **D1 — Foundation, Data & Compliance** | W2–W3 | **~11h** | 31% | [dominio-1](/blueprint/dominio-1-fundacion-datos), [vector stores](/tablas-decision/decision-vector-stores) |
| **D2 — Implementation & Integration** | W4–W5 | **~9h** | 26% | [dominio-2](/blueprint/dominio-2-implementacion), [deployment](/tablas-decision/decision-despliegue) |
| **D3 — AI Safety, Security & Governance** | W6 | **~7h** | 20% | [dominio-3](/blueprint/dominio-3-seguridad) |
| **D4 — Operational Efficiency & Optimization** | W7 | **~4h** | 12% | [dominio-4](/blueprint/dominio-4-optimizacion) |
| **D5 — Testing, Validation & Troubleshooting** | W7 | **~4h** | 11% | [dominio-5](/blueprint/dominio-5-testing) |
| **Total** | W1–W8 | **~40h** | 100% | all + [master constraint table](/tablas-decision/decision-por-restriccion) |

The hour split (5 / 11 / 9 / 7 / 4 / 4) tracks the 31 / 26 / 20 / 12 / 11 weighting, with the heaviest domains getting the most time.

---

## Week 1 — Orientation (Tue Oct 21 – Sun Oct 26) · ~2.5h

- **Study:** read [exam strategy](/blueprint/vision-examen) and practice the four-step scenario read; skim the [master constraint table](/tablas-decision/decision-por-restriccion) to see where each chapter will land.
- **Checkpoint:** state the format (75q/180min/750/compensatory) and 5 constraint keywords with their first-instinct pattern.
- **Self-test:** the [exam-strategy](/blueprint/vision-examen) self-check, all aloud.

## Week 2 — Domain 1, part 1 (Mon Oct 27 – Sun Nov 2) · ~5.5h

- **Study:** work the [Domain 1](/blueprint/dominio-1-fundacion-datos) arcs — RAG vs fine-tuning, the model-family contrast, chunking — following the Northwind knowledge build.
- **Checkpoint:** RAG-vs-fine-tuning and the three chunking strategies from memory.
- **Self-test:** [question bank](/practica/banco-preguntas) D1 Q1–Q6. Target ≥ 4/6.

## Week 3 — Domain 1, part 2 (Mon Nov 3 – Sun Nov 9) · ~5.5h

- **Study:** finish the [Domain 1](/blueprint/dominio-1-fundacion-datos) arcs, then use the [vector store table](/tablas-decision/decision-vector-stores) to review the reasoning the chapter taught.
- **Checkpoint:** the five-store picker (one decisive keyword each).
- **Self-test:** [question bank](/practica/banco-preguntas) D1 Q7–Q12 + redo misses. Target ≥ 10/12 across D1.

## Week 4 — Domain 2, part 1 (Mon Nov 10 – Sun Nov 16) · ~4.5h

- **Study:** work the [Domain 2](/blueprint/dominio-2-implementacion) arcs — AgentCore components, tools, state — as the assistant learns to ACT.
- **Checkpoint:** the five AgentCore components and each cue.
- **Self-test:** [question bank](/practica/banco-preguntas) D2 Q13–Q18. Target ≥ 4/6. Optional: [Lab 1](/practica/labs-hands-on).

## Week 5 — Domain 2, part 2 (Mon Nov 17 – Sun Nov 23) · ~4.5h

- **Study:** finish the [Domain 2](/blueprint/dominio-2-implementacion) arcs, then review with the [deployment table](/tablas-decision/decision-despliegue).
- **Checkpoint:** the five deployment modes (one decisive keyword each).
- **Self-test:** [question bank](/practica/banco-preguntas) D2 Q19–Q23 + redo misses. Target ≥ 8/10 across D2. Optional: [Lab 2](/practica/labs-hands-on) or redeploy [the AgentCore repo](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md).

## Week 6 — Domain 3 (Mon Nov 24 – Sun Nov 30) · ~7h

- **Study:** work the [Domain 3](/blueprint/dominio-3-seguridad) arcs as the assistant is made SAFE.
- **Checkpoint:** the four Guardrail layers and the "stay private" pattern (PrivateLink + `aws:SourceVpce`).
- **Self-test:** [question bank](/practica/banco-preguntas) D3 Q24–Q33. Target ≥ 8/10. Optional: [Lab 3](/practica/labs-hands-on).

## Week 7 — Domains 4 & 5 (Mon Dec 1 – Sun Dec 7) · ~8h (≈4h + ≈4h)

- **Study:** work the [Domain 4](/blueprint/dominio-4-optimizacion) arcs (make it CHEAP and FAST) and the [Domain 5](/blueprint/dominio-5-testing) arcs (PROVE it works).
- **Checkpoint:** cost-lever and RAGAS metric→fix tables from memory.
- **Self-test:** [question bank](/practica/banco-preguntas) D4 Q34–Q41 and D5 Q42–Q49. Target ≥ 6/8 each.

## Week 8 — Review, full mock & gate (Mon Dec 8 – Mon Dec 15) · ~2.5h + exam

- **Study:** [final mock](/practica/simulacro-final); re-skim each chapter's end-of-chapter "Exam traps & discriminators" recap and the [master constraint table](/tablas-decision/decision-por-restriccion).
- **Deliverable:** one full **75q / 180min** mock (official set + this bank), reviewed.
- **Readiness gate (~Dec 8):** apply the gate table in the [final mock](/practica/simulacro-final). If not trending to a pass, consider rescheduling over burning the `$300` attempt.
- **Exam:** Mon Dec 15, 2026 *(confirm your date/time at registration)*.

---

## Weekly tracker

| Week | Dates | Focus | Hours | Done |
|---|---|---|---|---|
| W1 | Oct 21–26 (start Tue Oct 21) | Orientation + strategy | ~2.5h | - [ ] |
| W2 | Oct 27 – Nov 2 | D1 part 1 | ~5.5h | - [ ] |
| W3 | Nov 3–9 | D1 part 2 + vector stores | ~5.5h | - [ ] |
| W4 | Nov 10–16 | D2 part 1 (agents/tools) | ~4.5h | - [ ] |
| W5 | Nov 17–23 | D2 part 2 (deploy/stream) | ~4.5h | - [ ] |
| W6 | Nov 24–30 | D3 (security/governance) | ~7h | - [ ] |
| W7 | Dec 1–7 | D4 + D5 | ~8h | - [ ] |
| W8 | Dec 8–15 | Review + full mock + gate + exam | ~2.5h + exam | - [ ] |
| | | **Total** | **~40h** | |

Start: [exam strategy](/blueprint/vision-examen). Memorize: [master constraint table](/tablas-decision/decision-por-restriccion). Rehearse: [question bank](/practica/banco-preguntas) → [final mock](/practica/simulacro-final).
