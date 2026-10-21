# Master Decision Table — Constraint Keyword → Preferred Pattern

This is the single most exam-valuable asset in the course. Nearly every AIP-C01 scenario hides **one governing constraint**. If you can name that constraint, this table tells you the preferred AWS service or pattern — and lets you eliminate the distractors.

Back to [course home](../README.md). See also [vector store table](./decision-vector-stores.md) and [deployment table](./decision-despliegue.md).

## How to use

1. Read the question stem, then the scenario.
2. Scan for the **governing constraint keyword** (cost, latency, overhead, privacy, hallucination, scale, compliance). Underline it mentally.
3. Look the keyword up below and pick the matching pattern.
4. Eliminate options that fight the constraint — even if they are valid services.

## The master table

| Constraint keyword(s) in stem | Preferred service / pattern | Why it wins | Domain |
|---|---|---|---|
| "lowest cost", "reduce spend", "cost-effective" | **Prompt Caching** (cache static system prompt / long context / few-shot prefix); **Batch Inference API** (async bulk, discounted — *confirm % in docs*); **Model Cascading** (cheap small model first, escalate only hard cases); **Intelligent Prompt Routing** (route each request to the cheapest capable model); **ElastiCache** semantic/deterministic cache for repeated queries | All reduce tokens billed or route work to cheaper models; pay-per-token means fewer/cheaper tokens = lower cost | [D4](../blueprint/dominio-4-optimizacion.md) |
| "lowest latency", "fastest response", "fastest first token", "no cold start" | **Response streaming** (`InvokeModelWithResponseStream` / Converse streaming) for perceived latency; **Provisioned Throughput** for consistent low latency and no cold starts; **WebSocket API** (API Gateway) for bidirectional streaming | Streaming cuts time-to-first-token; Provisioned Throughput reserves capacity so there is no throttling/cold start | [D4](../blueprint/dominio-4-optimizacion.md) / [D2](../blueprint/dominio-2-implementacion.md) |
| "least operational overhead", "minimal effort", "fully managed", "fastest to build" | **Bedrock Knowledge Bases** (turn-key managed RAG); **Bedrock Agents** (managed agent orchestration); managed inference (On-Demand) | Managed services remove ops/plumbing; the exam rewards the lowest-effort option that still meets the requirement | [D1](../blueprint/dominio-1-fundacion-datos.md) / [D2](../blueprint/dominio-2-implementacion.md) |
| "must stay private", "no public internet", "data residency", "strict security" | **Interface VPC Endpoints via AWS PrivateLink** + **IAM least-privilege** with conditions like `aws:SourceVpce`; add **Guardrails** and region/inference-profile controls for residency | PrivateLink keeps Bedrock traffic off the public internet; IAM conditions restrict access to the VPC; region choice enforces residency | [D3](../blueprint/dominio-3-seguridad.md) |
| "detect hallucination", "answer not grounded", "make up facts" | **Contextual Grounding check** (Bedrock Guardrails) to block ungrounded output; **RAGAS Faithfulness** to measure it in testing | Grounding validates output against retrieved source chunks; Faithfulness quantifies grounding | [D3](../blueprint/dominio-3-seguridad.md) / [D5](../blueprint/dominio-5-testing.md) |
| "missing information in answers", "retrieval incomplete" | Improve **chunking** (hierarchical/semantic) and retrieval; measure with **RAGAS Context Recall** | Low recall means retrieval did not fetch all needed context; fix retrieval, not the prompt | [D1](../blueprint/dominio-1-fundacion-datos.md) / [D5](../blueprint/dominio-5-testing.md) |
| "mask / redact PII", "do not expose personal data" | **Sensitive Information Filters** in Guardrails (native patterns or custom **Amazon Comprehend**), **ANONYMIZE** to mask or **BLOCK** to halt; **Amazon Macie** to find PII in stores; **KMS** for encryption | Guardrails PII filters mask or block in-flight; Macie discovers PII at rest; KMS encrypts | [D3](../blueprint/dominio-3-seguridad.md) |
| "ultra-large scale", "billions of vectors", "scale + cost" | **S3 Vectors** (ultra-large, cost-sensitive); **OpenSearch Serverless** (hybrid search at scale) | These scale to very large corpora economically | [D1](../blueprint/dominio-1-fundacion-datos.md) |
| "hybrid search", "keyword + semantic" | **OpenSearch Serverless** (BM25 sparse + k-NN dense) | Only option combining lexical and vector search natively | [D1](../blueprint/dominio-1-fundacion-datos.md) |
| "use existing relational database" | **Aurora PostgreSQL + pgvector** | Reuses the relational store teams already operate | [D1](../blueprint/dominio-1-fundacion-datos.md) |
| "enterprise document search", "connectors to SharePoint/etc." | **Amazon Kendra** | Managed enterprise semantic search with built-in connectors | [D1](../blueprint/dominio-1-fundacion-datos.md) |
| "compliance", "audit trail", "who invoked what", "lineage" | **Model Invocation Logging** (to S3/CloudWatch) + **CloudTrail** + **AWS Audit Manager** + **model cards** | Together they produce the invocation records, API audit trail, and governance evidence auditors expect | [D3](../blueprint/dominio-3-seguridad.md) |
| "bias", "drift", "responsible/ethical AI" | **SageMaker Clarify** + human-in-the-loop | Clarify measures bias/drift and supports responsible-AI reporting | [D3](../blueprint/dominio-3-seguridad.md) |
| "agent uses tools / calls APIs" | **Bedrock Action Groups → Lambda**, or **MCP** tools via **AgentCore Gateway** | Action Groups/MCP are the standard tool-invocation mechanisms for agents | [D2](../blueprint/dominio-2-implementacion.md) |
| "multi-step workflow", "retry / fallback / human review" | **AWS Step Functions** (orchestration) + **EventBridge** (async events) | Step Functions handles distributed retries, branches, and human-approval steps | [D2](../blueprint/dominio-2-implementacion.md) |
| "throttling", "ThrottlingException", "429" | **Exponential backoff with jitter**; fallback model/region; **Provisioned Throughput** for guaranteed capacity | Backoff+jitter avoids thundering herd; Provisioned Throughput removes the throttle | [D4](../blueprint/dominio-4-optimizacion.md) / [D5](../blueprint/dominio-5-testing.md) |
| "valid JSON", "structured output", "schema" | Schema/structured-output enforcement + validation + retry fallback | Enforces machine-parseable output and recovers from malformed responses | [D5](../blueprint/dominio-5-testing.md) |
| "switch models without redeploying" | **Lambda + API Gateway + AppConfig** indirection | AppConfig externalizes the model ID so you change it without a deploy | [D1](../blueprint/dominio-1-fundacion-datos.md) / [D2](../blueprint/dominio-2-implementacion.md) |

## Multi-constraint tie-breakers

Some stems stack two constraints. Rough precedence when they conflict:

| If the stem combines… | …the usual winner | Reasoning |
|---|---|---|
| Security/privacy **and** cost | Security first | A cheaper option that leaks data or breaks residency is never the "best" answer on a Pro exam. |
| Minimal effort **and** cost | Read carefully | "Least operational overhead" → managed service; "lowest cost" → caching/batch/cascade. If both appear, the *primary* verb of the question wins. |
| Latency **and** cost | The named primary metric | If it says "real-time chat," latency wins (streaming/Provisioned). If it says "nightly bulk job," cost wins (Batch). |
| Scale **and** hybrid search | OpenSearch Serverless | Satisfies both at once. |
| Compliance **and** anything | Compliance usually gates | Audit/residency requirements are typically non-negotiable constraints. |

**Rule of thumb:** when two constraints appear, the one tied to a hard requirement ("must," "regulatory," "cannot leave the region") outranks a soft preference ("ideally cheaper").

See the focused tables: [vector stores](./decision-vector-stores.md) · [deployment modes](./decision-despliegue.md). Practice applying this table in the [question bank](../practica/banco-preguntas.md).
