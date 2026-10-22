---
id: banco-preguntas
sidebar_position: 1
title: Practice Question Bank
---

~50 original, scenario-style questions weighted toward the heavier domains (D1 ≈ 12, D2 ≈ 10, D3 ≈ 10, D4 ≈ 8, D5 ≈ 8). Several are multiple-response (labeled **Select TWO**) to rehearse the all-or-nothing rule.

**These questions are original.** They do not reproduce or imitate real AWS exam items. They exist to drill scenario-reading and the [master constraint table](/tablas-decision/decision-por-restriccion).

Back to [course home](/) · then run the [final mock](/practica/simulacro-final).

## How to use

1. Cover the answer key. Give yourself ~2.4 minutes per question.
2. **Before** choosing, name the decisive **constraint keyword** in the stem.
3. For **Select TWO**, judge each option independently (no partial credit).
4. Score yourself per domain; take weak domains back to the matching [blueprint](/blueprint/dominio-1-fundacion-datos) file.

---

## Domain 1 (≈12) — Foundation, Data & Compliance

**Q1.** A support bot must answer using the company's constantly updated internal PDFs without retraining. Best approach?
- A) Full fine-tuning nightly
- B) RAG with a Bedrock Knowledge Base
- C) Increase the model's temperature
- D) Prompt caching

**Q2.** Answers are missing details that clearly exist in the source documents. Which RAGAS metric is failing and what is the fix?
- A) Faithfulness → add Guardrails
- B) Answer Relevance → rewrite the system prompt
- C) Context Recall → improve chunking/retrieval
- D) Context Precision → raise temperature

**Q3.** You must store billions of embeddings as cheaply as possible; real-time latency is not required. Which store?
- A) Aurora pgvector
- B) Amazon Kendra
- C) Amazon S3 Vectors
- D) Provisioned Throughput

**Q4.** A team wants both keyword and semantic search with relevance tuning at large scale. Which store?
- A) Bedrock Knowledge Bases (default)
- B) Amazon OpenSearch Serverless
- C) DynamoDB
- D) S3 Vectors

**Q5.** The base model will not consistently produce the brand's required tone and output format, even with good prompts. The team has a modest labeled dataset. Best approach?
- A) RAG
- B) Parameter-efficient fine-tuning (LoRA/PEFT)
- C) Full fine-tuning from scratch
- D) Train a new foundation model

**Q6. (Select TWO)** Which actions most directly improve **Context Precision** (signal-to-noise of retrieved chunks)?
- A) Add a reranking step (e.g., Cohere Rerank)
- B) Increase max output tokens
- C) Use semantic chunking instead of fixed-size
- D) Switch to a larger generation model
- E) Disable Guardrails

**Q7.** Operations need to switch the active Bedrock model without redeploying application code. Best design?
- A) Hard-code the new model ID and redeploy
- B) Lambda + API Gateway with the model ID in AWS AppConfig
- C) Provisioned Throughput
- D) Store the model ID in the Lambda source file

**Q8.** Which service provides managed, versioned, reusable prompt templates?
- A) Amazon Bedrock Prompt Management
- B) AWS Glue Data Quality
- C) SageMaker Clarify
- D) Amazon Macie

**Q9.** A greenfield RAG app with no existing database wants the least operational overhead to get end-to-end retrieval working. Which store?
- A) Aurora pgvector
- B) Self-managed OpenSearch cluster
- C) Bedrock Knowledge Bases
- D) S3 Vectors

**Q10.** A pipeline ingests messy third-party CSVs and bad records keep poisoning retrieval. Which service validates data quality before indexing?
- A) AWS Glue Data Quality
- B) Amazon Comprehend
- C) Amazon Kendra
- D) CloudTrail

**Q11.** Which best describes when to use RAG vs fine-tuning?
- A) RAG for behavior/tone; fine-tuning for fresh facts
- B) RAG for fresh/proprietary knowledge; fine-tuning for behavior/format
- C) They are interchangeable
- D) Always fine-tune first

**Q12. (Select TWO)** Which are valid reasons to choose Amazon Titan Embeddings in a RAG pipeline?
- A) It converts text chunks into vectors for similarity search
- B) It generates the final chat response
- C) The embedding model at ingestion should match the one used at query time
- D) It enforces JSON schemas
- E) It blocks prompt-injection attacks

---

