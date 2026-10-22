---
id: dominio-2-implementacion
sidebar_position: 3
title: Domain 2 — Implementation & Integration (26%)
---

The second-heaviest domain. It covers building **agentic** applications (models that plan and call tools), choosing deployment/inference options, streaming responses, event-driven orchestration, multimodal voice, and wiring GenAI into enterprise systems.

Back to [course home](/) · cost ripple into [Domain 4](/blueprint/dominio-4-optimizacion).

## Agentic AI

An **agent** is an LLM that can reason about a goal, decide to call tools, observe results, and iterate. Key AWS building blocks:

- **Amazon Bedrock Agents** — managed agents that plan and invoke **Action Groups** (tools backed by Lambda).
- **Amazon Bedrock AgentCore** — a platform for building/running production agents. Core components below.
- **Strands Agents** — an AWS open-source SDK for building agents in code (used in the companion `intro_4h_agentcore` repo).
- **AWS Agent Squad** (multi-agent framework) — orchestrate multiple specialized agents.
- **ReAct** — a reasoning pattern where the agent alternates *reason → act (tool call) → observe*.

### AgentCore components

| Component | What it does | Exam cue |
|---|---|---|
| **Runtime** | Serverless, session-isolated execution (a microVM per session) for agents | "run an agent securely with session isolation / per-session sandbox" |
| **Gateway** | Turns APIs/Lambdas into agent-callable tools; MCP endpoint | "expose existing APIs as agent tools", "MCP server" |
| **Memory** | Short-term (session) and long-term (persisted user preferences) memory | "remember context across turns / across sessions" |
| **Observability** | Traces, metrics, and logs for agent behavior | "debug / monitor the agent's steps" |
| **Identity** | Auth for agents (e.g., JWT authorizer, access to downstream resources) | "secure who/what the agent can call" |

> **Recap:** Bedrock Agents = managed agent + Action Groups. AgentCore = production platform (Runtime, Gateway, Memory, Observability, Identity). Strands = the code SDK.

## Tool integration

- **Model Context Protocol (MCP)** — an open standard for exposing tools/data to models; AgentCore **Gateway** can serve MCP tools.
- **Bedrock Action Groups → Lambda** — the standard way a Bedrock Agent calls business logic.
- **MCP servers on Lambda vs ECS** — run lightweight/bursty tools on **Lambda** (serverless, scale-to-zero); run long-running or heavier tool servers on **ECS** (containers) when you need persistent processes or more control.

## State & session

| Need | Choice |
|---|---|
| General application state, key-value, high scale | **Amazon DynamoDB** (managed NoSQL) |
| Agent conversational memory (short + long term) | **AgentCore Memory** |

Use DynamoDB for app data; use AgentCore Memory when the requirement is specifically **agent conversation/preference memory**.

## Deployment & inference decision set

Summary here; full picker in the [deployment decision table](/tablas-decision/decision-despliegue).

| Mode | One-line when-to-pick |
|---|---|
| **On-Demand** | Bursty/variable traffic, no commitment |
| **Provisioned Throughput** | Steady, mission-critical, low-latency, no cold starts |
| **SageMaker endpoints (incl. Serverless Inference)** | Host custom/open-source weights; scale-to-zero |
| **Batch Inference API** | Async bulk, cost over latency *(confirm discount % in docs)* |
| **Model Cascading** | Cheap small model first, escalate hard cases |

## Response streaming

Streaming sends tokens as they are generated, cutting **time-to-first-token (TTFT)** and improving *perceived* latency even if total time is similar.

| Mode | Use case | Latency perception |
|---|---|---|
| **Non-streaming** (`InvokeModel` / `Converse`) | Short responses, batch calls, when you need the whole answer before acting | User waits for the full answer |
| **Streaming** (`InvokeModelWithResponseStream` / Converse streaming) | Chat UIs, long answers | User sees text immediately → feels fast |

Delivery to the client: **WebSockets** or **Server-Sent Events (SSE)** via **API Gateway**.

## Event-driven orchestration

- **Amazon EventBridge** — event bus for **asynchronous** decoupling (fire-and-forget, fan-out).
- **AWS Step Functions** — orchestrates distributed workflows with **retry**, **fallback**, branching, and **human-review/approval** steps. The go-to answer for "multi-step workflow with retries and a human approval gate."

## Multimodal voice

For voice assistants: **Amazon Transcribe** (streaming speech-to-text) feeds text to a model; **Amazon Nova Sonic** is AWS's speech-capable model for conversational voice. Pair them for real-time voice interactions.

## Enterprise integration

- **Amazon API Gateway** — managed front door for your GenAI APIs (auth, throttling, routing).
- **CI/CD** — **AWS CodePipeline** / **CodeBuild** to build, test, and deploy GenAI apps.
- **GenAI gateway architectures** — a central proxy/gateway that enforces quotas, routing, logging, and model access across teams.
- **Amazon Q Developer** — AWS's AI coding assistant for developer productivity.

## SDK & APIs

| API | Use |
|---|---|
| `InvokeModel` | Single, non-streaming model call |
| `InvokeModelWithResponseStream` | Streaming model call (token-by-token) |
| **Converse API** | Unified, model-agnostic conversational API (handles multi-turn + tool use consistently across models) |

> **Ripple-effect callout:** multi-agent and ReAct loops improve reasoning but **multiply token cost** (every step is more tokens). Mitigate with **model cascading** and **Intelligent Prompt Routing** — see [Domain 4](/blueprint/dominio-4-optimizacion).

> **Reuse note:** the companion repo `../../intro_4h_agentcore/` already demonstrates D2 concepts hands-on — **AgentCore Runtime** (`agent/main.py`), **Memory** short/long-term (`agent/memoria.py`), **tools/Action-Group-style logic** (`agent/herramientas.py`), and **Identity / MCP Gateway** (`teoria/cap09-identidad.html`, `cap07-mcp-gateway.html`). Reuse it rather than rebuilding — see [labs](/practica/labs-hands-on).

## Exam traps & key discriminators

- **Bedrock Agents vs AgentCore:** Agents = managed agent with Action Groups; AgentCore = production platform (Runtime/Gateway/Memory/Observability/Identity). Match the component to the cue.
- **Streaming is about perceived latency / TTFT**, not total compute saved. "Chat feels slow to start" → streaming.
- **Step Functions for retries/human-review**, EventBridge for async decoupling — don't swap them.
- **DynamoDB vs AgentCore Memory:** app state vs agent conversation memory.
- **Lambda vs ECS for MCP tools:** bursty/short → Lambda; long-running/heavy → ECS.
- **AWS Batch (out of scope) ≠ Bedrock Batch Inference API.**
- **Converse API** is the unified, model-agnostic choice when the stem wants portability across models.
- Multi-agent reasoning gains come at a **token-cost** price — expect a D4 mitigation in the correct answer.

## Self-check (5–8 questions)

1. Which AgentCore component gives each session an isolated microVM, and which exposes existing APIs as agent tools?
2. A chat UI "feels slow to respond." What implementation change helps most, and why?
3. You need a workflow with retries, a fallback branch, and a human-approval step. Which service?
4. When do you host a model on a SageMaker endpoint instead of calling Bedrock On-Demand?
5. What is the difference between `InvokeModel` and the Converse API?
6. Where should MCP tool servers run if they are long-running and stateful?
7. Why does a multi-agent design raise cost, and what two D4 levers mitigate it?

Decision tables: [deployment](/tablas-decision/decision-despliegue) · [by constraint](/tablas-decision/decision-por-restriccion). Labs: [hands-on](/practica/labs-hands-on). Practice: [question bank](/practica/banco-preguntas).
