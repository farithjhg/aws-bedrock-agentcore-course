---
id: dominio-5-testing
sidebar_position: 6
title: Domain 5 — Testing, Validation & Troubleshooting (11%)
---

The Northwind Support Assistant is now knowledgeable ([Domain 1](/blueprint/dominio-1-fundacion-datos)), capable of acting ([Domain 2](/blueprint/dominio-2-implementacion)), safe ([Domain 3](/blueprint/dominio-3-seguridad)), and efficient ([Domain 4](/blueprint/dominio-4-optimizacion)). One question remains, and it is the one that lets Northwind actually ship: does the assistant really work, and will it keep working after the next change? In this domain we PROVE it. We measure retrieval and grounding with RAGAS metrics, score answer quality with an LLM-as-judge and with human review, lock in quality with regression tests against a benchmark set, force the model to return machine-readable structured output, and wrap the whole thing in fault-tolerant patterns. By the end, Northwind can prove the assistant works and catch it the moment it regresses.

Back to [course home](/) · grounding ties to [Domain 3](/blueprint/dominio-3-seguridad) · backoff shared with [Domain 4](/blueprint/dominio-4-optimizacion).

This is the smallest domain by weight, but it is highly answerable once you truly understand the four RAGAS metrics. Most questions read like a bug report: "the assistant does X wrong — what do you do?" The whole skill is mapping the symptom to the metric that measures it, then to the lever that fixes it.

## The mental model for the whole domain

A RAG answer passes through two stages, and a test can only be useful if it knows which stage broke. Stage one is **retrieval**: the assistant searches `northwind-support-kb` and pulls back some chunks of Northwind's documents. Stage two is **generation**: the model reads those chunks and writes an answer. A bad final answer can come from a bad retrieval (we fetched the wrong or incomplete documents) or from a bad generation (we had the right documents and the model still wrote something wrong). RAGAS gives you one metric per failure mode so you can tell retrieval bugs from generation bugs instead of guessing. Keep that split in mind for every metric below.

### RAGAS metrics (the core D5 decision)

#### Concept

RAGAS is an evaluation framework for RAG systems. Its value is that it scores the parts of a RAG answer **separately**, so a low score points at a specific cause. There are four metrics you must know, and the cleanest way to hold them is to attach each to one of three inputs: the user question, the retrieved context, and the generated answer.

- **Faithfulness** asks: is every claim in the answer actually supported by the retrieved context? It compares the **answer** against the **context**. Low faithfulness means the model made up facts that the documents never stated — hallucination.
- **Context Precision** asks: of the chunks we retrieved, how many are actually relevant, and are the relevant ones ranked near the top? It judges the **context** against the **question**. Low precision means the retrieval is noisy — it dragged in junk.
- **Context Recall** asks: did retrieval pull back *all* the information needed to answer? It judges the **context** against the **question** (and the known correct answer). Low recall means retrieval missed documents that exist and are relevant — the answer is incomplete through no fault of the model.
- **Answer Relevance** asks: does the answer actually address what the user asked? It compares the **answer** against the **question**. Low relevance means the answer is off-topic, padded, or only half an answer.

The memory hook: *Faithfulness* = grounded, *Precision* = clean, *Recall* = complete, *Answer Relevance* = on-topic. Precision and recall are the classic pair — precision punishes retrieving junk, recall punishes missing the good stuff — so they trade off exactly the way they do in any search system.

#### Example

A customer asks the Northwind assistant: "Can I return a blender I opened three weeks ago during the holidays?" Here is how each metric catches a different failure of that one question.

- The assistant answers "Yes, you have 90 days," but Northwind's return policy says 30 days. The 90 came from nowhere in the retrieved chunks. That is a **Faithfulness** failure — the generation invented a fact.
- The retrieval pulled back ten chunks, but eight were about shipping and warranty, and the actual holiday-return clause was ranked ninth. The model got distracted and answered vaguely. That is a **Context Precision** failure — noisy, badly ranked retrieval.
- Northwind has a separate "Holiday Returns Addendum" document that extends the window, but retrieval never fetched it, so the assistant answered using only the standard policy and gave an answer that is technically grounded but wrong for the holiday case. That is a **Context Recall** failure — the needed document existed and was missed.
- The assistant replies with three paragraphs about Northwind's sustainability program and never says whether the blender can be returned. That is an **Answer Relevance** failure — on none of the facts, just off-topic.

