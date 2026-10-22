---
id: dominio-2-implementacion
sidebar_position: 3
title: Domain 2 — Implementation & Integration (26%)
---

Second-heaviest. You know what agents, tools, and streaming are — this is which AWS building block wins per cue, and what not to swap.

Back to [course home](/) · cost ripple into [Domain 4](/blueprint/dominio-4-optimizacion).

## AgentCore components (the discriminator)

| Component | Exam cue |
|---|---|
| **Runtime** | "run an agent with per-session isolation / microVM sandbox" |
| **Gateway** | "expose existing APIs as agent tools", "MCP server" |
| **Memory** | "remember context across turns / across sessions" |
| **Observability** | "debug / monitor the agent's steps" |
| **Identity** | "secure who/what the agent can call" (auth, JWT) |

## Discriminators (pick X, not Y)

- **Bedrock Agents** = managed agent + Action Groups; **AgentCore** = production platform (5 components above); **Strands** = the code SDK. Match the component to the cue.
- **AgentCore Memory, not DynamoDB** — when the requirement is *agent conversation/preference memory*. DynamoDB is for general app state.
- **Lambda, not ECS** — for bursty/short MCP tools (scale-to-zero). **ECS, not Lambda** — for long-running/stateful tool servers.
- **Step Functions, not EventBridge** — for multi-step workflows with retries, branches, and human-approval. **EventBridge, not Step Functions** — for async fire-and-forget decoupling/fan-out. Don't swap them.
- **Converse API, not `InvokeModel`** — when the stem wants unified, model-agnostic portability + tool use across models.
- **Streaming, not a bigger model / Provisioned** — when "chat feels slow to start": streaming cuts time-to-first-token (perceived latency), not total compute.

## Tool integration & APIs (one-liners)

- **Action Groups → Lambda** = standard Bedrock Agent tool call; **MCP** tools served via **AgentCore Gateway** (open standard).
- `InvokeModel` = single non-streaming call; `InvokeModelWithResponseStream` = token-by-token; **Converse** = unified multi-turn + tool use.
- Streaming delivery to client: WebSockets or SSE via **API Gateway**.
- Voice: **Transcribe** (streaming STT) feeds text; **Nova Sonic** = speech-capable model.

## Deployment modes (one decisive keyword each)

| Mode | When to pick |
|---|---|
| **On-Demand** | bursty/variable, no commitment |
| **Provisioned Throughput** | steady, mission-critical, low-latency, no cold starts |
| **SageMaker endpoints** | host custom/open-source weights; scale-to-zero |
| **Batch Inference API** | async bulk, cost over latency *(confirm discount % in docs)* |
| **Model Cascading** | cheap small model first, escalate hard cases |

Full picker: [deployment table](/tablas-decision/decision-despliegue).

## Cost ripple (ties to D4)

Multi-agent and ReAct loops improve reasoning but **multiply token cost** — every step is more tokens. Expect the correct answer to pair them with a D4 mitigation: **model cascading** or **Intelligent Prompt Routing** ([Domain 4](/blueprint/dominio-4-optimizacion)).

## Traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "chat feels slow to start" | response streaming (TTFT) | Provisioned / bigger model |
| "retries + fallback + human approval" | Step Functions | EventBridge alone |
| "async fan-out, fire-and-forget" | EventBridge | Step Functions |
| "expose existing APIs as agent tools" | AgentCore Gateway (MCP) | rewrite as a model |
| "host our fine-tuned/open-source weights" | SageMaker endpoint | Bedrock On-Demand |
| "nightly bulk enrichment, cost matters" | Batch Inference API | AWS Batch (out of scope) |
| "portability across models" | Converse API | `InvokeModel` |

Reuse what you built: the companion repo `intro_4h_agentcore` already demonstrates Runtime ([`agent/main.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/main.py)), Memory ([`agent/memoria.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/memoria.py)), and tools ([`agent/herramientas.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/herramientas.py)) — redeploy it instead of rebuilding (see [labs](/practica/labs-hands-on)).

## Self-check

1. Which AgentCore component gives per-session microVM isolation, and which exposes APIs as tools?
2. "Chat feels slow to start" — best implementation change, and why?
3. Workflow with retries, fallback, and a human-approval gate: which service?
4. When SageMaker endpoint instead of Bedrock On-Demand?
5. `InvokeModel` vs Converse API?
6. Where do long-running stateful MCP tools run?
7. Why does multi-agent raise cost, and which two D4 levers mitigate it?

Confirm on AWS docs: current AgentCore components, Converse API tool-use, agent options.

Decision tables: [deployment](/tablas-decision/decision-despliegue) · [by constraint](/tablas-decision/decision-por-restriccion). Labs: [hands-on](/practica/labs-hands-on). Practice: [question bank](/practica/banco-preguntas).
