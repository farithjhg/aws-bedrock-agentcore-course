---
id: plan-estrategico
sidebar_position: 2
title: 8-Week Strategy Plan
---

Your week-by-week roadmap at **5 hours/week ≈ 40 hours total**, from **Tue Oct 21, 2026** to the exam on **Mon Dec 15, 2026**. This plan drives the whole course — follow it in order and hit the self-test targets.

Honest reminder: 40 hours for a Professional-tier exam from a basic base is a **stretch goal**. The plan is weighted to spend the most time where the most points are (D1 + D2 = 57%) and builds in a real **readiness gate around Dec 8** (see the [final mock](/practica/simulacro-final)).

Back to [course home](/).

## How this plan is weighted

Hours are allocated roughly in proportion to domain weight, plus fixed time for orientation and mock exams.

| Block | Weeks | Hours | Exam weight | Files |
|---|---|---|---|---|
| Orientation + mocks | W1 (≈2.5h) + W8 (≈2.5h) | ~5h | n/a | [README](/), [00-vision-examen](/blueprint/vision-examen), [simulacro-final](/practica/simulacro-final) |
| **D1 — Foundation, Data & Compliance** | W2–W3 | **~11h** | 31% | [dominio-1](/blueprint/dominio-1-fundacion-datos), [vector stores](/tablas-decision/decision-vector-stores) |
| **D2 — Implementation & Integration** | W4–W5 | **~9h** | 26% | [dominio-2](/blueprint/dominio-2-implementacion), [deployment](/tablas-decision/decision-despliegue) |
| **D3 — AI Safety, Security & Governance** | W6 | **~7h** | 20% | [dominio-3](/blueprint/dominio-3-seguridad) |
| **D4 — Operational Efficiency & Optimization** | W7 | **~4h** | 12% | [dominio-4](/blueprint/dominio-4-optimizacion) |
| **D5 — Testing, Validation & Troubleshooting** | W7 | **~4h** | 11% | [dominio-5](/blueprint/dominio-5-testing) |
| **Total** | W1–W8 | **~40h** | 100% | all + [master constraint table](/tablas-decision/decision-por-restriccion) |

The hour split (5 / 11 / 9 / 7 / 4 / 4) tracks the 31 / 26 / 20 / 12 / 11 weighting, with the heaviest domains getting the most time.

---

## Week 1 — Orientation (Tue Oct 21 – Sun Oct 26) · ~2.5h

- **Goal:** understand the exam machinery and how to read scenarios before touching content.
- **Files to study:** [README.md](/), [blueprint/00-vision-examen.md](/blueprint/vision-examen), skim the [master constraint table](/tablas-decision/decision-por-restriccion).
- **Deliverable/checkpoint:** you can state the format (75q/180min/750-pass/compensatory) and list 5 constraint keywords with their first-instinct pattern.
- **Self-test:** do the self-check at the end of [00-vision-examen.md](/blueprint/vision-examen). Target: explain all 7 aloud.

## Week 2 — Domain 1, part 1 (Mon Oct 27 – Sun Nov 2) · ~5.5h

- **Goal:** FM selection, customization (RAG vs fine-tuning, PEFT vs full), data pipelines, chunking, embeddings.
- **Files to study:** [dominio-1](/blueprint/dominio-1-fundacion-datos) (first half through Chunking/Embeddings).
- **Deliverable/checkpoint:** a one-page note on RAG-vs-fine-tuning and the three chunking strategies.
- **Self-test:** [banco-preguntas](/practica/banco-preguntas) D1 Q1–Q6. Target ≥ 4/6.

## Week 3 — Domain 1, part 2 (Mon Nov 3 – Sun Nov 9) · ~5.5h

- **Goal:** vector stores, retrieval quality (hybrid, reranking), prompt engineering/governance, model decoupling.
- **Files to study:** [dominio-1](/blueprint/dominio-1-fundacion-datos) (second half) + the [vector store decision table](/tablas-decision/decision-vector-stores).
- **Deliverable/checkpoint:** memorize the five-store picker (one decisive keyword each).
- **Self-test:** [banco-preguntas](/practica/banco-preguntas) D1 Q7–Q12 + redo any missed in W2. Target ≥ 10/12 across all D1.

