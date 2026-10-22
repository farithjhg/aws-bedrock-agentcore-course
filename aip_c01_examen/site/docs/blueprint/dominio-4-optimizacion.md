---
id: dominio-4-optimizacion
sidebar_position: 5
title: Domain 4 — Operational Efficiency & Optimization (12%)
---

Billed by **input + output tokens**. Every cost lever sends fewer tokens, caches them, or routes to a cheaper model. Every latency lever cuts time-to-first-token or reserves capacity.

Back to [course home](/) · deployment choices in [Domain 2](/blueprint/dominio-2-implementacion) · shared backoff with [Domain 5](/blueprint/dominio-5-testing).

## Cost levers

| Lever | What it reduces | Exam cue keyword |
|---|---|---|
| **Prompt Caching** | Re-billing of static prefix (system prompt / few-shot) | "same long system prompt every call" |
| **Intelligent Prompt Routing** | Using a big model for easy work — routes to cheapest capable | "route to right/cheapest model" |
| **Semantic / deterministic cache (ElastiCache)** | Re-running repeated queries | "cache repeated answers" |
| **Batch Inference API** | Per-token cost on non-real-time bulk *(confirm discount % in docs)* | "offline", "bulk", "cost over latency" |
| **Model Cascading** | Always using the top model | "escalate only hard cases" |

Cost question → think **cache** (prompt/semantic), **route** (Routing/Cascading), or **batch** (async discount).

## Latency levers

| Lever | What it improves | Note |
|---|---|---|
| **Response streaming** | TTFT / perceived latency | Does NOT reduce total tokens or cost |
| **Provisioned Throughput** | Consistent latency, no cold starts | Costs even when idle — wrong for spiky traffic |
| **Prompt compression** | Total tokens → faster gen | Trim redundant context |

## Observability triad

| Tool | Use for | Discriminator cue |
|---|---|---|
| **CloudWatch Metrics** | Token counts, throttle/error alarms, spend | "alert when throttling spikes" |
| **X-Ray** | Distributed traces (API GW → Lambda → vector → Bedrock) | "find which hop is slow" |
| **Model Invocation Logging** | Full prompt/response records (also D3 audit) | "debug quality per call" |

## Provisioned vs On-Demand

| | Provisioned | On-Demand |
|---|---|---|
| Cost | Fixed — pays for idle | Pay per token |
| Latency | Consistent, no cold start | Can throttle under load |
| Best for | Steady, high-volume, latency-critical | Bursty, variable |
| **Trap** | Spiky traffic → paying for idle | Sustained heavy → throttling |

## Throttling mitigation

**Exponential backoff with jitter** (jitter is the point — avoids synchronized retry storm) + **fallback endpoints** (secondary model/region) + **Provisioned Throughput** (guaranteed capacity).

## Traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "same 3k-token prefix every call, cut cost" | Prompt Caching | smaller model / Batch |
| "mixed difficulty, cut cost" | Intelligent Prompt Routing / Cascading | always-top model |
| "offline/bulk, cost matters" | Batch Inference API *(confirm %)* | Provisioned |
| "chat feels slow to start" | streaming (TTFT) | Provisioned (doesn't fix perceived latency) |
| "which hop is slow?" | X-Ray | CloudWatch metrics alone |
| "ThrottlingException / 429" | exponential backoff **with jitter** | tight-loop retry |
| "Provisioned Throughput + spiky traffic" | wrong pairing (paying for idle) | On-Demand fits |
| "does streaming cut cost?" | No — it's perceived latency only | — |

## Self-check

1. Every call sends the same 2k-token system prompt — cheapest lever?
2. Which tool tells you which hop in a multi-step pipeline is slow?
3. Nightly job, 100k documents, latency irrelevant — which mode?
4. What does jitter add to exponential backoff, and why?
5. When is Provisioned Throughput the wrong choice despite its low latency?
6. Does streaming reduce total token cost?
7. Which lever routes each request to the cheapest capable model?

Confirm on AWS docs: current Batch Inference discount and Provisioned Throughput pricing.

Decision tables: [deployment](/tablas-decision/decision-despliegue) · [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