## Domain 2 (≈10) — Implementation & Integration

**Q13.** A chat UI "feels slow to start responding" even though total latency is acceptable. Best fix?
- A) Provisioned Throughput
- B) Response streaming (`InvokeModelWithResponseStream` / Converse streaming)
- C) Batch Inference API
- D) Larger model

**Q14.** You need a workflow with retries, a conditional fallback branch, and a human-approval step before a response is sent. Which service orchestrates this?
- A) Amazon EventBridge alone
- B) AWS Step Functions
- C) DynamoDB Streams
- D) API Gateway

**Q15.** Which AgentCore component provides per-session isolated execution (a microVM per session)?
- A) Gateway
- B) Memory
- C) Runtime
- D) Identity

**Q16.** A team must expose several existing internal REST APIs as tools an agent can call, using an open standard. Best choice?
- A) AgentCore Gateway exposing MCP tools
- B) Store the APIs in DynamoDB
- C) Call them via Cost Explorer
- D) Rewrite them as a foundation model

**Q17.** When should you host a model on a SageMaker endpoint instead of calling a Bedrock-catalog model On-Demand?
- A) When you want the least operational overhead
- B) When you host custom or open-source model weights not in the Bedrock catalog
- C) When traffic is bursty and low-volume
- D) Always, for lower cost

**Q18.** Which API is the unified, model-agnostic conversational interface recommended for portability across models?
- A) `InvokeModel`
- B) The Converse API
- C) `ApplyGuardrail`
- D) Cost Explorer API

**Q19. (Select TWO)** A design uses a multi-agent orchestration that noticeably increases token cost. Which two levers mitigate the cost while preserving quality on hard cases?
- A) Model cascading (cheap model first, escalate hard cases)
- B) Intelligent Prompt Routing
- C) Disable observability
- D) Always use the largest model
- E) Remove all tools

**Q20.** Where should a long-running, stateful MCP tool server run?
- A) AWS Lambda (scale-to-zero)
- B) Amazon ECS containers
- C) Amazon S3
- D) Amazon Macie

**Q21.** An agent must remember a user's preferences across different sessions over weeks. Best fit?
- A) Store nothing; re-ask each time
- B) AgentCore Memory (long-term)
- C) CloudWatch Logs
- D) X-Ray traces

**Q22.** A nightly job must enrich 500,000 records with model output; latency is irrelevant and cost matters. Which inference mode?
- A) Provisioned Throughput
- B) On-Demand real-time calls
- C) Bedrock Batch Inference API
- D) AWS Batch compute

**Q23.** For an event-driven, fire-and-forget fan-out of GenAI tasks, which service decouples producers from consumers?
- A) Amazon EventBridge
- B) Provisioned Throughput
- C) KMS
- D) Kendra

---

## Domain 3 (≈10) — AI Safety, Security & Governance

**Q24.** Bedrock traffic must never traverse the public internet. Best control?
- A) Put the endpoint behind a public URL with an IP allow-list
- B) Interface VPC Endpoints via AWS PrivateLink
- C) Transit Gateway
- D) Direct Connect

**Q25.** A response must hide customer phone numbers but still return a usable answer. Which Guardrail PII action?
- A) BLOCK
- B) ANONYMIZE
- C) Delete the Guardrail
- D) Raise temperature

**Q26.** Which Guardrail layer stops the model from asserting facts not present in the retrieved sources?
- A) Denied Topics
- B) Content Filters
- C) Contextual Grounding Checks
- D) Word Filters

**Q27.** You must apply the **same** safety policy to a self-hosted (non-Bedrock) model. What do you use?
- A) The standalone `ApplyGuardrail` API
- B) SageMaker Clarify
- C) Cost Explorer
- D) Model cards

**Q28. (Select TWO)** Which two produce a compliance/audit trail of Bedrock model usage?
- A) Model Invocation Logging to S3/CloudWatch
- B) AWS CloudTrail
- C) Increasing temperature
- D) Prompt caching
- E) Response streaming

**Q29.** Which service discovers and classifies PII sitting at rest in your S3 data stores?
- A) Amazon Macie
- B) Bedrock Guardrails
- C) AWS X-Ray
- D) EventBridge

**Q30.** Which service detects bias and drift for responsible-AI reporting?
- A) Amazon SageMaker Clarify
- B) Amazon Kendra
- C) AppConfig
- D) AgentCore Gateway