One question, four distinct ways to fail, four distinct fixes. That separation is the entire reason RAGAS exists.

#### Implementation

RAGAS itself is an open-source Python library; on AWS you can also run managed RAG evaluation through Amazon Bedrock model/RAG evaluation jobs. The exam cares that you can describe an evaluation harness: a benchmark set of questions with known-good answers, a run that produces answers plus the context that was retrieved, and a scoring pass that produces per-metric numbers you can gate on.

Here is a compact harness sketch. It uses `bedrock-agent-runtime` `retrieve_and_generate` to get both the answer and the retrieved context for each benchmark question, then hands them to a scorer.

```python
import boto3

# bedrock-agent-runtime gives us retrieval + generation in one call,
# and crucially returns the retrieved chunks (the "context") so we can
# score retrieval and generation SEPARATELY.
agent_rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

KB_ID = "NORTHWINDKB01"          # northwind-support-kb
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/MODEL_ID"  # confirm exact model id in current AWS docs

# A benchmark set is the heart of any eval: fixed questions + known-good
# answers ("ground truth"). Curated once, reused on every change.
benchmark = [
    {
        "question": "Can I return an opened blender bought during the holidays?",
        "ground_truth": "Holiday purchases follow the 30-day Holiday Returns Addendum...",
    },
    # ... dozens more, covering returns, shipping, warranty, account issues
]

def run_one(question: str) -> dict:
    resp = agent_rt.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": MODEL_ARN,
            },
        },
    )  # confirm exact params in boto3 docs
    answer = resp["output"]["text"]
    # citations carry the retrieved chunks = the "context" RAGAS scores against
    contexts = [
        ref["content"]["text"]
        for cit in resp.get("citations", [])
        for ref in cit.get("retrievedReferences", [])
    ]
    return {"answer": answer, "contexts": contexts}

# Collect answers + contexts for the whole benchmark set.
samples = []
for row in benchmark:
    out = run_one(row["question"])
    samples.append({
        "question": row["question"],
        "answer": out["answer"],
        "contexts": out["contexts"],
        "ground_truth": row["ground_truth"],
    })

# Score with the open-source RAGAS library. Each metric reads the fields
# it needs: faithfulness(answer,contexts), context_precision/recall(question,
# contexts,ground_truth), answer_relevancy(question,answer).
from ragas import evaluate
from ragas.metrics import (
    faithfulness, answer_relevancy,
    context_precision, context_recall,
)
from datasets import Dataset

dataset = Dataset.from_list(samples)
scores = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)  # confirm exact RAGAS API in current library docs
print(scores)  # e.g. per-metric averages across the benchmark set
```

The architecture is a loop, not a one-shot: a fixed benchmark set feeds a run, the run produces answers and contexts, a scorer turns those into per-metric numbers, and a gate decides pass or fail.

```text
            ┌─────────────────────┐
            │  Benchmark set      │  questions + ground-truth answers
            │  (curated, fixed)   │
            └──────────┬──────────┘
                       v
         ┌──────────────────────────┐
         │ Run: retrieve_and_generate│  -> answer + retrieved context
         │  over northwind-support-kb│
         └──────────┬────────────────┘
                    v
         ┌──────────────────────────┐
         │ Score (RAGAS / LLM-judge) │  faithfulness, precision,
         │  per metric               │  recall, relevance
         └──────────┬────────────────┘
                    v
         ┌──────────────────────────┐
         │ Gate: all metrics >= bar? │  pass -> ship
         │  else -> block the change │  fail -> block + show which metric
         └───────────────────────────┘
```

#### When & Why

Use RAGAS metrics whenever you need to **diagnose** a RAG quality problem or **quantify** quality before and after a change. The metric you reach for is decided purely by the symptom:

