---
id: dominio-4-optimizacion
sidebar_position: 5
title: Domain 4 — Make It Cheap & Fast (Optimization, 12%)
---

After [Domain 3](/blueprint/dominio-3-seguridad) the Northwind Support Assistant is safe and compliant — Guardrails screen every request, the network is private, PII is handled, and auditors can trace who did what. But safety was not free: the grounding pass added latency, the whole thing is billed per token, and Northwind's traffic is climbing fast as the assistant rolls out across stores. In this domain we make it **CHEAP and FAST**: prompt caching for the repeated system prompt, intelligent routing and cascading so easy questions use cheap models, batch inference for offline bulk jobs, the observability triad so we can actually *see* cost and latency, and resilience against throttling. By the end, the safe assistant runs at a cost and speed Northwind can live with. Proving it actually works is [Domain 5](/blueprint/dominio-5-testing).

Back to [course home](/) · deployment choices live in [Domain 2](/blueprint/dominio-2-implementacion) · the backoff pattern is shared with [Domain 5](/blueprint/dominio-5-testing).

The one mental model to carry through this whole domain: **Bedrock bills you by input tokens plus output tokens.** Every cost lever does exactly one of three things — it sends *fewer* tokens, it stops *re-billing* tokens you already paid for, or it sends tokens to a *cheaper model*. Every latency lever either cuts the time until the first token appears, or reserves capacity so you never wait in a queue. Keep that frame and every lever below slots into place.

---

## Prompt Caching

#### Concept

A large language model has no memory between calls. Each time you call it, you resend the entire prompt — system instructions, few-shot examples, retrieved context, the user's question — and you pay for every one of those input tokens, every single call. If the first 3,000 tokens of your prompt are *identical* on every request (because your system prompt and formatting rules never change), you are paying full price to re-process the same text thousands of times a day.

Prompt caching fixes this. You mark the stable prefix of your prompt as cacheable. The first call processes it normally and stores the model's internal representation of that prefix. Subsequent calls that start with the *exact same prefix* reuse that stored work instead of re-processing it. The cached portion is billed at a steep discount (confirm the current cache-read rate in current AWS docs), and because the model skips re-processing, it also responds faster.

The mental model: think of the model as a chef who has to read the entire recipe book from scratch before cooking each dish. Prompt caching lets the chef keep the standard prep instructions open on the counter — only the day's specific order changes. The fixed part stays put; you pay to read it once, not every order.