**Q31.** Users are attempting jailbreak/prompt-injection attacks. Which Guardrail capability targets this?
- A) Contextual Grounding
- B) Content Filters → Prompt Attacks
- C) Sensitive Information Filters
- D) Batch Inference

**Q32.** Which IAM condition restricts Bedrock access to calls coming through your VPC endpoint?
- A) `aws:SourceVpce`
- B) `aws:TemperatureEquals`
- C) `bedrock:MaxTokens`
- D) `s3:x-amz-acl`

**Q33.** A regulated workload must keep inference within the EU for data residency. Which lever most directly helps?
- A) Choosing an EU region / EU inference profile
- B) Increasing max tokens
- C) Prompt caching
- D) A Denied Topics filter

---

## Domain 4 (≈8) — Operational Efficiency & Optimization

**Q34.** Every request sends the same 3,000-token system prompt and few-shot examples. Cheapest lever?
- A) Switch to a larger model
- B) Prompt Caching
- C) Provisioned Throughput
- D) Increase temperature

**Q35.** You must find which hop (API Gateway → Lambda → vector search → Bedrock) is causing latency. Which tool?
- A) CloudWatch metrics only
- B) AWS X-Ray distributed tracing
- C) Cost Explorer
- D) Macie

**Q36.** Traffic is a mix of trivial and complex requests; you want to cut cost without hurting hard-case quality. Best lever?
- A) Intelligent Prompt Routing / model cascading
- B) Always use the top model
- C) Batch Inference for everything
- D) Disable Guardrails

**Q37.** Bedrock returns intermittent `ThrottlingException` under load. Best client-side mitigation?
- A) Retry immediately in a tight loop
- B) Exponential backoff with jitter
- C) Increase max output tokens
- D) Switch to Kendra

**Q38.** A steady, mission-critical, high-volume workload needs consistent low latency and no cold starts. Which mode?
- A) On-Demand
- B) Provisioned Throughput
- C) Serverless Inference scaled to zero
- D) Batch Inference

**Q39. (Select TWO)** Which two reduce **cost** on a non-real-time bulk workload?
- A) Bedrock Batch Inference API
- B) Model cascading
- C) Provisioned Throughput reserved for the bulk job
- D) Response streaming
- E) Larger context window

**Q40.** Does response streaming reduce total token cost?
- A) Yes, it halves tokens
- B) No — it improves perceived latency (TTFT), not total tokens
- C) Yes, by caching
- D) Only with Provisioned Throughput

**Q41.** A spiky, low-average-volume app chose Provisioned Throughput and the bill is high. What went wrong?
- A) Nothing; it is optimal
- B) They pay for reserved capacity that sits idle; On-Demand fits spiky traffic
- C) Streaming is disabled
- D) The model is too small

---

## Domain 5 (≈8) — Testing, Validation & Troubleshooting

**Q42.** The bot confidently states facts not in the knowledge base. Which RAGAS metric detects this, and which control prevents it?
- A) Context Precision → reranking
- B) Faithfulness → Contextual Grounding
- C) Answer Relevance → bigger model
- D) Context Recall → Provisioned Throughput

**Q43.** Which metric asks whether retrieval fetched **all** the reference info needed to answer?
- A) Faithfulness
- B) Context Precision
- C) Context Recall
- D) Answer Relevance

**Q44.** A downstream parser keeps breaking because the model sometimes returns invalid JSON. Best fix?
- A) Use a bigger model and hope
- B) Schema/structured-output enforcement + validation + retry fallback
- C) Increase temperature
- D) Disable the parser

**Q45.** After upgrading the model version, quality dropped silently. How should the team have caught this?
- A) Regression testing against a benchmark/evaluation set
- B) Prompt caching
- C) Raising temperature
- D) PrivateLink

**Q46. (Select TWO)** Which two are appropriate ways to evaluate RAG answer quality at scale and for subjective nuance?
- A) LLM-as-a-Judge for scaled, rubric-based scoring
- B) Human-in-the-loop review for subjective/high-stakes cases
- C) Counting tokens only
- D) Measuring CPU utilization
- E) Checking the S3 bucket size

**Q47.** Retrieval returns many irrelevant chunks (low signal-to-noise). Which metric and fix?
- A) Context Recall → more chunks
- B) Context Precision → reranking and semantic chunking
- C) Faithfulness → raise temperature
- D) Answer Relevance → Provisioned Throughput

