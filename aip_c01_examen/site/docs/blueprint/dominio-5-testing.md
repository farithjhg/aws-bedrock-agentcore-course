---
id: dominio-5-testing
sidebar_position: 6
title: Domain 5 — Testing, Validation & Troubleshooting (11%)
---

The smallest domain, but very answerable once you know the **RAGAS** metrics and the common failure→fix mappings. Expect "the app does X wrong — what do you do?" questions.

Back to [course home](/) · grounding ties to [Domain 3](/blueprint/dominio-3-seguridad) · backoff shared with [Domain 4](/blueprint/dominio-4-optimizacion).

## RAGAS framework

**RAGAS** is a framework for evaluating RAG systems with four core metrics. Each targets a different failure mode. Know what each measures, what failure looks like, and the fix.

| Metric | What it measures | What failure looks like | The fix lever |
|---|---|---|---|
| **Faithfulness** | Is the answer grounded in the retrieved context (no fabrication)? | Model invents facts not in sources (hallucination) | Guardrails **Contextual Grounding** ([D3](/blueprint/dominio-3-seguridad)); better retrieval |
| **Context Precision** | Are the retrieved chunks relevant and ranked high (signal-to-noise)? | Lots of irrelevant chunks retrieved | **Reranking**, **semantic chunking** ([D1](/blueprint/dominio-1-fundacion-datos)) |
| **Context Recall** | Did retrieval fetch **all** the reference info needed to answer? | Answer missing details that exist in the docs | Better **chunking/retrieval**, hybrid search ([D1](/blueprint/dominio-1-fundacion-datos)) |
| **Answer Relevance** | Does the answer directly address the user's prompt? | Answer is off-topic or partial | Prompt engineering, query decomposition |

> **Memory hook:** *Faithfulness* = grounded in context; *Precision* = clean context; *Recall* = complete context; *Answer Relevance* = answers the question.

## Faithfulness

Faithfulness detects **hallucination** by checking that every claim in the answer traces back to retrieved context. Low faithfulness → add **Contextual Grounding** and improve retrieval. This is the direct bridge to Domain 3.

## Context Precision

Precision is the signal-to-noise ratio of retrieval: relevant chunks should rank high. Low precision means noisy retrieval — fix with **reranking** (e.g., Cohere Rerank in Knowledge Bases) and **semantic chunking**.

## Context Recall

Recall asks whether retrieval fetched *everything* needed. Low recall is the classic "answers are missing information that exists in the documents" symptom — fix the **chunking/retrieval** strategy, not the prompt.

## Answer Relevance

Measures how directly the answer addresses the prompt, independent of grounding. Fix with clearer prompts and **query decomposition** for multi-part questions.

## Judging quality

- **LLM-as-a-Judge** — use a powerful model to score a smaller model's outputs against a rubric at scale. Cheap, fast, repeatable; good for regression gates.
- **Human-in-the-loop** — humans review subjective quality (tone, nuance, safety-critical correctness) that automated metrics miss.

Use LLM-as-a-Judge for volume and consistency; add humans for subjective or high-stakes judgments.

## Regression testing

Keep a **benchmark/evaluation set** and re-run it whenever you change prompts, model versions, or retrieval parameters. This catches silent quality regressions (ties to **SageMaker Model Registry** versioning in [D1](/blueprint/dominio-1-fundacion-datos)). "We upgraded the model and quality dropped — how do you catch this?" → regression testing against a benchmark set.

## Structured output enforcement

When downstream systems need valid JSON:

- **Schema enforcement / structured output** — constrain the model to a schema.
- **System-prompt validation** — instruct and validate the format.
- **Structural parsing** — parse and verify the output shape.
- **Fallback formatting retries** — on malformed output, retry with a corrective prompt.

Symptom "the model sometimes returns invalid JSON that breaks the parser" → schema enforcement + validation + retry.

## Resilience patterns

| Pattern | Problem it solves | Detail |
|---|---|---|
| **Exponential backoff with jitter** | Bedrock throttling / `429` | Growing + randomized retry delays avoid the thundering-herd retry storm |
| **Fallback routing** | A model/region is unavailable or throttled | Fail over to a secondary model or region |
| **Dynamic content masking + recovery** | Guardrail blocks a response | Mask/anonymize and retry, or return a safe fallback, instead of failing hard |

## Exam traps & key discriminators

- **Hallucination** → **Faithfulness** metric + **Contextual Grounding** fix.
- **Missing info** → **Context Recall** → fix **chunking/retrieval** (not the prompt).
- **Noisy retrieval** → **Context Precision** → **reranking / semantic chunking**.
- **Off-topic answer** → **Answer Relevance** → prompt / query decomposition.
- **Throttling** → **exponential backoff with jitter** (jitter prevents synchronized retries).
- **Invalid JSON** → **schema enforcement + validation + retry**, not a bigger model.
- **Quality dropped after a change** → **regression testing** against a benchmark set.
- **LLM-as-a-Judge** scales evaluation; **human-in-the-loop** handles subjective/high-stakes cases.

## Self-check (5–8 questions)

1. The chatbot confidently states facts that are not in the knowledge base. Which RAGAS metric and which fix?
2. Answers omit details that the source documents contain. Which metric and which domain's lever fixes it?
3. Why does exponential backoff need jitter?
4. A parser keeps breaking on malformed model output. What is the layered fix?
5. You changed the retrieval parameters and want to prove quality did not regress. What do you do?
6. When do you use LLM-as-a-Judge vs human review?
7. Distinguish Context Precision from Context Recall in one sentence each.

Decision table: [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
