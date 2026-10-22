---
id: dominio-1-fundacion-datos
sidebar_position: 2
title: Domain 1 — Foundation, Data & Compliance (31%)
---

This is the heaviest domain. Just under a third of your scored questions come from here, so this is the longest file in the course. It covers choosing a foundation model (FM = a large pre-trained model you call rather than train), customizing it, building the data/RAG pipeline that feeds it, and engineering prompts.

Back to [course home](/) · [exam strategy](/blueprint/vision-examen) · overlaps with [Domain 3 compliance](/blueprint/dominio-3-seguridad).

## FM selection from the Bedrock catalog

**Amazon Bedrock** is AWS's managed service that exposes many foundation models through one API. Choosing the right model family is a recurring exam task. You balance **capability vs context window vs latency vs cost**.

| Model family | Typical strengths | Context / latency / cost profile | Pick for |
|---|---|---|---|
| **Anthropic Claude** | Strong reasoning, long-context, instruction following | Large context window, higher cost, mid latency *(confirm exact window/pricing in docs)* | Complex reasoning, long documents, high-quality agents |
| **Meta Llama** | Open-weight, customizable, good general performance | Mid context, lower cost *(confirm in docs)* | Cost-sensitive general use, teams wanting open weights |
| **Amazon Titan** | AWS-native text + **Titan Embeddings** for RAG | Efficient, lower cost *(confirm in docs)* | Embeddings, lightweight text tasks, AWS-native stack |
| **Amazon Nova** | AWS's model family across tiers (e.g., Nova Micro/Lite/Pro, Nova Sonic for speech) | Nova Lite = cheap/fast for simple tasks; higher tiers for harder tasks *(confirm tiering in docs)* | Tiered cost/quality; Nova Lite for classification/routing, higher tiers for complex work |

**Discriminator:** match the task to the cheapest model that clears the quality bar. A simple classification does not need Claude Sonnet; use a small Nova/Llama tier and save cost (ties into [Intelligent Prompt Routing](/blueprint/dominio-4-optimizacion)).

> **Recap:** Bedrock = one API, many FMs. Pick by capability vs context vs latency vs cost. Do not over-provision model capability for a simple task.

## Customization

When prompting alone is not enough, you can adapt a model. Know the two approaches and when each applies.

| Approach | What it is | Data needed | Cost / effort | When to use |
|---|---|---|---|---|
| **Parameter-efficient fine-tuning (PEFT / LoRA/adapters)** | Train a small set of extra parameters, freeze the base weights | Moderate labeled data | Lower compute/cost | Teach style/format/domain tone efficiently; most common fine-tuning choice |
| **Full fine-tuning** | Update all model weights | Large, high-quality labeled dataset | High compute/cost | Deep domain adaptation when PEFT is insufficient and you have lots of data |

Supporting services:

- **Amazon SageMaker AI** — hosts custom/fine-tuned model weights that are not in the Bedrock catalog (serve via SageMaker endpoints; see [deployment table](/tablas-decision/decision-despliegue)).
- **SageMaker Model Registry** — versions and governs models so you can track which version is in production (ties to regression testing in [D5](/blueprint/dominio-5-testing)).
- **Cross-region inference** — routes requests across regions for capacity/availability; note region choice interacts with **data residency** ([D3](/blueprint/dominio-3-seguridad)).

**Exam discriminator:** prefer **RAG before fine-tuning** when the need is *fresh/proprietary facts* — RAG injects knowledge at query time with no training. Fine-tune (PEFT first) when you need *behavior/format/style* the base model will not follow via prompting.

> **Recap:** RAG for knowledge, fine-tuning for behavior. PEFT/LoRA before full fine-tuning unless you have lots of data and a deep-adaptation need.

## Well-Architected Generative AI Lens

The **AWS Well-Architected GenAI Lens** is AWS's set of best-practice guidance for GenAI workloads (reliability, cost, security, operational excellence applied to GenAI). On the exam, an answer that invokes Well-Architected GenAI best practices (e.g., responsible AI, cost controls, observability) is often the "best practice" choice. Treat it as the framework your correct answers should align with.

## Data pipelines

RAG quality starts with data quality. You ingest unstructured and multimodal data (text, PDFs, images), validate it, and format it for embedding.

- **AWS Glue Data Quality** — validates and flags data-quality issues in your ingestion pipeline before bad data poisons retrieval.
- **Input formatting** — clean, consistent text improves embedding quality; garbage in → irrelevant retrieval.
- Multimodal ingestion may pair text extraction with models/services that handle images or audio.

## Chunking strategies

**Chunking** splits documents into pieces small enough to embed and retrieve. The strategy has a direct ripple effect on retrieval quality (and therefore on [RAGAS Context Recall](/blueprint/dominio-5-testing)).

