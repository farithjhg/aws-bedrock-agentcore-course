---
id: dominio-1-fundacion-datos
sidebar_position: 2
title: Domain 1 — Foundation, Data & Compliance (31%)
---

Heaviest domain. You know what FMs, RAG, embeddings, and chunking are — this is only the **pick-X-not-Y** decisions and the traps.

Back to [course home](/) · [exam strategy](/blueprint/vision-examen) · overlaps [Domain 3](/blueprint/dominio-3-seguridad).

## Discriminators (pick X, not Y — because …)

- **RAG, not fine-tuning** — when the need is *fresh/proprietary facts*; RAG injects knowledge at query time with no training. The single most tested D1 call.
- **Fine-tuning (PEFT/LoRA first), not RAG** — when the need is *behavior/format/tone* the base model won't follow via prompting.
- **PEFT/LoRA, not full fine-tuning** — unless you have a large labeled dataset and a deep-adaptation need; full is the default-wrong answer.
- **Cheapest model that clears the quality bar, not the strongest** — a classification task does not need a top-tier reasoning model. Ties to [Intelligent Prompt Routing](/blueprint/dominio-4-optimizacion).
- **Fix chunking/retrieval, not the prompt** — when answers *miss info that exists in the docs* (a Context Recall problem).
- **Reranking + semantic chunking, not a bigger model** — when retrieval is *noisy* (a Context Precision problem).

## Model-family contrast (one deciding axis + cue)

| Family | The ONE deciding axis | Exam cue |
|---|---|---|
| **Anthropic Claude** | Top reasoning / long context (higher cost) | "complex reasoning", "long documents", "high-quality agent" |
| **Meta Llama** | Open weights, cost-sensitive general use | "open-weight", "customizable", cost-sensitive general |
| **Amazon Titan** | AWS-native; **Titan Embeddings** for RAG | "embeddings", lightweight text, AWS-native stack |
| **Amazon Nova** | Tiered cost/quality (Micro/Lite/Pro; Sonic=speech) | "cheap/fast small tier for simple tasks", voice (Sonic) |

Embeddings trap: the embedding model at **ingestion must match** the one at query time — that match is the exam cue, not which embedding model.

## Vector store picker (one decisive keyword each)

| Store | Decisive keyword |
|---|---|
| **Bedrock Knowledge Bases** | least effort / managed turn-key RAG |
| **OpenSearch Serverless** | hybrid (keyword + semantic) at scale |
| **Aurora PostgreSQL + pgvector** | reuse an existing relational DB |
| **Amazon Kendra** | enterprise doc search with connectors |
| **S3 Vectors** | ultra-large scale, cost-sensitive (not speed) |

Full picker + traps: [vector store table](/tablas-decision/decision-vector-stores).

## One-liners worth memorizing

- **Chunking:** fixed (simple, cuts ideas) → hierarchical (keeps context, better recall) → semantic (cleanest signal, higher cost).
- **Retrieval levers:** hybrid search (OpenSearch) for relevance; **reranking** (e.g., Cohere Rerank) raises Precision; **query decomposition** covers multi-part questions.
- **Prompt Management = versioned templates; Prompt Flows = branching/routing prompt chains.** Don't swap them.
- **Switch model without redeploy → Lambda + API Gateway + AppConfig** (model ID in config, not code).
- **Glue Data Quality** validates records before they poison retrieval.
- **"Best practice" answers** usually align with the Well-Architected GenAI Lens.

## Traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "answer from latest internal PDFs, no retraining" | RAG | fine-tuning / higher temperature |
| "won't follow our tone/format even with good prompts" | PEFT/LoRA fine-tuning | RAG / full fine-tuning |
| "answers miss info that's in the docs" | fix chunking/retrieval (Context Recall) | rewrite the prompt |
| "retrieval is noisy/irrelevant" | reranking + semantic chunking (Precision) | bigger model |
| "switch active model without a deploy" | AppConfig indirection | hard-code + redeploy |
| trivial task | cheapest capable model | top-tier model (cost trap) |

## Self-check

1. Latest internal PDFs, no retraining: RAG or fine-tuning, and why?
2. Answers omit details present in sources: which RAGAS metric, which D1 lever?
3. Billions of vectors, cheap, no real-time latency: which store?
4. PEFT/LoRA vs full fine-tuning — which is the default and why?
5. Let ops switch the active model with no code deploy — how?
6. Prompt Management vs Prompt Flows?
7. When OpenSearch Serverless over Knowledge Bases?

Confirm on AWS docs: current model families/tiers, context windows, embedding model options, Knowledge Bases features.

Decision tables: [vector stores](/tablas-decision/decision-vector-stores) · [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
