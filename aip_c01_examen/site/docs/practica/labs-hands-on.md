---
id: labs-hands-on
sidebar_position: 2
title: Optional Hands-On Labs
---

**Optional** and time-boxed. With ~40 hours total, the exam rewards reading scenarios, not building systems. Do the **Core** labs only if you have never touched Bedrock.

Back to [course home](/) · concepts in [Domain 2](/blueprint/dominio-2-implementacion) and [Domain 3](/blueprint/dominio-3-seguridad).

- **Cost/teardown:** use the cheapest model, tiny inputs, and tear everything down after.
- **No real PII or secrets** in any lab.

## The labs — objective + the discriminator it makes concrete

| Lab | Objective (do this) | The discriminator it proves | Priority | Minutes |
|---|---|---|---|---|
| **1 — Console + Converse + streaming** | Invoke a cheap model, then re-run with streaming | Streaming cuts time-to-first-token (perceived latency), not total compute ([D2](/blueprint/dominio-2-implementacion)) | Core | ~30 |
| **2 — Bedrock Knowledge Base (managed RAG)** | Index a few S3 files, query, then change chunking | Chunking drives Context Recall/Precision ([D5](/blueprint/dominio-5-testing)); KB = least-effort store ([D1](/blueprint/dominio-1-fundacion-datos)) | Core | ~45 |
| **3 — Attach a Guardrail** | Enable a content filter + PII filter; test ANONYMIZE then BLOCK | ANONYMIZE (usable answer) vs BLOCK (halt); Contextual Grounding rejects off-source ([D3](/blueprint/dominio-3-seguridad)) | Do if time | ~30 |
| **4 — Bedrock Agent + one Action Group** | Agent + a tiny Lambda tool; watch it decide to call it | Action Groups → Lambda is the core agent tool mechanism ([D2](/blueprint/dominio-2-implementacion)) | Do if time | ~45 |

## Reuse your existing AgentCore repo (Domain 2)

You already have a working, deployable agent in `intro_4h_agentcore`. Redeploy and inspect it instead of rebuilding — it covers most D2 hands-on:

- **Runtime** — [`agent/main.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/main.py)
- **Memory (short + long-term)** — [`agent/memoria.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/memoria.py)
- **Tools (Action-Group-style)** — [`agent/herramientas.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/herramientas.py)
- Start here: [`intro_4h_agentcore` README](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md)

Resources: [resources](/recursos). Back to [plan](/plan-estrategico).