| Strategy | How it works | Pros | Cons | Context Recall impact |
|---|---|---|---|---|
| **Fixed-size** | Split every N tokens | Simple, predictable | Can cut sentences/ideas mid-thought | Poor chunk boundaries can lower recall |
| **Hierarchical** | Parent/child chunks (retrieve small, expand to parent) | Keeps local precision + broader context | More complex to configure | Better recall of surrounding context |
| **Semantic** | Split on meaning/topic boundaries | Chunks align with ideas → cleaner retrieval | Higher processing cost | Best signal-to-noise; improves recall & precision |

> **Ripple-effect callout:** bad chunking shows up downstream as **low Context Recall** (missing info) or **low Context Precision** (noisy chunks). If a scenario says "the model's answers are missing details that exist in the docs," the fix is usually **chunking/retrieval**, not the prompt.

## Embeddings

An **embedding** turns text into a vector so similar meanings sit close together. **Amazon Titan Embeddings** is the AWS-native embedding model commonly used to vectorize chunks for RAG. The embedding model you choose at ingestion must match the one used at query time.

## Vector store decision set

Where you store/search embeddings is a top-5 exam topic. Summary below; the full picker is the [vector store decision table](/tablas-decision/decision-vector-stores).

| Store | One-line when-to-pick |
|---|---|
| **Bedrock Knowledge Bases** | Least effort, managed turn-key RAG |
| **OpenSearch Serverless** | Hybrid (keyword + semantic) search at scale |
| **Aurora PostgreSQL + pgvector** | Reuse an existing relational database |
| **Amazon Kendra** | Enterprise document search with connectors |
| **S3 Vectors** | Ultra-large scale, cost-sensitive |

> **Recap:** memorize the five-store picker. The decisive keywords are *managed effort*, *hybrid*, *existing Postgres*, *enterprise connectors*, *huge scale+cost*.

## Retrieval quality

Getting relevant chunks is half the battle. Levers to improve retrieval:

- **Hybrid search** — combine lexical (BM25 keyword) and dense (vector) search for better relevance (OpenSearch Serverless).
- **Reranking** — re-score retrieved candidates with a reranker (e.g., **Cohere Rerank** available in Knowledge Bases) so the best chunks rank highest → improves **Context Precision**.
- **Query expansion / decomposition** — rewrite or break a complex query into sub-queries so retrieval covers all parts of the question.

## Prompt engineering & governance

- **Amazon Bedrock Prompt Management** — store, version, and share prompt templates centrally instead of hard-coding them.
- **Prompt Flows** — build visual, multi-step prompt workflows: **sequential chains**, **conditional branching**, and **dynamic routing** between prompts/models.
- **Parameterized templates** — inject variables into reusable prompts for consistency.
- **Chain-of-thought** — ask the model to reason step by step to improve accuracy on complex tasks.

> **Recap:** Prompt Management = versioned prompts; Prompt Flows = orchestrated prompt chains with branching/routing. These are the managed answers to "govern and chain prompts."

## Model decoupling

To swap the underlying model **without redeploying code**, put indirection in front of it: **Lambda** (serverless function) behind **API Gateway** (managed HTTP front door), with the model ID stored in **AWS AppConfig** (runtime configuration). You change the config value and traffic shifts to the new model — no deploy. This is the standard "switch models dynamically" answer.

## Exam traps & key discriminators

- **RAG vs fine-tuning:** RAG for fresh/proprietary **knowledge**; fine-tuning (PEFT first) for **behavior/format**. This is the single most tested D1 distinction.
- **"Missing info in answers"** → fix **chunking/retrieval** (Context Recall), not the prompt.
- **"Noisy / irrelevant chunks"** → **reranking** and **semantic chunking** (Context Precision).
- **Over-provisioned model** for a trivial task is a cost trap — pick the cheapest capable model.
- **Titan Embeddings** is for embeddings, not chat; don't confuse embedding models with text-generation models.
- **Switch models without redeploy** → Lambda + API Gateway + **AppConfig**, not a code change.
- **Full fine-tuning** needs lots of data and cost; defaulting to it over PEFT/LoRA is usually wrong.

## Self-check (5–8 questions)

1. A team needs the chatbot to answer from the company's latest internal PDFs. RAG or fine-tuning — and why?
2. Answers omit details that exist in the source docs. Which RAGAS metric is failing and which D1 lever fixes it?
3. You must store billions of vectors cheaply with no real-time latency requirement. Which store?
4. What is the difference between PEFT/LoRA and full fine-tuning, and which is the usual default?
5. How do you let ops switch the active model without a code deploy?
6. Which service provides managed, versioned prompt templates, and which builds branching prompt chains?
7. When would you pick OpenSearch Serverless over Bedrock Knowledge Bases?

Decision tables: [vector stores](/tablas-decision/decision-vector-stores) · [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