Two things make or break caching. First, the cached prefix must be **byte-for-byte identical** across calls — change one character in the system prompt and the cache misses. So put the stable content *first* (system prompt, policy text, few-shot examples) and the variable content *last* (the user's actual question). Second, caches are short-lived — they expire after a few minutes of inactivity (confirm the exact TTL in current AWS docs), so caching pays off under steady traffic, not for a request that arrives once an hour.

#### Example

Northwind's assistant ships a 2,000-token system prompt on every call: the persona ("You are Northwind's support assistant"), the tone rules, the formatting schema, and a block of few-shot examples showing how to cite a policy. During the morning rush the assistant handles thousands of chats an hour, and every one of those chats re-bills the same 2,000 tokens before the customer's one-line question is even considered.

By marking that 2,000-token preamble as a cache checkpoint and placing the customer's question after it, Northwind processes the preamble at full price on the first request of a busy window, then reuses it for the flood of requests that follow within the cache window. The customer's question — the only part that actually changes — is the only part billed at full input rate on those later calls.

#### Implementation

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

# The stable prefix (persona + rules + few-shot) goes FIRST and is marked
# as a cache checkpoint. Everything up to the cachePoint is cached.
# The customer's question goes LAST so the cached prefix stays identical.
response = client.converse(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    system=[
        {"text": NORTHWIND_SYSTEM_PROMPT},        # ~2,000 tokens, never changes
        {"text": FEW_SHOT_CITATION_EXAMPLES},     # also stable
        {"cachePoint": {"type": "default"}},      # cache everything above this marker
        # confirm exact cachePoint field shape in boto3 / Bedrock docs
    ],
    messages=[
        {
            "role": "user",
            "content": [{"text": "What is the holiday return window this year?"}],
        }
    ],
)

# The response includes cache usage so you can confirm a hit.
usage = response["usage"]  # confirm exact usage keys for cache read/write in boto3 docs
print(usage)  # look for cacheReadInputTokens vs cacheWriteInputTokens
```

```text
Request 1 (cache WRITE)
  [ system prompt + few-shot  2000 tok ]  --> processed at full price, stored
  [ customer question ]                   --> processed at full price

Request 2..N within cache window (cache READ)
  [ system prompt + few-shot  2000 tok ]  --> reused, billed at discount, no reprocessing
  [ customer question ]                   --> processed at full price (this is all that changed)
```

#### When & Why

**Use prompt caching when** a large, identical prefix repeats across many calls under steady traffic — a long system prompt, fixed few-shot examples, or a big reference document you ask many questions about. That is exactly Northwind's chat workload.

**Do NOT use it when** the prefix changes every call (per-user personalization injected at the top defeats it), or when traffic is so sparse that the cache expires between requests. Caching a prefix you only hit once wastes the write cost for no read savings.

**Prompt caching vs a smaller model:** caching keeps the *same quality* and cuts the cost of the *repeated* part — reach for it when the repetition is the problem. A smaller model cuts the cost of *every* token but risks quality. If the exam stem says "same long system prompt on every call," that is the caching signal, not the smaller-model signal.

**Prompt caching vs semantic cache:** caching reuses model *work on an identical prefix*; it still generates a fresh answer. A semantic cache (below) skips the model entirely when a *whole question* repeats. They stack — cache the prefix, and separately short-circuit repeat questions.

---

## Intelligent Prompt Routing and Model Cascading

#### Concept

Not every question is hard. "What are your store hours?" and "Explain the warranty implications of a third-party repair on my extended-coverage plan" cost the same if you send both to your most powerful (and most expensive) model. You are overpaying to crush easy questions with a sledgehammer.

Two patterns fix this, and the exam wants you to tell them apart.

**Intelligent Prompt Routing** is a managed Bedrock feature: you send the request to a routing endpoint, and Bedrock predicts up front which model in a family can handle it, sending easy prompts to the cheaper/smaller model and hard prompts to the larger one. The decision happens *before* generation, in one hop. The mental model: a triage nurse who reads the case and sends it to the right specialist immediately.

**Model Cascading** is a pattern *you* build: send the request to the cheap model first; inspect the answer (confidence score, a validation check, or a self-reported "I'm not sure"); and only if it fails your bar do you *escalate* — re-send to the bigger model. The decision happens *after* a first generation. The mental model: a tiered help desk — tier-1 tries first, and only hard tickets get escalated to tier-2.

The trade-off between them: routing is one call and lower latency but relies on an up-front prediction; cascading can make two calls for hard questions (so hard questions cost *more* and are slower) but it decides based on an actual attempt, which can be more accurate about what was truly hard.

#### Example

Northwind's traffic is roughly 80% simple ("where is my order," "what are your hours") and 20% genuinely complex (multi-policy warranty reasoning). Sending all of it to the flagship model is burning budget on the 80% that a small, cheap model answers perfectly well.

With **routing**, Northwind points the chat at Bedrock's prompt-routing endpoint for the Claude family; the easy 80% quietly resolves on the cheaper model and only the hard 20% reaches the flagship. With **cascading**, Northwind instead sends everything to the cheap model first, checks whether the answer cited a policy and cleared a confidence threshold, and re-asks the flagship only when the cheap attempt looks weak — paying the double cost only on the small slice that needs it.

#### Implementation

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

# --- Pattern A: Intelligent Prompt Routing (managed, one hop) ---
# You invoke a prompt-router resource instead of a single model; Bedrock
# picks the model within the configured family.
routed = client.converse(
    modelId="arn:aws:bedrock:us-east-1:111122223333:prompt-router/northwind-router",
    # confirm exact prompt-router ARN/field shape in current AWS docs
    messages=[{"role": "user", "content": [{"text": user_question}]}],
)
```

```python
# --- Pattern B: Model Cascading (you build the escalation logic) ---
CHEAP_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"    # confirm model id in current AWS docs
STRONG_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"  # confirm model id in current AWS docs

def answer_with_cascade(question: str) -> str:
    # 1) Try the cheap model first.
    cheap = client.converse(
        modelId=CHEAP_MODEL,
        messages=[{"role": "user", "content": [{"text": question}]}],
    )
    text = cheap["output"]["message"]["content"][0]["text"]

    # 2) Decide if the cheap answer is good enough.
    #    Here: did it ground itself in a policy? Real systems also use a
    #    confidence score or a structured-output validation check.
    if is_good_enough(text):
        return text

    # 3) Escalate ONLY the hard cases to the expensive model.
    strong = client.converse(
        modelId=STRONG_MODEL,
        messages=[{"role": "user", "content": [{"text": question}]}],
    )
    return strong["output"]["message"]["content"][0]["text"]
```

```text
Routing (managed):   question --> [router predicts] --> cheap OR strong --> answer   (1 hop)

Cascading (DIY):     question --> cheap model --> good enough? --yes--> answer
                                                      |
                                                      no
                                                      v
                                              strong model --> answer               (2 hops on hard cases)
```

#### When & Why

**Use routing when** you want managed, low-latency, per-request model selection across a family and you trust an up-front prediction — minimal code, one hop. **Use cascading when** you want control over the escalation rule, or you can only judge difficulty *after* seeing an attempt (e.g. you validate structured output or a confidence signal), and you accept that hard questions cost two calls.

**Do NOT** use either if your traffic is uniformly hard — then every request escalates anyway and you have added latency and complexity for nothing; just send everything to the capable model. And neither pattern helps if the cost problem is a *repeated identical prefix* — that is prompt caching's job, and the two compose (route to a cheap model *and* cache its prefix).

**Routing/cascading vs just picking one cheaper model (the D1 "cheapest model that clears the bar" call):** picking one model is a static, one-time decision for the *whole* workload. Routing and cascading are *per-request* — they let a mixed workload use the cheap model for easy traffic and the strong model for hard traffic, instead of forcing one compromise model on everything. If the stem says "mixed difficulty, cut cost," that is routing/cascading. If it says "pick the right single model for this task," that is the D1 model-selection call.

---

## Batch Inference

#### Concept

Real-time inference is a premium service: you pay for the model to answer *right now*, while a customer waits. But a huge amount of generative-AI work has no customer waiting — nightly summarization of support transcripts, bulk classification of a document backlog, re-embedding a whole catalog. For that work, speed is irrelevant and only cost matters.

Batch Inference is the answer. You hand Bedrock a file of many prompts sitting in S3, Bedrock processes them asynchronously whenever it has spare capacity (which may take hours), and writes the results back to S3. Because you gave up the "answer now" guarantee, the per-token price is discounted (confirm the current batch discount percentage in current AWS docs).

The mental model: real-time inference is paying for express overnight shipping on every single item; batch inference is loading a pallet onto a freight truck. The freight is far cheaper per item, but it leaves when it's full and arrives when it arrives. You choose it precisely because nobody is waiting at the door.

#### Example

Every night Northwind wants a one-paragraph summary and a sentiment tag for each of the day's 100,000 support conversations, to feed a quality dashboard the team reviews the next morning. Running 100,000 real-time `converse` calls at full price to produce a report nobody reads until 9 a.m. is pure waste — there is no latency requirement at all.

Northwind writes the 100,000 prompts as a JSONL file to `s3://northwind-support-docs/batch/input/`, submits one batch inference job, and lets Bedrock grind through them overnight at the discounted rate. The summaries land in `s3://northwind-support-docs/batch/output/` before the morning standup.

#### Implementation

```python
import boto3

# Batch jobs are a control-plane operation on the "bedrock" client,
# not bedrock-runtime (which is for live, per-request inference).
bedrock = boto3.client("bedrock", region_name="us-east-1")

response = bedrock.create_model_invocation_job(
    # confirm exact create_model_invocation_job params in current boto3 docs
    jobName="northwind-nightly-summaries",
    modelId="anthropic.claude-3-haiku-20240307-v1:0",  # confirm model id in current AWS docs
    roleArn="arn:aws:iam::111122223333:role/BedrockBatchRole",
    inputDataConfig={
        "s3InputDataConfig": {
            "s3Uri": "s3://northwind-support-docs/batch/input/transcripts.jsonl"
        }
    },
    outputDataConfig={
        "s3OutputDataConfig": {
            "s3Uri": "s3://northwind-support-docs/batch/output/"
        }
    },
)

print(response["jobArn"])  # poll job status; results are written to S3 when done
```

```text
Each line of the input JSONL is one independent prompt:
{"recordId": "conv-0001", "modelInput": { ... prompt body ... }}
{"recordId": "conv-0002", "modelInput": { ... prompt body ... }}
...
S3 input file  -->  [ Bedrock batch job, async, discounted ]  -->  S3 output file
                         (runs when capacity is free; hours, not seconds)
```

#### When & Why

**Use batch inference when** the work is offline/bulk and latency does not matter: nightly reports, backfills, bulk classification, re-embedding a corpus. You are explicitly trading speed for a lower per-token price.

**Do NOT use it when** anything is waiting on the answer — a live chat, an interactive agent step, an API that must respond in seconds. Batch results can take hours; using it in a request path would hang the user.

**Batch vs Provisioned Throughput (the classic trap):** both relate to volume, but they solve opposite problems. Batch is *cheapest per token for async bulk*; Provisioned Throughput is *consistent low latency for steady real-time* and costs even while idle. If the stem says "offline, bulk, cost over latency" → Batch. If it says "steady high-volume traffic that must stay fast" → Provisioned. Never answer Provisioned for an offline job (you would pay for idle capacity to do work that had no deadline) and never answer Batch for a latency-sensitive path (you would make a user wait hours).

---

## Latency Levers: Streaming, Provisioned Throughput, and Prompt Compression

#### Concept

Cost and latency are different problems and some levers move only one of them. The exam loves to test whether you know the difference.

**Response streaming** sends the answer token-by-token as it is generated instead of waiting for the whole thing. It dramatically improves *perceived* latency — the time-to-first-token (TTFT) — so a chat feels instant. Crucially, it does **not** change how many tokens are generated or what you pay. It is a user-experience lever, not a cost lever.

**Provisioned Throughput** reserves dedicated model capacity for you. You get consistent latency with no queueing or throttling under load — but you pay a fixed rate whether or not you use it (confirm current Provisioned Throughput pricing in current AWS docs). It buys predictability, at the price of paying for idle time.

**Prompt compression** means trimming redundant or low-value context before you send it — removing boilerplate, de-duplicating retrieved chunks, summarizing long history. Fewer input tokens means both a lower bill *and* faster generation, so it is the rare lever that helps cost and latency at once. The mental model: streaming changes how the meal is *served* (one course at a time, so you start eating sooner); compression changes how much food you *ordered* (less to cook, cheaper and faster); Provisioned Throughput is *renting the whole kitchen* so there is never a wait.

#### Example

Northwind's chat answers felt sluggish because the full reply only appeared after the model finished generating. Turning on streaming made the first words show up almost immediately — the perceived speed jumped even though the total generation time and the token bill were unchanged. Separately, Northwind noticed its RAG step was stuffing five near-duplicate policy chunks into the prompt; compressing that to the two distinct chunks cut input tokens on every call, trimming both cost and generation time. Provisioned Throughput came up only when the team considered a steady, high-volume internal batch of live agent calls that could not tolerate throttling — but with Northwind's spiky customer traffic, reserving capacity would mean paying for idle hours overnight, so they held off.

#### Implementation

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

# Streaming: get tokens as they are produced -> low time-to-first-token.
# Same total tokens, same cost -- this only improves PERCEIVED latency.
stream = client.converse_stream(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm model id in current AWS docs
    messages=[{"role": "user", "content": [{"text": user_question}]}],
)

for event in stream["stream"]:
    if "contentBlockDelta" in event:
        # Push each delta to the UI over WebSocket/SSE as it arrives.
        print(event["contentBlockDelta"]["delta"]["text"], end="")
    # confirm exact streaming event shape in current boto3 docs
```

#### When & Why

**Use streaming when** a human is reading the output live and you want the UI to feel fast — any interactive chat. **Do NOT reach for streaming to cut cost** — it changes nothing on the bill. If the stem says "the chat feels slow to start," that is streaming; if it says "reduce total token cost," streaming is a *distractor*.

**Use Provisioned Throughput when** traffic is steady and high-volume and must never throttle or cold-start. **Do NOT use it for spiky or bursty traffic** — you would pay for reserved capacity that sits idle between bursts; On-Demand fits spiky traffic because you pay only per token used. "Provisioned Throughput plus spiky traffic" is a deliberate wrong-pairing trap.

**Use prompt compression** almost always as free hygiene — fewer tokens is strictly cheaper and faster, as long as you do not trim context the answer actually needs.

---

## The Observability Triad

#### Concept

You cannot optimize what you cannot see. Before you can cut cost or chase down a slow response, you need three different kinds of visibility, and the exam wants you to match each symptom to the right tool.

**Metrics (CloudWatch)** are numbers over time: token counts, invocation counts, error and throttle rates, latency percentiles, estimated spend. Metrics answer "how much" and "how often," and they drive alarms — "page me when throttling spikes." The mental model: the dashboard gauges in a car — speed, fuel, temperature.

**Logs (Model Invocation Logging)** are the full records: the exact prompt sent and the exact response returned for a given call. Logs answer "what actually happened on *this* request" — essential for debugging a bad answer and (as you saw in [Domain 3](/blueprint/dominio-3-seguridad)) for the audit trail. The mental model: the black-box flight recorder.

**Traces (X-Ray)** follow a single request as it hops across services — API Gateway to Lambda to the vector store to Bedrock and back — and time each hop. Traces answer "*which part* of my pipeline is slow." The mental model: a parcel-tracking timeline showing exactly which leg of the journey took hours.

The discriminator: metrics tell you *that* something is wrong and how often; traces tell you *where* in the pipeline; logs tell you *what* the exact prompt and response were. You usually need all three, but each question points at one.

#### Example

Northwind's assistant occasionally feels slow and occasionally returns a wrong policy. CloudWatch metrics first show a nightly latency spike and a climbing throttle count — that is the alarm that wakes someone up. To find *where* the slowness is, X-Ray traces reveal the vector-store retrieval hop, not the model, is the slow leg during that spike. Separately, when a customer reports a flat-out wrong return-window answer, Model Invocation Logging holds the exact prompt and response for that conversation, so the team can see the retrieved context was stale — a data problem, not a model problem.

#### Implementation

```python
# 1) Model Invocation Logging (control plane): capture full prompt/response.
#    Set up once; logs flow to CloudWatch Logs and/or S3.
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")
bedrock.put_model_invocation_logging_configuration(
    # confirm exact put_model_invocation_logging_configuration shape in boto3 docs
    loggingConfig={
        "cloudWatchConfig": {
            "logGroupName": "/northwind/bedrock/invocations",
            "roleArn": "arn:aws:iam::111122223333:role/BedrockLoggingRole",
        },
        "textDataDeliveryEnabled": True,      # include prompt/response text
        "embeddingDataDeliveryEnabled": False,
    }
)
```

```python
# 2) A custom CloudWatch metric for spend/tokens you want to alarm on.
cw = boto3.client("cloudwatch", region_name="us-east-1")
cw.put_metric_data(
    Namespace="Northwind/Assistant",
    MetricData=[
        {
            "MetricName": "InputTokens",
            "Value": response["usage"]["inputTokens"],  # from a converse response
            "Unit": "Count",
        }
    ],
)
# Then create a CloudWatch alarm on throttle/error rate to get paged.
```

```python
# 3) X-Ray trace around the pipeline to find the slow hop.
from aws_xray_sdk.core import xray_recorder  # confirm current X-Ray SDK usage in AWS docs

with xray_recorder.in_segment("support-request"):
    with xray_recorder.in_subsegment("vector-retrieve"):
        context = retrieve_context(question)   # times the retrieval hop
    with xray_recorder.in_subsegment("bedrock-invoke"):
        answer = client.converse(...)          # times the model hop
```

```text
Customer request
   |
   v
API Gateway --> Lambda --> Vector store --> Bedrock --> response
   \________________ X-Ray trace spans every hop (find the slow one) ______________/

CloudWatch metrics: counts, latency, throttles, spend  (alarm: "something is wrong, how often")
Model Invocation Logging: full prompt + response text   (debug: "what exactly happened here")
```

#### When & Why

**Reach for CloudWatch metrics** when the need is an alarm, a threshold, or a trend — "alert me when throttling spikes," "track daily spend." **Reach for X-Ray** when the need is to locate a bottleneck in a multi-service pipeline — "which hop is slow." **Reach for Model Invocation Logging** when the need is the exact content of a specific call — "debug why this one answer was wrong," or a compliance record.

**Do NOT** try to find a slow hop with metrics alone (they tell you total latency is high, not where) and do NOT try to debug a single bad answer with metrics (they have no prompt text). The trap is answering "CloudWatch" for a "which hop is slow" question — that is X-Ray. And note Model Invocation Logging double-duties as the D3 audit trail, so a question can reach it from either the debugging or the compliance angle.

---

## Throttling Resilience

#### Concept

Bedrock enforces per-account, per-model service quotas (requests per minute, tokens per minute). Exceed them and the API returns a `ThrottlingException` (an HTTP 429). Under a traffic burst — a marketing email that drives everyone to chat at once — you *will* hit this, and a naive client that just retries immediately makes it worse: every failed client retries at the same instant, producing a synchronized retry storm that keeps the service pinned.

The resilient pattern has three parts. **Exponential backoff** means waiting longer after each successive failure (1s, then 2s, then 4s) so you stop hammering a service that is already overloaded. **Jitter** means adding a random amount to each wait so that thousands of clients do *not* all retry at the same synchronized moment — jitter is the part that actually breaks the retry storm, and it is the detail the exam checks. **Fallback endpoints** mean that when your primary model or region is saturated, you fail over to a secondary model or another region instead of just waiting. And for capacity you must guarantee in advance, **Provisioned Throughput** reserves headroom so you throttle less in the first place.

The mental model: if a phone line is busy, redialing instantly over and over just keeps it jammed. Waiting progressively longer, each caller waiting a slightly *random* extra beat, lets the line clear — and if it stays busy, you try a different line (the fallback).

#### Example

Northwind sends a promo email; within minutes the chat volume triples and Bedrock starts returning `ThrottlingException`. The first version of the client retried instantly in a tight loop, which only deepened the throttling and dropped answers. The fixed client backs off exponentially with random jitter so retries spread out over time, and if `us-east-1` stays saturated it fails over to the same model family in `eu-west-1`. For the predictable baseline load Northwind also reserved a slice of Provisioned Throughput so the steady portion of traffic never competes for on-demand capacity.

#### Implementation

```python
import random
import time
import boto3
from botocore.exceptions import ClientError

client = boto3.client("bedrock-runtime", region_name="us-east-1")

def invoke_with_backoff(messages, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return client.converse(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm model id in current AWS docs
                messages=messages,
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code != "ThrottlingException":
                raise  # only retry throttling; real errors should surface
            if attempt == max_attempts - 1:
                raise  # out of retries -> escalate to a fallback or fail

            # Exponential backoff: wait grows 1s, 2s, 4s, ...
            base = 2 ** attempt
            # Jitter: a RANDOM extra wait so clients don't retry in lockstep.
            # This is the piece that actually breaks the retry storm.
            wait = base + random.uniform(0, 1)
            time.sleep(wait)
```

```python
# boto3 also has a built-in adaptive retry mode you can configure instead
# of (or alongside) a hand-rolled loop.
from botocore.config import Config

resilient = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=Config(retries={"max_attempts": 5, "mode": "adaptive"}),
    # confirm current retry 'mode' options in boto3 docs
)
```

```text
call --> ThrottlingException? --no--> done
             | yes
             v
      wait = 2^attempt + random jitter   (backoff spreads retries; jitter de-synchronizes them)
             |
      retries left? --yes--> retry
             | no
             v
      fail over to secondary model/region  (fallback endpoint)
```

#### When & Why

**Use exponential backoff with jitter** on any client calling Bedrock that could be throttled — which is effectively all of them. **Add fallback endpoints** when availability matters enough to justify a second model or region. **Add Provisioned Throughput** when you have a known baseline load you cannot afford to have throttled.

**Do NOT** retry in a tight loop with no delay (that *causes* the storm), and do NOT retry non-throttling errors blindly — a validation or auth error will fail the same way every time, so retrying wastes calls and hides the real bug. The exam's favorite distractor is backoff *without* jitter: plain exponential backoff still lets every client retry on the same synchronized schedule, so if the stem offers both, jitter is the better answer. And remember this exact pattern reappears in [Domain 5](/blueprint/dominio-5-testing) as a core fault-tolerance technique — it is shared, not domain-specific.

---

## The decision path (how the levers fit together)

```text
A request / a workload shows up. Ask, in order:

Is anyone waiting on the answer?
  NO  -> offline bulk? ------------------> BATCH INFERENCE (cheapest per token)
  YES -> continue...

Does a big identical prefix repeat every call?
  YES -> PROMPT CACHING (stop re-billing the prefix)

Is the workload mixed easy/hard?
  YES -> ROUTING (managed, 1 hop) or CASCADING (DIY, escalate hard cases)

Does the chat feel slow to start?
  YES -> RESPONSE STREAMING (perceived latency only -- NOT cost)

Is traffic steady+heavy and must never throttle?
  YES -> PROVISIONED THROUGHPUT   |  spiky traffic? -> stay ON-DEMAND

Getting ThrottlingException / 429?
  -> EXPONENTIAL BACKOFF WITH JITTER (+ fallback model/region)

Can't see cost or latency?
  -> metrics=CloudWatch | which hop=X-Ray | exact prompt/response=Model Invocation Logging
```

---

## Exam traps & discriminators

| Stem says | Right move | Trap it beats |
|---|---|---|
| "same 3k-token prefix on every call, cut cost" | Prompt Caching | smaller model / Batch |
| "mixed difficulty, cut cost per request" | Intelligent Prompt Routing / Model Cascading | always using the top model |
| "offline / bulk job, cost over latency" | Batch Inference API *(confirm discount % in docs)* | Provisioned Throughput |
| "steady high-volume, must stay fast, never throttle" | Provisioned Throughput | Batch / On-Demand |
| "spiky / bursty traffic, control cost" | On-Demand | Provisioned Throughput (pays for idle) |
| "chat feels slow to start" | Response streaming (TTFT) | Provisioned / bigger model |
| "does streaming cut token cost?" | No — perceived latency only | treating it as a cost lever |
| "which hop in the pipeline is slow?" | X-Ray traces | CloudWatch metrics alone |
| "alert when throttling / spend spikes" | CloudWatch metrics + alarm | X-Ray |
| "debug why one specific answer was wrong" | Model Invocation Logging | CloudWatch metrics |
| "ThrottlingException / HTTP 429" | Exponential backoff **with jitter** (+ fallback) | tight-loop retry / backoff without jitter |
| "repeated identical whole question" | Semantic cache (ElastiCache) | prompt caching (that's for the prefix) |

## Self-check

Answer each aloud. If you cannot, re-read that concept's four parts.

1. Every call ships the same 2,000-token system prompt. What is the cheapest lever, and what two conditions must hold for it to pay off?
2. Your traffic is 80% easy and 20% hard. Explain routing vs cascading and when each wins.
3. A nightly job summarizes 100,000 transcripts with no deadline. Which inference mode, and why is Provisioned Throughput the wrong answer here?
4. What does jitter add on top of exponential backoff, and why is it the part that actually matters?
5. When is Provisioned Throughput the *wrong* choice despite its consistent low latency?
6. Does response streaming reduce total token cost? If not, what does it actually improve?
7. You need to find which hop of an API Gateway → Lambda → vector store → Bedrock pipeline is slow. Which observability tool, and why not the other two?
8. A customer reports one specific wrong answer. Which observability tool holds what you need, and what does it tell you that metrics cannot?

Confirm on current AWS docs: the prompt-cache read/write rates and TTL, the Batch Inference discount percentage, and current Provisioned Throughput pricing.

Decision tables: [by constraint](/tablas-decision/decision-por-restriccion) · [deployment & inference modes](/tablas-decision/decision-despliegue). Practice: [question bank](/practica/banco-preguntas).