**Q48.** Why does exponential backoff need **jitter**?
- A) To increase total retries
- B) To randomize delays so clients don't retry in sync (avoid thundering herd)
- C) To reduce token cost
- D) To encrypt traffic

**Q49.** A Guardrail blocks a response and the app fails hard. Better resilience pattern?
- A) Remove the Guardrail
- B) Dynamic content masking + recovery / safe fallback
- C) Retry immediately forever
- D) Switch to Batch Inference

---

## Answer key & explanations

| # | Answer | Why the right answer wins (and why top distractors lose) |
|---|---|---|
| Q1 | **B** | RAG injects fresh knowledge at query time with no retraining. Fine-tuning (A) is slow/costly and not for volatile facts; temperature (C) and prompt caching (D) don't add knowledge. |
| Q2 | **C** | Missing-but-present info is a **Context Recall** failure → fix retrieval/chunking. Faithfulness (A) is about fabrication; relevance/temperature don't fetch missing context. |
| Q3 | **C** | S3 Vectors targets ultra-large scale at low cost with no real-time requirement. pgvector/Kendra don't fit scale+cost; Provisioned Throughput is an inference mode, not a store. |
| Q4 | **B** | OpenSearch Serverless offers hybrid (BM25 + k-NN) at scale. Knowledge Bases defaults to less control; DynamoDB/S3 Vectors aren't hybrid search. |
| Q5 | **B** | Behavior/format needs fine-tuning; with modest data, PEFT/LoRA is the efficient default. RAG (A) teaches knowledge not behavior; full/from-scratch (C/D) need far more data/cost. |
| Q6 | **A, C** | Reranking and semantic chunking raise signal-to-noise (precision). More output tokens, a bigger model, or disabling Guardrails don't improve retrieval precision. |
| Q7 | **B** | AppConfig externalizes the model ID so you switch at runtime without a deploy. Hard-coding/redeploy (A/D) and Provisioned Throughput (C) don't decouple the model choice. |
| Q8 | **A** | Prompt Management stores versioned templates. Glue DQ validates data; Clarify is bias/drift; Macie is PII at rest. |
| Q9 | **C** | Knowledge Bases is the lowest-overhead managed RAG for greenfield. pgvector/self-managed OpenSearch add ops; S3 Vectors is for huge scale, not quickest setup. |
| Q10 | **A** | Glue Data Quality validates records pre-index. Comprehend is NLP/PII entities; Kendra is search; CloudTrail is API audit. |
| Q11 | **B** | RAG = fresh/proprietary knowledge; fine-tuning = behavior/format. The rest invert or oversimplify. |
| Q12 | **A, C** | Titan Embeddings vectorizes chunks, and the ingestion/query embedding models must match. It does not generate chat, enforce JSON, or block attacks. |
| Q13 | **B** | Streaming cuts time-to-first-token → feels fast. Provisioned Throughput/larger model don't change perceived start; Batch is non-real-time. |
| Q14 | **B** | Step Functions orchestrates retries, branches, and human-approval steps. EventBridge alone is async events; DynamoDB Streams/API Gateway don't orchestrate. |
| Q15 | **C** | Runtime provides session-isolated microVM execution. Gateway=tools, Memory=context, Identity=auth. |
| Q16 | **A** | AgentCore Gateway exposes existing APIs as MCP tools (open standard). The others are unrelated. |
| Q17 | **B** | SageMaker endpoints host custom/open-source weights not in Bedrock. Least overhead and bursty low-volume favor managed On-Demand; "always for cost" is false. |
| Q18 | **B** | Converse API is the unified, model-agnostic conversational interface. `InvokeModel` is single-call; `ApplyGuardrail` is safety; Cost Explorer is billing. |
| Q19 | **A, B** | Cascading and Intelligent Prompt Routing cut cost while keeping quality on hard cases. Disabling observability, always-largest, and removing tools don't (or hurt quality). |
| Q20 | **B** | Long-running stateful servers fit ECS containers. Lambda is for bursty/short; S3/Macie aren't compute for tools. |
| Q21 | **B** | AgentCore Memory (long-term) persists preferences across sessions. Logs/traces aren't memory; re-asking is poor UX. |
| Q22 | **C** | Bedrock Batch Inference API = async bulk, cost-efficient. Provisioned/On-Demand are real-time; **AWS Batch** is out-of-scope generic compute (the trap). |
| Q23 | **A** | EventBridge decouples producers/consumers for async fan-out. The rest are unrelated to eventing. |
| Q24 | **B** | PrivateLink interface VPC endpoints keep traffic private. Public URL+IP list still uses the internet; Transit Gateway/Direct Connect are out-of-scope networking. |
| Q25 | **B** | ANONYMIZE masks PII but returns a usable answer. BLOCK halts; the others are nonsense. |
| Q26 | **C** | Contextual Grounding validates output against sources to stop hallucination. The other layers target topics/content/words. |
| Q27 | **A** | `ApplyGuardrail` applies the policy to any model, including non-Bedrock. Clarify is bias/drift; the rest don't apply policy. |
| Q28 | **A, B** | Model Invocation Logging + CloudTrail form the audit trail. Temperature, caching, streaming are not audit controls. |
| Q29 | **A** | Macie discovers PII at rest in S3. Guardrails act in-flight; X-Ray/EventBridge are unrelated. |
| Q30 | **A** | SageMaker Clarify measures bias/drift. The others are search/config/agent tooling. |
| Q31 | **B** | Content Filters → Prompt Attacks target jailbreak/injection. Grounding/PII/Batch don't. |
| Q32 | **A** | `aws:SourceVpce` restricts access to the VPC endpoint. The others aren't valid Bedrock IAM conditions for this. |
| Q33 | **A** | Region/EU inference profile enforces data residency. Tokens/caching/denied-topics don't control residency. |
| Q34 | **B** | Prompt Caching stops re-billing the large static prefix. Bigger model/Provisioned/temperature don't cut repeated-prefix cost. |
| Q35 | **B** | X-Ray distributed tracing isolates the slow hop. CloudWatch metrics alone show symptoms, not the hop; others are unrelated. |
| Q36 | **A** | Routing/cascading send easy work to cheap models, hard work to strong ones. Always-top/Batch-everything/disabling Guardrails are wrong. |
| Q37 | **B** | Exponential backoff with jitter avoids retry storms. Tight-loop retries worsen throttling; tokens/Kendra are irrelevant. |
| Q38 | **B** | Provisioned Throughput gives consistent low latency and no cold starts for steady high volume. On-Demand throttles; Serverless cold-starts; Batch is offline. |
| Q39 | **A, B** | Batch Inference (async discount) and cascading cut bulk cost. Reserving Provisioned for a bulk job, streaming, and bigger context don't reduce cost. |
| Q40 | **B** | Streaming improves perceived latency (TTFT), not total tokens/cost. The other claims are false. |
| Q41 | **B** | Provisioned Throughput bills for idle reserved capacity on spiky traffic; On-Demand fits. The rest misdiagnose. |
| Q42 | **B** | Faithfulness detects ungrounded claims; Contextual Grounding prevents them. The other pairings don't address hallucination. |
| Q43 | **C** | Context Recall = did retrieval fetch all needed info. Precision=relevance/noise; Faithfulness=grounding; Answer Relevance=on-topic. |
| Q44 | **B** | Schema enforcement + validation + retry reliably yields valid JSON. Bigger model/temperature/disabling parser don't guarantee structure. |
| Q45 | **A** | Regression testing against a benchmark set catches version-change regressions. Caching/temperature/PrivateLink don't test quality. |
| Q46 | **A, B** | LLM-as-a-Judge scales rubric scoring; humans handle subjective/high-stakes nuance. Token/CPU/bucket-size metrics don't measure answer quality. |
| Q47 | **B** | Low signal-to-noise = Context Precision; fix with reranking + semantic chunking. The others misidentify metric or fix. |
| Q48 | **B** | Jitter randomizes retry timing so clients don't retry in lockstep (thundering herd). It doesn't add retries, cut cost, or encrypt. |
| Q49 | **B** | Dynamic masking + recovery / safe fallback degrades gracefully. Removing Guardrails is unsafe; infinite retries and Batch don't fix the block. |

Next: take the [final mock & readiness gate](/practica/simulacro-final). Review weak domains in the [blueprints](/blueprint/vision-examen) and the [master constraint table](/tablas-decision/decision-por-restriccion).
