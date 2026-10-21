---
id: blueprint/dominio-4-optimizacion
sidebar_position: 5
title: Domain 4 — Operational Efficiency & Optimization (12%)
---

A smaller but high-yield domain: cutting **cost** and **latency**, and observing the system. GenAI billing is pay-per-token, so most optimization is about using fewer/cheaper tokens or reserving capacity.

Back to [course home](/) · deployment choices in [Domain 2](/blueprint/dominio-2-implementacion) · shared backoff with [Domain 5](/blueprint/dominio-5-testing).

## The pay-per-token cost model

You are billed by **input + output tokens** (a token ≈ a word fragment). Every optimization reduces to: send fewer tokens, generate fewer tokens, cache repeats, or route to a cheaper model. Adopt a **token-reduction mindset** when you read a cost question.

## Cost levers

| Lever | What it reduces | Best-fit workload | Exam cue keyword |
|---|---|---|---|
| **Prompt Caching** | Re-billing of static prompt prefixes (system prompt, long context, few-shot examples) | Repeated calls sharing a large static prefix | "same long system prompt every call" |
| **Intelligent Prompt Routing** | Cost of using a big model for easy work — routes each request to the cheapest capable model (e.g., Nova Lite for classification vs Claude Sonnet for complex) | Mixed-difficulty traffic | "route to the right/cheapest model automatically" |
| **Semantic / deterministic caching (ElastiCache)** | Re-running identical or near-identical queries | FAQ-style repeated questions | "cache repeated/similar answers" |
| **Batch Inference API** | Per-token cost for non-real-time bulk jobs (async discount — *confirm % in docs, often cited ~50%*) | Overnight/offline bulk processing | "offline", "bulk", "cost over latency" |
| **Model Cascading** | Cost of always using the top model | Most requests simple, few hard | "escalate only hard cases" |

> **Recap:** cost question → think *cache* (prompt/semantic), *route* (Intelligent Prompt Routing/cascading), or *batch* (async discount). Pick by whether work is repeated, mixed-difficulty, or offline.

## Latency levers

| Lever | What it improves | Notes |
|---|---|---|
| **Response streaming** | Time-to-first-token (TTFT), perceived latency | Stream tokens as generated; see [D2](/blueprint/dominio-2-implementacion) |
| **Provisioned Throughput** | Consistent latency, no cold starts | Reserved capacity; costs even when idle |
| **Prompt compression** | Total tokens → faster generation | Trim redundant context without losing meaning |

**Metrics to know:** **TTFT** (how fast the first token appears) and **token generation rate** (tokens/second). Streaming helps TTFT; it does not reduce total tokens.

## Observability triad

| Tool | What it gives you | Use for |
|---|---|---|
| **Amazon CloudWatch Metrics** | Token counts, invocation counts, throttling/error metrics, alarms | Spot throttling, track spend/volume |
| **AWS X-Ray** | Distributed traces across API Gateway → Lambda → vector search → Bedrock | Isolate *where* latency is spent (which hop is slow) |
| **Model Invocation Logging** | Full prompt/response records (also a D3 audit tool) | Debug quality and cost per call |

**Discriminator:** "find which component is the bottleneck in a multi-step GenAI pipeline" → **X-Ray** distributed tracing. "Alert when throttling spikes" → **CloudWatch** alarm.

## Throttling mitigation

When Bedrock returns throttling/`429`:

- **Exponential backoff with jitter** — retry with growing, randomized delays to avoid a synchronized retry storm (thundering herd). Shared with [D5 resilience](/blueprint/dominio-5-testing).
- **Fallback endpoints** — fail over to a secondary model/region.
- **Provisioned Throughput** — reserve capacity so you stop hitting on-demand throttles.

## Cost tracking

- **AWS Cost Explorer** — analyze and forecast spend; identify the costliest models/workloads.
- **Shift async workloads to Batch** — move anything not real-time to the **Batch Inference API** for the discount.

## Provisioned Throughput vs On-Demand

| Attribute | Provisioned Throughput | On-Demand |
|---|---|---|
| Cost | Fixed, pay for reserved units (even idle) | Pay per token/request |
| Latency | Consistent, no cold start, no throttling | Good, but can throttle under load |
| Best for | Steady, high-volume, latency-critical | Bursty, variable, low/medium volume |
| Trap | Paying for idle capacity on spiky traffic | Throttling under sustained heavy load |

## Exam traps & key discriminators

- **Cost + repeated large static prompt** → **Prompt Caching** (not a smaller model, not batch).
- **Cost + mixed difficulty** → **Intelligent Prompt Routing** or **Model Cascading**.
- **Cost + offline/bulk** → **Batch Inference API** (confirm discount %).
- **"Chat feels slow to start"** → **streaming** (TTFT), not Provisioned Throughput.
- **"Which hop is slow?"** → **X-Ray tracing**, not CloudWatch metrics alone.
- **Throttling** → **exponential backoff with jitter** (the jitter is the point); Provisioned Throughput for guaranteed capacity.
- **Provisioned Throughput on spiky traffic** = paying for idle capacity (wrong).
- Streaming improves *perceived* latency, not *total* tokens or cost.

## Self-check (5–8 questions)

1. Every request sends the same 2,000-token system prompt. Cheapest lever to cut cost?
2. You need to know which component in an API Gateway → Lambda → Bedrock chain is slow. Which tool?
3. A nightly job summarizes 100k documents, latency does not matter. Which inference mode?
4. What exactly does `jitter` add to exponential backoff, and why does it matter?
5. When is Provisioned Throughput the wrong choice despite its low latency?
6. Does response streaming reduce total token cost? Why or why not?
7. Which lever routes each request to the cheapest capable model automatically?

Decision tables: [deployment](/tablas-decision/decision-despliegue) · [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