- **Hallucination** (states facts not in the knowledge base): low **Faithfulness**. Fix the generation side — add Guardrails Contextual Grounding ([D3](/blueprint/dominio-3-seguridad)) and improve retrieval so the true fact is actually present. The trap answer here is "use a bigger model"; a bigger model still hallucinates if the grounding is not enforced.
- **Missing information** that genuinely exists in the docs: low **Context Recall**. Fix retrieval — better chunking, hybrid search, broader top-k ([D1](/blueprint/dominio-1-fundacion-datos)). The trap is "rewrite the prompt"; the prompt cannot fix documents that were never retrieved.
- **Noisy retrieval**, many irrelevant chunks: low **Context Precision**. Fix ranking — add reranking (e.g. Cohere Rerank) and semantic chunking ([D1](/blueprint/dominio-1-fundacion-datos)). The trap is "retrieve more chunks," which usually adds more noise.
- **Off-topic or partial answers**: low **Answer Relevance**. Fix the prompt or decompose the query into sub-questions.

Do NOT use RAGAS as a production guardrail — it is an offline/CI measurement tool, not a real-time blocker. The real-time prevention of hallucination is Contextual Grounding in [D3](/blueprint/dominio-3-seguridad). The clean division to memorize: **Contextual Grounding prevents, RAGAS Faithfulness measures.** Precision versus Recall is the other classic confusion — precision is about the junk you let in, recall is about the good stuff you left out.

### LLM-as-a-Judge vs human review

#### Concept

RAGAS gives you numbers for retrieval and grounding, but a lot of answer quality is subjective: was the tone right, was the explanation clear, did it follow Northwind's style, did it refuse appropriately? You cannot write a simple assertion for "is this a good answer." The two ways to score subjective quality are to ask a human or to ask another language model.

**LLM-as-a-Judge** means you call a strong model with a rubric — a written scoring guide — and the question, the answer, and (optionally) the reference answer, and you ask it to grade. The mental model is a grading teaching assistant with an answer key: it is fast, cheap, available around the clock, and — this is the key property — **repeatable**. Give it the same rubric and inputs and it scores the same way, which is exactly what you need to compare two versions of the assistant fairly. Humans drift, get tired, and disagree with each other; a judge model applies the same rubric to sample one and sample ten-thousand.

**Human review** is what you use when the stakes or the subtlety are too high to trust to a model: legally sensitive answers, safety edge cases, brand-defining tone calls, or building the ground-truth set that the judge is later measured against. Humans are the gold standard for nuance; they just do not scale.

#### Example

Northwind wants to score 2,000 past support conversations for "did the assistant correctly refuse to share another customer's order details." Writing a regex for that is hopeless — refusals are phrased a hundred ways. Sending all 2,000 to the support team would take days and the reviewers would score inconsistently by the end. So Northwind writes a one-paragraph rubric ("score 1 if the answer declines to reveal third-party personal data and offers the correct self-service path, else 0") and runs an LLM judge over all 2,000 in minutes, getting one consistent number. For the 30 borderline cases the judge marks low-confidence, a human reviewer makes the final call. That split — judge for scale, human for the hard tail — is the pattern the exam rewards.

#### Implementation

An LLM-as-judge call is an ordinary `converse` call whose prompt is a rubric and whose job is to return a score. Forcing the judge to answer in a tiny fixed JSON shape makes the result parseable and keeps the judge disciplined.

