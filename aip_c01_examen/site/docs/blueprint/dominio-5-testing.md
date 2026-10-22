---
id: dominio-5-testing
sidebar_position: 6
title: Domain 5 — Testing, Validation & Troubleshooting (11%)
---

Smallest domain, highly answerable once the **RAGAS** metric→symptom→fix mapping is memorized. Questions read "the app does X wrong — what do you do?"

Back to [course home](/) · grounding ties to [Domain 3](/blueprint/dominio-3-seguridad) · backoff shared with [Domain 4](/blueprint/dominio-4-optimizacion).

## RAGAS — metric, symptom, fix (the whole domain)

| Metric | Measures | Failure symptom | Fix lever |
|---|---|---|---|
| **Faithfulness** | Answer grounded in retrieved context | Invents facts (hallucination) | Guardrails **Contextual Grounding** ([D3](/blueprint/dominio-3-seguridad)) + better retrieval |
| **Context Precision** | Retrieved chunks relevant, ranked high | Lots of irrelevant chunks | **Reranking**, **semantic chunking** ([D1](/blueprint/dominio-1-fundacion-datos)) |
| **Context Recall** | Retrieval fetched **all** needed info | Answer missing details that exist in docs | Better **chunking/retrieval**, hybrid search ([D1](/blueprint/dominio-1-fundacion-datos)) |
| **Answer Relevance** | Answer addresses the prompt | Off-topic / partial | Prompt engineering, query decomposition |

Memory hook: *Faithfulness* = grounded; *Precision* = clean; *Recall* = complete; *Answer Relevance* = on-topic.

## Failure → fix (pick X)

- **Hallucination** → Faithfulness → Contextual Grounding + retrieval.
- **Missing info** → Context Recall → fix chunking/retrieval (not the prompt).
- **Noisy retrieval** → Context Precision → rerank + semantic chunking.
- **Off-topic** → Answer Relevance → prompt / query decomposition.

## Discriminators (pick X, not Y)

- **LLM-as-a-Judge, not humans** — for scaled, rubric-based, repeatable scoring / regression gates. **Humans, not LLM-judge** — for subjective or high-stakes nuance.
- **Regression testing against a benchmark set, not ad-hoc checks** — for "quality dropped after a model/prompt/retrieval change" (ties to SageMaker Model Registry, [D1](/blueprint/dominio-1-fundacion-datos)).
- **Schema enforcement + validation + retry, not a bigger model** — for "sometimes returns invalid JSON".

## Resilience patterns

| Pattern | Solves |
|---|---|
| **Exponential backoff with jitter** | Throttling / 429 (jitter avoids thundering herd) |
| **Fallback routing** | Model/region unavailable or throttled |
| **Dynamic masking + recovery** | Guardrail blocks → mask/retry or safe fallback, don't fail hard |

## Traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "states facts not in the KB" | Faithfulness + Contextual Grounding | bigger model |
| "misses info that's in the docs" | Context Recall → chunking/retrieval | rewrite prompt |
| "many irrelevant chunks" | Context Precision → rerank/semantic | more chunks |
| "quality dropped after upgrade" | regression test vs benchmark set | caching / temperature |
| "invalid JSON breaks the parser" | schema enforcement + validation + retry | bigger model |
| "Guardrail block fails the app" | masking + recovery / safe fallback | remove the Guardrail |

## Self-check

1. Bot states facts not in the KB — which metric, which fix?
2. Answers omit details in the sources — which metric, which domain's lever?
3. Why does backoff need jitter?
4. Parser keeps breaking on bad output — layered fix?
5. Prove a retrieval-parameter change didn't regress quality — how?
6. LLM-as-a-Judge vs human review — when each?
7. Context Precision vs Context Recall in one sentence each?

Confirm on AWS docs: current Bedrock evaluation / model-evaluation features.

Decision table: [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
