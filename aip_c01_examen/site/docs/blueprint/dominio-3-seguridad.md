---
id: dominio-3-seguridad
sidebar_position: 4
title: Domain 3 — AI Safety, Security & Governance (20%)
---

A fifth of the exam. It covers keeping GenAI apps safe (Guardrails), private (networking + IAM), auditable (logging + lineage), and responsible (bias/drift). Many answers here are "add the managed safety control."

Back to [course home](/) · compliance overlaps [Domain 1](/blueprint/dominio-1-fundacion-datos) · grounding ties to [Domain 5](/blueprint/dominio-5-testing).

## Bedrock Guardrails

**Amazon Bedrock Guardrails** is a unified safety layer that checks **both inbound prompts and outbound model outputs** against policies you configure. It works across any Bedrock model, and via the standalone **`ApplyGuardrail` API** you can apply the same guardrail to **external or self-hosted models** too. This decoupling is a common exam cue: "apply the same safety policy across different models, including non-Bedrock ones" → `ApplyGuardrail`.

## The four Guardrail layers

| Layer | What it catches | Key config | Exam cue |
|---|---|---|---|
| **1. Content Filters** | Harmful categories: Hate, Insults/Harassment, Sexual, Violence, Misconduct, and **Prompt Attacks** (jailbreak/prompt-injection) | Configurable strength thresholds per category | "block toxic content", "stop prompt injection/jailbreak" |
| **2. Denied Topics & Word Filters** | Topics or specific words you forbid | Define topics by name/description; word/phrase lists | "the bot must never discuss X topic" |
| **3. Sensitive Information Filters (PII)** | Personal data — native PII patterns or **custom Amazon Comprehend** entity recognizers | Action = **ANONYMIZE** (mask) or **BLOCK** (halt) | "redact/mask PII", "do not expose personal data" |
| **4. Contextual Grounding Checks** | Hallucinations — validates the output against the **source chunks** and the query | Grounding + relevance thresholds | "stop the model making up facts not in the sources" |

### ANONYMIZE vs BLOCK

| Action | Behavior | When to use |
|---|---|---|
| **ANONYMIZE** | Masks the detected PII (e.g., replaces with a tag) but lets the response continue | You still need a usable answer; preserve utility while hiding personal data |
| **BLOCK** | Halts and returns an error/blocked message | Policy forbids processing the request at all if PII is present |

> **Recap:** four layers — Content Filters (incl. Prompt Attacks), Denied Topics/Words, PII filters (ANONYMIZE vs BLOCK), Contextual Grounding (anti-hallucination). `ApplyGuardrail` extends them to non-Bedrock models.

## Network isolation

- **Interface VPC Endpoints via AWS PrivateLink** — reach Bedrock over private AWS networking so traffic never crosses the public internet. This is the canonical "must stay private / no public internet" answer.
- **IAM least-privilege** — grant only the actions/resources needed, with **resource-level permissions** and **conditions** such as `aws:SourceVpce` (allow only calls coming through your VPC endpoint) or `aws:SourceIp`.

> **Trap:** for "keep Bedrock traffic private," PrivateLink interface endpoints beat distractors like NAT gateways or public endpoints with IP allow-lists.

## Auditing & lineage

- **Model Invocation Logging** — log all Bedrock prompts/responses/metadata to **Amazon S3** and/or **CloudWatch** for audit and debugging.
- **AWS CloudTrail** — records the API calls (who did what, when) across your account.
- **AWS Audit Manager** — continuously collects evidence to map your controls to compliance frameworks.
- **Model cards** — documented model metadata (intended use, limitations) for governance/lineage.

Together these answer "we need a compliance/audit trail of model usage."

## Bias, drift & responsible AI

- **Amazon SageMaker Clarify** — detects **bias** and **drift** and supports responsible/ethical-AI reporting.
- **Transparency** — document data sources, limitations (model cards).
- **Human-in-the-loop** — route sensitive or low-confidence outputs to a human for review (pairs with Step Functions human-review steps in [D2](/blueprint/dominio-2-implementacion)).

## Encryption & PII at rest

- **AWS KMS** — encrypt data at rest and manage keys; TLS for data in transit.
- **Amazon Macie** — discovers and classifies **PII stored in S3** (finds personal data sitting in your data stores, complementing Guardrails which act in-flight).

> **Ripple-effect callout:** Contextual Grounding checks add inference latency (an extra validation pass). If the app is interactive, pair it with **response streaming** ([D2](/blueprint/dominio-2-implementacion)) to protect perceived latency, and watch cost ([D4](/blueprint/dominio-4-optimizacion)).

> **Reuse note:** the companion repo `../../intro_4h_agentcore/` uses an **EU inference profile** (`eu.` prefix) to keep inference in-region — a concrete **data-residency** example — plus a **least-privilege IAM** role in its Terraform. Good real examples of D3 patterns.

## Exam traps & key discriminators

- **"Private / no public internet"** → **PrivateLink interface VPC endpoints** + IAM `aws:SourceVpce`, not public endpoints or NAT.
- **ANONYMIZE vs BLOCK:** mask to preserve a usable answer; block to refuse outright.
- **Prompt injection / jailbreak** → Guardrails **Content Filters → Prompt Attacks**.
- **Hallucination** → Guardrails **Contextual Grounding** (prevention) and **RAGAS Faithfulness** (measurement in D5).
- **Macie vs Guardrails PII:** Macie finds PII **at rest** in stores; Guardrails filters PII **in-flight**.
- **Same policy across non-Bedrock models** → standalone **`ApplyGuardrail` API**.
- **Clarify** = bias/drift, not a safety filter — don't confuse it with Guardrails.
- **Data residency** → region/inference-profile choice (plus KMS/PrivateLink), not a Guardrail setting.

## Self-check (5–8 questions)

1. Which Guardrail layer stops the model from inventing facts not in the retrieved sources?
2. You must keep Bedrock traffic off the public internet. Which networking construct, and which IAM condition reinforces it?
3. A response must hide customer emails but still return a useful answer. ANONYMIZE or BLOCK?
4. How do you apply one guardrail policy to a self-hosted (non-Bedrock) model?
5. What combination produces a compliance/audit trail of model invocations?
6. Macie vs Guardrails PII filters — what is the difference in where they act?
7. Which service detects bias and drift for responsible-AI reporting?

Decision table: [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