```python
import boto3
import json

rt = boto3.client("bedrock-runtime", region_name="us-east-1")
JUDGE_MODEL = "MODEL_ID"  # a strong model as judge; confirm exact model id in current AWS docs

# The rubric IS the test. Keep it explicit so scoring is repeatable:
# same rubric + same inputs -> same score, run after run.
RUBRIC = """You are grading a customer-support answer.
Score 1-5 on each axis and return ONLY JSON:
- faithful: is every claim supported by the provided context?
- relevant: does it answer the actual question?
- tone: is it polite and on-brand for a retailer?
Return: {"faithful": n, "relevant": n, "tone": n, "reason": "..."}"""

def judge(question: str, answer: str, context: str) -> dict:
    resp = rt.converse(
        modelId=JUDGE_MODEL,
        system=[{"text": RUBRIC}],
        messages=[{
            "role": "user",
            "content": [{"text":
                f"QUESTION:\n{question}\n\nCONTEXT:\n{context}\n\nANSWER:\n{answer}"
            }],
        }],
        inferenceConfig={"temperature": 0, "maxTokens": 300},
        # temperature 0 keeps the judge deterministic => repeatable scores
    )  # confirm exact params in boto3 docs
    text = resp["output"]["message"]["content"][0]["text"]
    return json.loads(text)  # judge was told to return JSON only

score = judge(
    question="Can I return an opened blender from the holidays?",
    answer="Holiday purchases can be returned within 30 days...",
    context="Holiday Returns Addendum: 30-day window for holiday purchases...",
)
print(score)  # e.g. {"faithful": 5, "relevant": 5, "tone": 4, "reason": "..."}
```

#### When & Why

Use **LLM-as-a-Judge** when you need scaled, rubric-based, repeatable scoring — regression gates in CI, scoring thousands of samples, comparing two prompt versions. Its superpower is consistency across volume. Use **human review** when the judgment is subjective and high-stakes, when you are establishing the ground-truth benchmark the judge will be checked against, or when a wrong score has real consequences (legal, safety, brand). The near-neighbor trap: do not reach for humans just because the task "feels qualitative" — if it is a repeatable rubric at scale, the judge wins on speed, cost, and consistency. And do not trust the judge blindly on the small, high-stakes tail — route low-confidence or sensitive cases to a human. A judge model can carry its own biases, so for anything that must be defensible, humans set the standard.

### Regression testing against a benchmark set

#### Concept

A regression test answers one question: did a change make things worse? Every lever you touched in prior domains — swapping the foundation model, editing the system prompt, re-chunking the corpus, changing top-k, turning on caching — can silently degrade answer quality while everything still "runs." The mental model is the test suite a software team runs before every release, except the pass/fail is a quality score instead of a green checkmark. You freeze a representative **benchmark set** (a fixed collection of questions with known-good answers), you score the assistant against it today to get a baseline, and from then on you re-score on every change and compare to the baseline. If the new score drops below the bar, the change is a regression and you block it.

The benchmark set is the whole trick. Ad-hoc "I tried a few questions and it seemed fine" proves nothing, because you cannot compare it to anything and you will test different questions each time. A fixed set makes the comparison apples-to-apples.

#### Example

Northwind's team wants to turn on prompt caching ([D4](/blueprint/dominio-4-optimizacion)) to cut cost, and also bump to a newer model version. Both changes "work" — the assistant still answers. But before shipping, they run the 200-question Northwind benchmark through the eval harness. Faithfulness and Answer Relevance hold steady, but Context Recall drops noticeably: the newer model's different handling of the retrieved context is dropping a detail on multi-part return questions. Without the benchmark they would have shipped a quiet quality regression and found out from customer complaints. With it, the gate fails, points at Context Recall, and they fix retrieval before release. This ties directly to the **SageMaker Model Registry**, where model versions and their evaluation results are tracked so you always know which version passed which bar.

#### Implementation

A regression test is the eval harness from the RAGAS section wrapped in a pass/fail gate with a stored baseline. The skeleton below is deliberately CI-shaped — it exits non-zero when quality regresses so a pipeline can block the deploy.

```python
import json
import sys

# Reuse run_one() + RAGAS scoring from the eval-harness section above.
# Here we focus on the GATE: compare today's scores to a stored baseline.

BASELINE = {               # produced by a known-good run, version-controlled
    "faithfulness": 0.90,
    "answer_relevancy": 0.88,
    "context_precision": 0.85,
    "context_recall": 0.87,
}
TOLERANCE = 0.03           # allow small noise; bigger drop = regression

def gate(current: dict, baseline: dict, tol: float) -> bool:
    regressions = {
        metric: (baseline[metric], current[metric])
        for metric in baseline
        if current[metric] < baseline[metric] - tol
    }
    if regressions:
        for metric, (was, now) in regressions.items():
            print(f"REGRESSION {metric}: {was:.2f} -> {now:.2f}")
        return False
    print("PASS: no metric regressed beyond tolerance")
    return True

if __name__ == "__main__":
    # current_scores = evaluate(...) from the harness; loaded here for brevity
    current_scores = json.load(open("latest_scores.json"))
    ok = gate(current_scores, BASELINE, TOLERANCE)
    sys.exit(0 if ok else 1)  # non-zero fails the CI job and blocks the change
```