## Week 4 — Domain 2, part 1 (Mon Nov 10 – Sun Nov 16) · ~4.5h

- **Goal:** agentic AI (Bedrock Agents, AgentCore components, Strands, ReAct), tool integration (MCP, Action Groups), state/session.
- **Files to study:** [dominio-2](/blueprint/dominio-2-implementacion) (through State & session).
- **Deliverable/checkpoint:** recite the five AgentCore components and their exam cue.
- **Self-test:** [banco-preguntas](/practica/banco-preguntas) D2 Q13–Q18. Target ≥ 4/6. Optional: [Lab 1](/practica/labs-hands-on).

## Week 5 — Domain 2, part 2 (Mon Nov 17 – Sun Nov 23) · ~4.5h

- **Goal:** deployment/inference modes, response streaming, event-driven orchestration, multimodal voice, enterprise integration, Converse API.
- **Files to study:** [dominio-2](/blueprint/dominio-2-implementacion) (rest) + the [deployment decision table](/tablas-decision/decision-despliegue).
- **Deliverable/checkpoint:** memorize the five deployment modes (one decisive keyword each).
- **Self-test:** [banco-preguntas](/practica/banco-preguntas) D2 Q19–Q23 + redo misses. Target ≥ 8/10 across all D2. Optional: [Lab 2](/practica/labs-hands-on) or redeploy [intro_4h_agentcore](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md).

## Week 6 — Domain 3 (Mon Nov 24 – Sun Nov 30) · ~7h

- **Goal:** Guardrails (four layers, ANONYMIZE vs BLOCK, `ApplyGuardrail`), network isolation (PrivateLink, IAM conditions), auditing/lineage, bias/drift, encryption/PII.
- **Files to study:** [dominio-3](/blueprint/dominio-3-seguridad).
- **Deliverable/checkpoint:** the four Guardrail layers and the "stay private" pattern (PrivateLink + `aws:SourceVpce`) from memory.
- **Self-test:** [banco-preguntas](/practica/banco-preguntas) D3 Q24–Q33. Target ≥ 8/10. Optional: [Lab 3](/practica/labs-hands-on).

## Week 7 — Domains 4 & 5 (Mon Dec 1 – Sun Dec 7) · ~8h (≈4h + ≈4h)

- **Goal:** D4 cost/latency levers + observability triad + throttling; D5 RAGAS metrics, judging, regression testing, structured output, resilience.
- **Files to study:** [dominio-4](/blueprint/dominio-4-optimizacion) and [dominio-5](/blueprint/dominio-5-testing).
- **Deliverable/checkpoint:** cost-lever and RAGAS metric→fix tables from memory.
- **Self-test:** [banco-preguntas](/practica/banco-preguntas) D4 Q34–Q41 and D5 Q42–Q49. Target ≥ 6/8 each.

## Week 8 — Final review, full mock & readiness gate (Mon Dec 8 – Mon Dec 15) · ~2.5h + exam

- **Goal:** consolidate, run a full timed mock, make the go/no-go call, then sit the exam.
- **Files to study:** [simulacro-final](/practica/simulacro-final); re-skim every [blueprint](/blueprint/vision-examen) "Exam traps" section and the [master constraint table](/tablas-decision/decision-por-restriccion).
- **Deliverable/checkpoint:** one full **75q / 180min** mock (official practice set + this bank), reviewed.
- **Readiness gate (~Dec 8):** apply the gate table in [simulacro-final.md](/practica/simulacro-final). If not trending to a pass, seriously consider rescheduling rather than burning the $300 attempt.
- **Exam:** Mon Dec 15, 2026 *(confirm your exact date/time at registration)*.
- **Self-test:** full mock scored; weak domains re-reviewed before exam day.

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

Start studying: [blueprint/00-vision-examen.md](/blueprint/vision-examen). Memorize: [master constraint table](/tablas-decision/decision-por-restriccion). Rehearse: [question bank](/practica/banco-preguntas) → [final mock](/practica/simulacro-final).
