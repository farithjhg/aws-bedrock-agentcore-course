---
id: intro
slug: /
sidebar_position: 1
title: AIP-C01 Exam-Prep Course
---

A **teach-by-example** course for the **AWS Certified Generative AI Developer – Professional (AIP-C01)** exam. Instead of a wall of definitions or a deck of "pick-X-not-Y" flashcards, this course teaches each concept from zero up to exam-level decision skill — so you finish able to explain it, sketch an implementation, and choose the right service under a new constraint.

## One running project, five domains

Every chapter builds the same system: the **Northwind Support Assistant**, a production generative-AI customer-support assistant that **Northwind Retail** (a mid-to-large retailer) is building on AWS. You watch one project mature step by step instead of reading five disconnected topic dumps:

- **[Domain 1](/blueprint/dominio-1-fundacion-datos) — give it KNOWLEDGE:** choose a foundation model, build RAG over Northwind's own support docs, pick a vector store, govern the prompts.
- **[Domain 2](/blueprint/dominio-2-implementacion) — make it ACT:** turn it into an agent with tools, choose how to deploy and stream responses, orchestrate multi-step jobs.
- **[Domain 3](/blueprint/dominio-3-seguridad) — make it SAFE:** add Guardrails, isolate the network, handle PII, set up audit and lineage.
- **[Domain 4](/blueprint/dominio-4-optimizacion) — make it CHEAP and FAST:** add caching, routing/cascading, batch inference, and observability.
- **[Domain 5](/blueprint/dominio-5-testing) — PROVE it works:** measure quality with RAGAS, add regression testing and fault-tolerant patterns.

## The teaching method

Every major concept is taught with the same four-part arc, so understanding comes before the verdict:

1. **Concept** — plain-language explanation and the mental model: what it is and why it exists.
2. **Example** — a concrete moment in the Northwind story that makes the idea tangible.
3. **Implementation** — real, runnable AWS code (mostly Python `boto3`) plus a short architecture sketch.
4. **When and Why** — the decision logic: when to use it, when not to, and how to choose against the near-neighbor alternative.

The terse discriminator tables still exist — but as **end-of-chapter recaps** of what the prose already taught, not as the teaching itself.

## Honest framing

AIP-C01 is Professional-tier. Starting from a basic base at ~**5h/week**, Oct 21 → **Dec 15, 2026** is a genuine **stretch goal**. A built-in **readiness gate** around Dec 8 tells you plainly whether to sit or reschedule ([final mock](/practica/simulacro-final)).

## Exam at a glance

| Attribute | Value |
|---|---|
| Exam code / level | AIP-C01 / Professional |
| Questions | 75 (65 scored + 10 unscored pretest) |
| Time | 180 min (~2.4 min/question) |
| Cost | `$300 USD` *(confirm current price at registration)* |
| Pass | 750 on a 100–1,000 scaled range |
| Scoring | Compensatory (no per-domain minimum) |
| Question types | Multiple choice (1 of 4); multiple response (2+ of 5+, all required, no partial credit) |
| Blank answers | Count as incorrect; no guessing penalty |

Full mechanics and scenario-reading discipline: [exam strategy](/blueprint/vision-examen).

## Domain weights

| Domain | Name | Weight |
|---|---|---|
| D1 | Foundation, Data & Compliance | 31% |
| D2 | Implementation & Integration | 26% |
| D3 | AI Safety, Security & Governance | 20% |
| D4 | Operational Efficiency & Optimization | 12% |
| D5 | Testing, Validation & Troubleshooting | 11% |

**D1 + D2 = 57%** — more than half your effort goes there.

## How to use this course

1. **Start with the [8-week plan](/plan-estrategico)** — it paces the whole journey.
2. **Work the teaching chapters in order** — [D1](/blueprint/dominio-1-fundacion-datos), [D2](/blueprint/dominio-2-implementacion), [D3](/blueprint/dominio-3-seguridad), [D4](/blueprint/dominio-4-optimizacion), [D5](/blueprint/dominio-5-testing). Read each four-part arc; the recap tables at the end are for review, not first contact.
3. **Keep the decision tables nearby** as quick reference after a chapter teaches the reasoning — [by constraint (master)](/tablas-decision/decision-por-restriccion), [vector stores](/tablas-decision/decision-vector-stores), [deployment modes](/tablas-decision/decision-despliegue).
4. **Rehearse** — [question bank](/practica/banco-preguntas) → [final mock](/practica/simulacro-final). Optional [hands-on labs](/practica/labs-hands-on) mirror the Northwind build steps.
5. **Then extend on official prep** — [resources](/recursos).

This course is a **base layer**: it teaches you the concepts and the reasoning here, and it pairs naturally with **AWS Skill Builder** and the official exam guide for breadth and the official practice set. Learn it here first; confirm live specifics and drill the official set there.

All practice questions are **original**; this course does not reproduce real exam items. It avoids inventing exact figures — where a number could drift, it flags "confirm in current AWS docs."