```text
  code / prompt / model / chunking change
                 │
                 v
   run benchmark set through eval harness
                 │
                 v
        new per-metric scores
                 │
         compare to stored BASELINE
          ┌──────┴───────┐
      within tol      dropped > tol
          │                │
        PASS            FAIL -> block deploy,
      ship change       name the metric that fell
```

#### When & Why

Use regression testing whenever quality "dropped after a change" or before promoting any new model, prompt, or retrieval configuration to production — it is the only way to prove a change is safe. The exam cue is almost always "quality got worse after we upgraded/changed X." The trap answers are the other things that *sound* related — tuning temperature, adding caching, tweaking the prompt — none of which **prove** anything; they are guesses. Regression testing against a fixed benchmark set is the move because it is the only option that gives you a before-and-after comparison. Pair it with the SageMaker Model Registry to track which version cleared the bar. When NOT to lean on it: it will not tell you *why* a metric fell — for that you drop back to the RAGAS per-metric diagnosis above. Regression testing is the alarm; RAGAS metrics are the diagnosis.

### Structured-output enforcement

#### Concept

The moment the assistant stops being a chat box and starts feeding other systems — calling a returns API, writing a ticket, triggering a workflow in [D2](/blueprint/dominio-2-implementacion) — its output has to be machine-readable, usually JSON with a fixed shape. Language models are probabilistic text generators, so "please reply in JSON" works most of the time and then occasionally emits a stray sentence, a trailing comma, or a missing field, and the downstream parser throws. The naive fix is "use a bigger model," but a bigger model still occasionally drifts; probabilistic output cannot be made perfectly reliable by scaling.

The real mental model is three layers. First, **constrain** the output at generation time — use the model's tool-use / function-calling mechanism (in Bedrock, the Converse API `toolConfig` with an input JSON schema), which pushes the model to emit arguments that fit your schema. Second, **validate** what came back against that schema. Third, **retry** on failure, feeding the validation error back so the model can correct itself. Constrain to reduce failures, validate to catch the ones that slip through, retry to recover — that layered defense is the pattern, not any single trick.

#### Example

Northwind's "process a return" flow needs the assistant to turn a free-text customer message into a structured command: `{ order_id, item_sku, reason_code, refund_method }`. If the model returns prose or omits `reason_code`, the returns Lambda crashes. So Northwind defines the return command as a tool with a strict JSON schema, lets the Converse API drive the model to fill that schema, validates the result, and on the rare malformed output, retries once with the validation error attached. The parser stops breaking not because the model got smarter but because the shape is enforced and checked.

#### Implementation

Two pieces: the Converse `toolConfig` that constrains generation to a schema, and a validate-and-retry wrapper that catches the ones that still slip through.

