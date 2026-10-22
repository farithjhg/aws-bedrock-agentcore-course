---
id: decision-despliegue
sidebar_position: 3
title: Deployment & Inference Modes
---

How you serve a model drives cost, latency, and operational effort. AIP-C01 tests whether you can match an inference mode to a workload's constraint. Memorize this table alongside the [master constraint table](/tablas-decision/decision-por-restriccion).

Back to [course home](/) · [Domain 2](/blueprint/dominio-2-implementacion) · [Domain 4](/blueprint/dominio-4-optimizacion).

## The table

| Mode | Cost structure | Latency / throughput | Ideal workload | Pick when | Avoid when |
|---|---|---|---|---|---|
| **On-Demand** | Pay per token/request, no commitment | Good, but subject to throttling under load | Bursty, low/medium volume, unpredictable traffic | "Variable traffic", "no commitment", "simplest to start" | Sustained high volume needing guaranteed low latency |
| **Provisioned Throughput** | Reserved **model units** at a fixed cost | Consistent low latency, **no cold starts**, guaranteed capacity | Mission-critical, steady, high-volume, latency-sensitive | "Guaranteed throughput", "no throttling", "consistent low latency", "no cold start" | Spiky or low-volume traffic — you pay for idle reserved capacity |
| **SageMaker endpoints (incl. Serverless Inference)** | Pay for endpoint/compute; Serverless scales to zero | Real-time; **Serverless Inference** has cold starts when scaled to zero | Hosting **custom or open-source model weights** not in the Bedrock catalog | "Custom/fine-tuned weights", "open-source model we host", "scale to zero to save cost" | A Bedrock-catalog model would do (managed On-Demand is less work) |
| **Batch Inference API (Bedrock)** | Discounted async bulk pricing *(confirm % in AWS docs; often cited ~50%)* | Not real-time; results within an SLA window (e.g., up to ~24h — *confirm in docs*) | Large, **non-real-time** jobs: bulk summarization, offline enrichment, embeddings backfill | "Nightly/offline job", "thousands of records", "cost over speed" | Interactive/real-time responses |
| **Model Cascading** | Pay small-model cost for easy cases, large-model cost only for hard ones | Fast+cheap for the majority; escalates on confidence threshold | Mixed difficulty where most requests are simple | "Most requests are easy", "cut cost without losing quality on hard cases" | Every request genuinely needs the top model |

## Keyword cues

| Keyword in the scenario | Mode |
|---|---|
| "variable / unpredictable traffic", "just getting started" | On-Demand |
| "guaranteed capacity", "no cold start", "consistent low latency", "mission-critical" | Provisioned Throughput |
| "host our own fine-tuned / open-source weights", "scale to zero" | SageMaker endpoints / Serverless Inference |
| "offline", "bulk", "overnight", "cost over latency" | Batch Inference API |
| "most queries simple, a few complex", "reduce cost but keep quality" | Model Cascading |

## Common distractor traps

- **Provisioned Throughput for spiky traffic** is the classic wrong answer — you pay for reserved capacity that sits idle. It wins only for steady, latency-critical load.
- **Batch Inference API ≠ AWS Batch.** AWS Batch is a generic compute service and is **out of scope**. The Bedrock **Batch Inference API** is the discounted async model-inference path. The exam places both near each other on purpose.
- **SageMaker endpoint vs Bedrock On-Demand:** only reach for SageMaker when you host **custom/open-source weights**. If a Bedrock-catalog model fits, SageMaker is extra effort and usually the distractor.
- **Serverless Inference cold starts:** if the stem demands *always-on sub-second latency*, scale-to-zero Serverless Inference is a trap because of cold starts — Provisioned Throughput fits better.

Practice: [question bank](/practica/banco-preguntas).
