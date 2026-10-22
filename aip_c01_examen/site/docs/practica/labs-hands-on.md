---
id: labs-hands-on
sidebar_position: 2
title: Optional Hands-On Labs
---

These labs are **optional** and time-boxed. With only ~40 hours total, do not over-invest here — the exam rewards reading scenarios correctly, not building production systems. Do the **Core** labs if you have never touched Bedrock; treat the rest as *do if time permits*.

Back to [course home](/) · concepts in [Domain 2](/blueprint/dominio-2-implementacion) and [Domain 3](/blueprint/dominio-3-seguridad).

## Before you start

- **Cost caution:** Bedrock, Knowledge Bases, and endpoints can incur charges. Use the smallest/cheapest model, keep inputs tiny, and **tear everything down** when done.
- Confirm Bedrock model access is enabled in your account/region first (console → Bedrock → Model access).
- Never put real PII or secrets into a lab.

## Lab 1 — Explore the Bedrock console & Converse API (Core, ~30 min)

**Objective:** see how model invocation works and where the knobs live.

1. Open the Bedrock console; review the model catalog and enable access to one cheap text model.
2. Use the **Chat/Text playground** to send a prompt; adjust temperature and max tokens.
3. Call the model from the CLI/SDK with a simple `Converse` request.
4. Repeat with `InvokeModelWithResponseStream` (or Converse streaming) and watch tokens arrive incrementally.

**What to observe:** the difference between a single non-streaming call and streaming (time-to-first-token). This is the D2 streaming discriminator made concrete.

## Lab 2 — Build a Bedrock Knowledge Base (managed RAG) (Core, ~45 min)

**Objective:** experience turn-key managed RAG end to end.

1. Put a few small text/PDF files in an S3 bucket.
2. Create a **Bedrock Knowledge Base** pointing at the bucket; pick an embedding model (e.g., Titan Embeddings).
3. Let it chunk/embed; then run test queries in the console.
4. Change the chunking strategy and compare retrieved chunks.
5. (Optional) Enable reranking and compare precision.

**What to observe:** how chunking changes what gets retrieved — the direct link to **Context Recall/Precision** ([D5](/blueprint/dominio-5-testing)) and the vector-store choices ([D1](/blueprint/dominio-1-fundacion-datos)).

## Lab 3 — Attach a simple Guardrail (~30 min, do if time permits)

**Objective:** see the four safety layers in action.

1. Create a **Guardrail**; enable a Content Filter and a Denied Topic.
2. Add a **Sensitive Information Filter** for an email/phone pattern; set action to **ANONYMIZE**, then test; switch to **BLOCK** and test again.
3. (Optional) Enable **Contextual Grounding** against a source and try to make the model answer off-source.

**What to observe:** ANONYMIZE vs BLOCK behavior and how Contextual Grounding rejects ungrounded answers ([D3](/blueprint/dominio-3-seguridad)).

## Lab 4 — Create a basic Bedrock Agent with one Action Group (~45 min, do if time permits)

**Objective:** feel how an agent plans and calls a tool.

1. Create a **Bedrock Agent** with simple instructions.
2. Add one **Action Group** backed by a tiny Lambda (e.g., a fake "lookup order status").
3. Test in the console and watch the agent decide to call the tool (ReAct-style reason→act→observe).

**What to observe:** Action Groups → Lambda tool invocation, the core D2 agent mechanism.

## Reuse your existing AgentCore repo

You already have a working, deployable agent in `../../intro_4h_agentcore/` (Spanish, but the code/architecture is the point). Rather than rebuild from scratch, redeploy it and inspect:

- **AgentCore Runtime** — [`agent/main.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/main.py)
- **Memory (short + long-term)** — [`agent/memoria.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/memoria.py)
- **Tools / business rules (Action-Group-style)** — [`agent/herramientas.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/herramientas.py)
- **Identity / MCP Gateway** — `teoria/cap09-identidad.html`, `teoria/cap07-mcp-gateway.html`
- Infra (S3, least-privilege IAM, Memory, Runtime) under `infra/`.

Start from [`../../intro_4h_agentcore/README.md`](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md). This covers most Domain-2 hands-on concepts without new setup.

## Priority & time budget

| Lab | Concept | Priority | Minutes |
|---|---|---|---|
| Lab 1 | Bedrock console + Converse + streaming | Core | ~30 |
| Lab 2 | Managed RAG (Knowledge Base) + chunking | Core | ~45 |
| Lab 3 | Guardrails (4 layers, ANONYMIZE/BLOCK) | Do if time | ~30 |
| Lab 4 | Bedrock Agent + Action Group | Do if time | ~45 |
| Reuse | Redeploy `intro_4h_agentcore` | Do if time | varies |

Resources: [recursos.md](/recursos). Back to [plan](/plan-estrategico).