```python
import boto3
import json
from jsonschema import validate, ValidationError

rt = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "MODEL_ID"  # confirm exact model id in current AWS docs

# The schema is the contract. Converse tool-use nudges the model to emit
# arguments that FIT this schema instead of free-form prose.
RETURN_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string"},
        "item_sku": {"type": "string"},
        "reason_code": {"type": "string",
                        "enum": ["DAMAGED", "WRONG_ITEM", "CHANGED_MIND"]},
        "refund_method": {"type": "string",
                          "enum": ["ORIGINAL", "STORE_CREDIT"]},
    },
    "required": ["order_id", "item_sku", "reason_code", "refund_method"],
}

tool_config = {
    "tools": [{
        "toolSpec": {
            "name": "create_return",
            "description": "Create a structured return command.",
            "inputSchema": {"json": RETURN_SCHEMA},
        }
    }],
    # forcing the tool makes the model answer THROUGH the schema
    "toolChoice": {"tool": {"name": "create_return"}},
}  # confirm exact params in boto3 docs

def extract_return(message: str, max_retries: int = 2) -> dict:
    messages = [{"role": "user", "content": [{"text": message}]}]
    for attempt in range(max_retries + 1):
        resp = rt.converse(
            modelId=MODEL_ID,
            messages=messages,
            toolConfig=tool_config,
            inferenceConfig={"temperature": 0},
        )
        # pull the tool-use block the model produced
        blocks = resp["output"]["message"]["content"]
        tool_use = next(b["toolUse"] for b in blocks if "toolUse" in b)
        candidate = tool_use["input"]
        try:
            validate(instance=candidate, schema=RETURN_SCHEMA)  # layer 2: validate
            return candidate                                    # success
        except ValidationError as e:
            # layer 3: feed the error back and let the model fix itself
            messages.append({"role": "assistant", "content": blocks})
            messages.append({"role": "user", "content": [{"text":
                f"That did not match the schema: {e.message}. Try again."}]})
    raise ValueError("model could not produce schema-valid output")  # fail safe
```

```text
   customer free text
          │
          v
   converse(toolConfig = JSON schema)   <-- layer 1: constrain
          │
          v
   candidate JSON ──> validate(schema)  <-- layer 2: validate
          │                 │
        valid            invalid
          │                 │
        return      append error, retry  <-- layer 3: retry
                            │
                     still invalid -> raise (fail safe, don't pass junk on)
```

#### When & Why

Use structured-output enforcement any time the model's output is consumed by code rather than read by a human — tool calls, agents, pipelines, anything with a parser downstream. The exam cue is "sometimes returns invalid JSON and breaks the parser." The correct answer is the layered combination of **schema enforcement + validation + retry**, and the trap is almost always "use a bigger/better model" — scaling reduces the failure rate but never removes it, and it costs more for a problem that is really about contract enforcement. When NOT to bother: if the output is free-form prose a human reads, forcing a rigid schema just makes the assistant stilted. Near-neighbor nuance: tool-use/function-calling is the preferred constraint mechanism in Bedrock because it is built into the Converse API, but you still keep the validate-and-retry layers around it — constraint lowers the odds of a bad shape, validation is what guarantees you never pass one downstream.

### Fault-tolerant patterns

#### Concept

Proving the assistant works in a test is not the same as keeping it working under real traffic. Three things routinely break a live Bedrock application, and each has a standard pattern. First, **throttling**: under load, Bedrock returns `ThrottlingException` / HTTP 429, and the fix is **exponential backoff with jitter** — wait a growing interval between retries, plus a random offset so that a thousand clients that all got throttled at the same instant do not all retry at the same instant and re-create the storm. The jitter is the entire point; without it, synchronized retries just hammer the service again. Second, a **model or region being unavailable**: the fix is **fallback routing** — try a secondary model or region instead of failing the request. Third, a **Guardrail blocking** a response ([D3](/blueprint/dominio-3-seguridad)): the fix is **dynamic masking plus recovery** — mask the offending span or fall back to a safe canned response rather than crashing the whole interaction. The theme across all three: degrade gracefully, never fail hard.

#### Example

On a Black Friday spike, Northwind's assistant suddenly gets 429s from Bedrock. Without backoff, every chat session retries instantly and in lockstep, making the throttling worse. With exponential backoff plus jitter, retries spread out and most succeed on the second or third attempt. When one region briefly cannot serve the model, fallback routing sends those requests to a secondary region so customers never see an error. And when a Guardrail blocks an answer that happened to contain a customer's own masked card number, the assistant returns a safe "I can't show that here, please check your account page" instead of a stack trace. The assistant stays up and polite through all three — that is what fault tolerance buys.

#### Implementation

Backoff-with-jitter is the one you must be able to write. This is the same retry wrapper shared with [Domain 4](/blueprint/dominio-4-optimizacion), with a fallback model as the last resort.

