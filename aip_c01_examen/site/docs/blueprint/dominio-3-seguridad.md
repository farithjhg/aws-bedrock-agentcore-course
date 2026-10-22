---
id: dominio-3-seguridad
sidebar_position: 4
title: Domain 3 — AI Safety, Security & Governance (20%)
---

A fifth of the exam. You know Guardrails, IAM, and encryption exist — this is which control matches which cue, and the near-neighbor confusions.

Back to [course home](/) · overlaps [Domain 1](/blueprint/dominio-1-fundacion-datos) · grounding ties to [Domain 5](/blueprint/dominio-5-testing).

## Guardrails — four layers (the discriminator)

| Layer | What it catches | Exam cue |
|---|---|---|
| **Content Filters** | Harmful categories + **Prompt Attacks** (jailbreak/injection) | "block toxic content", "stop prompt injection/jailbreak" |
| **Denied Topics & Word Filters** | Topics/words you forbid | "the bot must never discuss X" |
| **Sensitive Information Filters (PII)** | Native PII patterns or custom **Comprehend**; ANONYMIZE or BLOCK | "redact/mask PII", "don't expose personal data" |
| **Contextual Grounding** | Ungrounded output vs source chunks | "stop it making up facts not in the sources" |

**ANONYMIZE, not BLOCK** — when you still need a usable answer (mask the PII). **BLOCK, not ANONYMIZE** — when policy forbids processing at all.

**`ApplyGuardrail`** — the standalone API that applies the same policy to **non-Bedrock / self-hosted** models. Cue: "same safety policy across different models."

## Discriminators (pick X, not Y)

- **PrivateLink interface VPC endpoints + IAM `aws:SourceVpce`, not public endpoint + IP allow-list / NAT** — for "must stay private, no public internet".
- **Macie, not Guardrails PII** — for PII *at rest* in S3. **Guardrails PII, not Macie** — for PII *in-flight*.
- **SageMaker Clarify = bias/drift, not a safety filter** — don't confuse with Guardrails.
- **Region / inference-profile choice, not a Guardrail setting** — for data residency.
- **Contextual Grounding (prevent) vs RAGAS Faithfulness (measure)** — same hallucination problem, different stage ([Domain 5](/blueprint/dominio-5-testing)).

## Audit / compliance combo (one answer, four parts)

"We need a compliance/audit trail of model usage" → **Model Invocation Logging** (to S3/CloudWatch) + **CloudTrail** (who called what) + **AWS Audit Manager** (evidence vs frameworks) + **model cards** (governance metadata).

## One-liners

- **IAM least-privilege** with resource-level permissions and conditions (`aws:SourceVpce`, `aws:SourceIp`).
- **KMS** encrypts at rest; TLS in transit.
- **Human-in-the-loop** for sensitive/low-confidence outputs (pairs with Step Functions human-review, [D2](/blueprint/dominio-2-implementacion)).
- Contextual Grounding adds a validation pass → extra latency; pair with streaming if interactive ([D2](/blueprint/dominio-2-implementacion)), watch cost ([D4](/blueprint/dominio-4-optimizacion)).

## Traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "no public internet / stay private" | PrivateLink + `aws:SourceVpce` | public endpoint + IP list, NAT |
| "mask PII but keep a usable answer" | ANONYMIZE | BLOCK |
| "same policy on a non-Bedrock model" | `ApplyGuardrail` | configure per model |
| "find PII in our S3 buckets" | Macie | Guardrails (in-flight only) |
| "jailbreak / prompt injection" | Content Filters → Prompt Attacks | Grounding / PII filter |
| "bias and drift reporting" | SageMaker Clarify | Guardrails |
| "keep inference in the EU" | region / EU inference profile | a Guardrail setting |

Reuse note: `intro_4h_agentcore` uses an **EU inference profile** (`eu.` prefix) for data residency and a **least-privilege IAM** role in its Terraform — concrete D3 examples.

## Self-check

1. Which Guardrail layer stops facts not in the retrieved sources?
2. Keep Bedrock traffic off the public internet — networking construct + IAM condition?
3. Hide customer emails but still answer: ANONYMIZE or BLOCK?
4. Apply one policy to a self-hosted non-Bedrock model — how?
5. What combination gives a compliance/audit trail of invocations?
6. Macie vs Guardrails PII — where does each act?
7. Which service detects bias and drift?

Confirm on AWS docs: current Guardrails filter categories and PII actions.

Decision table: [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