```python
import boto3
import random
import time
from botocore.exceptions import ClientError

rt = boto3.client("bedrock-runtime", region_name="us-east-1")
PRIMARY = "PRIMARY_MODEL_ID"      # confirm exact model id in current AWS docs
FALLBACK = "FALLBACK_MODEL_ID"    # secondary model/region for fallback routing

def invoke_resilient(messages, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return rt.converse(modelId=PRIMARY, messages=messages)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("ThrottlingException", "TooManyRequestsException"):
                # exponential backoff: 1s, 2s, 4s... PLUS jitter so that
                # many throttled clients do NOT retry in lockstep.
                base = 2 ** attempt
                sleep = base + random.uniform(0, base)  # full jitter
                time.sleep(sleep)
                continue
            raise  # non-throttle error: don't silently swallow it
    # primary exhausted its retries -> fallback routing to a secondary model
    return rt.converse(modelId=FALLBACK, messages=messages)
```

```text
   request ──> PRIMARY model
                  │
            ThrottlingException / 429
                  │
        exponential backoff + JITTER, retry
                  │
            still failing after N tries
                  │
                  v
        FALLBACK routing (secondary model/region)
                  │
   Guardrail block on output ──> mask span / safe canned reply
                                  (recover, never fail hard)
```

#### When & Why

Use **exponential backoff with jitter** for any throttling / 429 — it is the default answer and jitter is the discriminator; a tight-loop or fixed-interval retry is the trap because it re-creates the thundering herd. Use **fallback routing** when the primary model or region can be unavailable and the request must still succeed. Use **dynamic masking plus recovery** when a Guardrail block would otherwise fail the whole app — the trap answer is "remove the Guardrail," which trades a graceful degrade for a safety hole. When NOT to add these: if a call is genuinely non-retryable (a validation error, a permission denial), retrying just wastes time and hides the real bug — backoff is only for transient capacity errors. The near-neighbor split to hold: backoff handles *transient* failures (capacity), fallback handles *availability* failures (the endpoint is down), masking handles *policy* blocks (a Guardrail fired).

## Exam traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "states facts not in the KB" | Faithfulness (measure) + Contextual Grounding (prevent) | bigger model |
| "misses info that is in the docs" | Context Recall → fix chunking/retrieval | rewrite the prompt |
| "many irrelevant chunks retrieved" | Context Precision → rerank + semantic chunking | retrieve more chunks |
| "answer is off-topic / partial" | Answer Relevance → prompt / query decomposition | bigger model |
| "score thousands of answers consistently" | LLM-as-a-Judge (rubric, repeatable) | human review (does not scale) |
| "subjective, high-stakes, build ground truth" | human review | LLM judge alone |
| "quality dropped after an upgrade/change" | regression test vs benchmark set (Model Registry) | caching / temperature tweak |
| "sometimes returns invalid JSON" | schema + validation + retry (tool-use) | bigger model |
| "ThrottlingException / 429" | exponential backoff **with jitter** | tight-loop / fixed retry |
| "model or region unavailable" | fallback routing (secondary model/region) | just fail the request |
| "Guardrail block fails the app" | dynamic masking + recovery / safe fallback | remove the Guardrail |

## Self-check

1. A customer gets facts that are nowhere in the knowledge base — which RAGAS metric is low, and what is the prevent-versus-measure split that fixes it?
2. The answer omits a detail that genuinely exists in Northwind's docs — which metric, and which domain's lever do you pull?
3. Explain Context Precision versus Context Recall in one sentence each.
4. When do you pick an LLM-as-a-Judge over human review, and when do you do the reverse?
5. You changed the model and the prompt and quality feels worse — what exactly do you run to prove it, and why do temperature or caching tweaks not count?
6. The parser keeps breaking on bad model output — name the three-layer fix and say why a bigger model is the wrong answer.
7. What does jitter add to exponential backoff, and what failure does it prevent?
8. A Guardrail block is crashing the whole interaction — what is the graceful fix, and why is removing the Guardrail the trap?

Confirm on AWS docs: current Amazon Bedrock model-evaluation and RAG-evaluation features, and the exact Converse `toolConfig` and `retrieve_and_generate` parameter shapes.

Decision table: [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas).
