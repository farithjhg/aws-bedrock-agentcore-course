---
id: dominio-1-fundacion-datos
sidebar_position: 2
title: Domain 1 — Foundation, Data & Compliance (31%)
---

Northwind Retail is building the Northwind Support Assistant from scratch. Right now it is an empty idea: no model chosen, no knowledge, no way to answer a customer. In this domain we give it KNOWLEDGE — we choose a foundation model, build retrieval-augmented generation (RAG) over Northwind's own support documents, pick where those document vectors live, and learn to engineer and govern the prompts. By the end, the assistant can answer a customer's question grounded in Northwind's real policies. It still cannot *do* anything — that comes next in [Domain 2](/blueprint/dominio-2-implementacion).

Back to [course home](/) · [exam strategy](/blueprint/vision-examen) · overlaps [Domain 3](/blueprint/dominio-3-seguridad).

This is the heaviest domain on the exam. Do not skim it. Each concept below is taught the same way: first the idea, then a Northwind scenario, then code you could actually run, then the decision rule the exam tests. Read the Concept part even for topics you think you know — the exam traps live in the gap between "I've heard of RAG" and "I understand why RAG beats fine-tuning here."

---

## RAG vs Fine-Tuning (the core D1 decision)

#### Concept

A foundation model (FM) ships frozen. Its "knowledge" is whatever was in its training data, captured at training time and never updated. Two problems follow from that single fact: the model does not know your private information (it never saw Northwind's return policy), and it does not know anything that changed after training (last week's holiday-return update). You have two fundamentally different tools to fix this, and they fix different problems.

**RAG (Retrieval-Augmented Generation)** does not change the model at all. Think of it as giving the model an open book during the exam. At query time you search a knowledge store for the passages relevant to the question, paste those passages into the prompt, and ask the model to answer *using only this text*. The model's weights never move. Swap a document and the next answer reflects it instantly. RAG adds *knowledge*.

**Fine-tuning** changes the model's weights by continuing training on your examples. Think of it as sending the model back to school. You are not handing it facts to read — you are reshaping its instincts: how it phrases things, what format it returns, what tone it adopts, how it handles a specialized task. Fine-tuning adds *behavior*.

The mental model that keeps you out of trouble: **RAG is memory you can edit; fine-tuning is a skill you have to teach.** Facts you will keep changing belong in RAG. Behavior you cannot coax out with a good prompt belongs in fine-tuning.

#### Example

A Northwind customer asks: "Can I still return the blender I bought on December 20th? Your holiday page mentioned an extended window." The real return policy lives in `s3://northwind-support-docs/return-policy.pdf`, and the holiday extension was published *last week*. 

If Northwind had fine-tuned a model on its old policies, that model would confidently quote the *previous* 30-day window — wrong, and it would stay wrong until the next expensive retraining run. With RAG, the assistant searches `northwind-support-docs`, pulls the paragraph describing the extended holiday window, and answers from it. When legal changes the window again next year, Northwind re-uploads one PDF and the assistant is correct the same afternoon. No training, no redeploy.

Notice *why* this scenario decides RAG: the deciding fact is fresh and proprietary. That is the signal.

#### Implementation

The fastest correct RAG path on AWS is a Bedrock Knowledge Base plus the `retrieve_and_generate` call, which does retrieval and generation in one managed step.

```python
import boto3

# bedrock-agent-runtime is the DATA-plane client for Knowledge Bases + Agents.
# (bedrock-runtime is for raw model calls; bedrock-agent is the CONTROL plane.)
agent_rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

resp = agent_rt.retrieve_and_generate(
    input={"text": "Can I return a blender bought on December 20th?"},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "KB1234567890",  # the northwind-support-kb id
            # The generation model is the FM that writes the final answer
            # from the retrieved passages. confirm exact model id in current AWS docs.
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-...",
        },
    },
)

print(resp["output"]["text"])          # grounded answer
for c in resp["citations"]:            # which doc chunks backed the answer
    print(c)                           # use citations to show sources / audit
```

If you only want the retrieved passages (for example to build your own prompt, or to inspect what the search returned), call `retrieve` by itself:

```python
hits = agent_rt.retrieve(
    knowledgeBaseId="KB1234567890",
    retrievalQuery={"text": "holiday return window"},
    retrievalConfiguration={
        "vectorSearchConfiguration": {"numberOfResults": 5}  # top-k chunks
    },
)
for h in hits["retrievalResults"]:
    print(h["content"]["text"], h["score"])
```

Fine-tuning is a different workflow entirely — a control-plane job on `bedrock`, not a per-request call. The shape (not an exact signature) looks like this:

```python
bedrock = boto3.client("bedrock", region_name="us-east-1")

# You point at a JSONL training file in S3 and get a CUSTOMIZED model back.
# This is a one-time (slow, costed) job, not something you run per question.
bedrock.create_model_customization_job(
    jobName="northwind-tone-tuning",
    customModelName="northwind-support-tone-v1",
    roleArn="arn:aws:iam::111122223333:role/BedrockCustomizationRole",
    baseModelIdentifier="arn:aws:bedrock:us-east-1::foundation-model/...",  # confirm id
    trainingDataConfig={"s3Uri": "s3://northwind-training/tone-examples.jsonl"},
    outputDataConfig={"s3Uri": "s3://northwind-training/output/"},
    # confirm exact params (hyperParameters, customizationType) in boto3 docs
)
```

The RAG query-time flow, sketched:

```text
            INGEST (once / on doc change)              QUERY (per question)
  S3: northwind-support-docs                   customer question
        |  chunk + embed (Titan Embeddings)          |  embed question (same model!)
        v                                             v
   [ vector store: northwind-support-kb ]  <----- similarity search (top-k)
                                                      |  retrieved passages
                                                      v
                                            prompt = passages + question
                                                      |
                                                      v
                                            FM generates grounded answer + citations
```

#### When & Why

**Use RAG when** the need is fresh or proprietary *facts*: internal docs, policies that change, anything you want to edit without retraining. It is cheap to update, auditable (you get citations), and the first thing to reach for in D1.

**Use fine-tuning when** the model will not produce the *behavior* you need even with a well-crafted prompt — a consistent house tone, a strict output format, a narrow specialized task. Fine-tuning does not teach facts well, and it goes stale the moment the facts change.

**How to choose:** ask "is the gap knowledge or behavior?" A gap in knowledge ("it doesn't know our latest policy") is always RAG — fine-tuning on facts you will keep changing is the classic wrong answer because you would retrain forever. A gap in behavior ("it won't follow our tone no matter how I prompt it") is fine-tuning. They are not mutually exclusive: a mature system often fine-tunes for tone *and* uses RAG for facts. On the exam, a stem that says "latest internal documents, no retraining" is RAG; a stem that says "won't match our required format even with good prompts" is fine-tuning.

---

## PEFT / LoRA vs Full Fine-Tuning

#### Concept

Once you have decided to fine-tune, a second decision appears: *how much* of the model do you retrain? A large FM has billions of parameters. 

**Full fine-tuning** updates all of them. You get maximum adaptation, but you pay for it: you need a large, high-quality labeled dataset, a lot of compute, and you end up storing a whole new copy of the model.

**PEFT (Parameter-Efficient Fine-Tuning)**, of which **LoRA (Low-Rank Adaptation)** is the best-known method, freezes the original weights and trains a small set of new "adapter" parameters alongside them. The mental model: instead of rewriting the whole textbook, you clip a thin set of sticky notes onto it. Far less data and compute, far smaller artifact, and you can keep several adapters for several tasks on top of one base model.

Why PEFT exists: full fine-tuning is overkill for most real adaptation needs, and its cost and data requirements put it out of reach. PEFT gets you most of the behavioral change for a fraction of the cost.

#### Example

Northwind wants the assistant to always answer in its brand voice: warm, concise, and ending with a specific sign-off. Prompting gets close but drifts over long conversations. This is a *behavior* gap, so fine-tuning — but Northwind has only a few thousand curated example exchanges, not a massive labeled corpus. LoRA is the fit: a small adapter trained on those examples nudges the tone reliably, costs little, and can be re-trained quickly when the brand team tweaks the voice. Full fine-tuning here would demand far more data than Northwind has and produce a bulky model for what is essentially a styling change.

#### Implementation

On Bedrock, customization type is a parameter on the same customization job; you select the efficient method rather than hand-coding LoRA math.

```python
bedrock = boto3.client("bedrock", region_name="us-east-1")

bedrock.create_model_customization_job(
    jobName="northwind-tone-lora",
    customModelName="northwind-tone-v1",
    roleArn="arn:aws:iam::111122223333:role/BedrockCustomizationRole",
    baseModelIdentifier="arn:aws:bedrock:us-east-1::foundation-model/...",  # confirm id
    trainingDataConfig={"s3Uri": "s3://northwind-training/tone.jsonl"},
    outputDataConfig={"s3Uri": "s3://northwind-training/out/"},
    # customizationType selects the method; FINE_TUNING vs other efficient modes.
    # confirm the exact enum + supported methods per model in current AWS docs.
    customizationType="FINE_TUNING",
    hyperParameters={
        "epochCount": "1",       # fewer epochs/data than full tuning
        # confirm exact hyperparameter keys in boto3 docs
    },
)
```

```text
  Base FM  (weights FROZEN)
     +  small LoRA adapter (the only thing trained)
     =  customized model  -> deploy for inference
  Full fine-tuning instead: retrain ALL weights -> new full-size model
```

#### When & Why

**Default to PEFT / LoRA.** It is the right answer in the large majority of exam stems because it delivers behavioral adaptation with modest data and cost.

**Choose full fine-tuning only when** you have a large labeled dataset *and* a deep-adaptation need — a substantial shift in the model's core capability, not a tone or format tweak. On the exam, full fine-tuning is usually the distractor: if a stem describes a modest dataset or a formatting/tone goal and offers both, PEFT/LoRA wins. Pick full fine-tuning only when the stem explicitly signals heavy data and deep specialization.

---

## Choosing a Foundation Model (family contrast + the cost trap)

#### Concept

Bedrock offers several model families, and each one leads on a different axis. You do not memorize benchmark scores — you learn the *one deciding axis* per family so a stem's keyword maps to a family. Just as important: the strongest model is rarely the right answer. Every call costs tokens, and a top-tier reasoning model doing a trivial classification is burning money. The discipline is **pick the cheapest model that still clears the quality bar for the task** — not the most capable model available.

The mental model: choosing an FM is like staffing a task. You do not assign your most expensive senior engineer to sort the mail. Match the model's strength (and cost) to what the task actually demands.

The families and their deciding axis:

| Family | The ONE deciding axis | Exam cue |
|---|---|---|
| **Anthropic Claude** | Top reasoning / long context (higher cost) | "complex reasoning", "long documents", "high-quality agent" |
| **Meta Llama** | Open weights, cost-sensitive general use | "open-weight", "customizable", cost-sensitive general |
| **Amazon Titan** | AWS-native; Titan Embeddings for RAG | "embeddings", lightweight text, AWS-native stack |
| **Amazon Nova** | Tiered cost/quality (Micro/Lite/Pro; Sonic is speech) | "cheap/fast small tier for simple tasks", voice (Sonic) |

One trap lives inside the Titan row and matters enough to flag now: **embeddings**. An embedding model turns text into a vector. For RAG to work, the vectors you create when ingesting documents must come from the *same* embedding model you use to embed the incoming question — otherwise the two live in different vector spaces and similarity search returns garbage. The exam cue is not *which* embedding model is best; it is that the ingestion and query embedding models **must match**.

#### Example

Northwind faces three sub-tasks while building the assistant. (1) The main answer generation over long policy documents, where reasoning quality matters — Claude fits the "long documents, high-quality" cue. (2) A cheap pre-step that classifies whether an incoming message is about "returns", "shipping", or "billing" so it can be routed — a trivial label task that a small Nova tier handles at a fraction of the cost; using Claude here would be the cost trap. (3) Turning every policy chunk and every question into vectors for RAG — Titan Embeddings, and Northwind must use the exact same embedding model at ingestion and at query time or retrieval silently breaks.

#### Implementation

Generating an answer with the unified `converse` API (model-agnostic — swap `modelId` to change families without rewriting the call):

```python
import boto3
rt = boto3.client("bedrock-runtime", region_name="us-east-1")

resp = rt.converse(
    # Pick the cheapest model that clears the bar. confirm exact model id in AWS docs.
    modelId="anthropic.claude-3-sonnet-...",
    messages=[{"role": "user", "content": [{"text": "Summarize our return policy."}]}],
    inferenceConfig={"maxTokens": 500, "temperature": 0.2},
)
print(resp["output"]["message"]["content"][0]["text"])
```

Creating embeddings with Titan (same model id must be reused at ingest and query):

```python
import json
rt = boto3.client("bedrock-runtime", region_name="us-east-1")

def embed(text):
    out = rt.invoke_model(
        modelId="amazon.titan-embed-text-...",   # confirm exact model id in AWS docs
        body=json.dumps({"inputText": text}),
    )
    return json.loads(out["body"].read())["embedding"]

doc_vector = embed("Holiday returns are accepted within the extended window.")  # at INGEST
q_vector   = embed("Can I return my blender?")                                  # at QUERY
# Both vectors come from the SAME model id -> same vector space -> search works.
```

The cheap classification pre-step on a small tier:

```python
resp = rt.converse(
    modelId="amazon.nova-micro-...",   # small/cheap tier; confirm exact id in AWS docs
    messages=[{"role": "user", "content": [{"text":
        "Classify this message as returns, shipping, or billing. Message: 'where is my package'"}]}],
    inferenceConfig={"maxTokens": 5, "temperature": 0},
)
```

#### When & Why

**Use Claude** when the stem stresses reasoning depth, long context, or a high-quality agent and cost is secondary. **Use Llama** when the stem stresses open weights or customization on a cost-sensitive general task. **Use Titan** for embeddings and AWS-native lightweight text. **Use a small Nova tier** when the task is simple and the stem rewards low cost/latency — and use Nova Sonic when voice/speech appears.

**Do NOT reach for the strongest model by default.** If the task is trivial (classification, routing, short extraction), the cheapest capable model is the correct answer and the top-tier model is the trap. This cost discipline connects directly to Intelligent Prompt Routing in [Domain 4](/blueprint/dominio-4-optimizacion), which automates "easy question gets the cheap model." And never let the ingestion and query embedding models diverge — that is a correctness bug, not a tuning choice.

---

## Embeddings & Chunking

#### Concept

RAG only works if retrieval actually finds the right passage. Two mechanisms decide that: how you cut documents into pieces (**chunking**), and how you turn those pieces into searchable vectors (**embeddings**, covered above). 

Why chunk at all? You cannot embed a 90-page manual as one vector — the meaning blurs and retrieval becomes useless. You split it into chunks so each vector represents one coherent idea. *How* you split is the lever, and there is a progression:

- **Fixed-size chunking** cuts every N characters or tokens. Simple and fast, but it slices blindly — a sentence or a policy clause can be severed mid-idea, so the chunk that should have answered the question is split across two chunks and retrieval misses it.
- **Hierarchical chunking** keeps structure: a small child chunk is matched for precision, but its parent (the surrounding section) is returned for context. Better recall because the answer's context travels with it.
- **Semantic chunking** splits on *meaning* — it detects where one topic ends and the next begins and cuts there. Cleanest signal, best boundaries, but more expensive to compute at ingest.

Mental model: chunking is deciding where to tear the pages. Tear mid-sentence (fixed) and the reader loses the thought; tear at topic boundaries (semantic) and every page stands on its own.

#### Example

Northwind's warranty terms document has a clause: "Electronics carry a 1-year warranty; however, items marked clearance are sold as-is." Fixed-size chunking happened to cut right after "1-year warranty," dropping the clearance exception into a different chunk. A customer asks about a clearance blender's warranty; retrieval returns the "1-year" chunk, and the assistant wrongly promises warranty coverage. Switching to semantic (or hierarchical) chunking keeps the full clause — condition and exception — together, so the retrieved passage carries the complete rule.

#### Implementation

Bedrock Knowledge Bases lets you declare the chunking strategy at ingestion time on the data source, so you rarely hand-roll it:

```python
agent = boto3.client("bedrock-agent", region_name="us-east-1")

agent.create_data_source(
    knowledgeBaseId="KB1234567890",
    name="northwind-docs-source",
    dataSourceConfiguration={
        "type": "S3",
        "s3Configuration": {"bucketArn": "arn:aws:s3:::northwind-support-docs"},
    },
    vectorIngestionConfiguration={
        "chunkingConfiguration": {
            # FIXED_SIZE | HIERARCHICAL | SEMANTIC | NONE
            # confirm exact enum values + nested config keys in boto3 docs
            "chunkingStrategy": "SEMANTIC",
        }
    },
)
```

```text
  Fixed:        [....cut....][....cut....]   <- may split one idea across two chunks
  Hierarchical: child chunk (match) --> returns PARENT section (context)
  Semantic:     [whole idea A][whole idea B] <- cuts at topic boundaries, cleanest
```

#### When & Why

**Start with fixed-size** for prototypes or clean, uniformly structured text — it is cheap and often good enough. **Move to hierarchical** when answers are losing surrounding context (recall is the problem). **Move to semantic** when document structure is messy and clean boundaries matter most and you can absorb the higher ingest cost.

The exam framing: if answers *miss information that genuinely exists in the docs*, that is a retrieval/recall problem — fix chunking and retrieval, do **not** rewrite the prompt. This maps to the RAGAS Context Recall metric in [Domain 5](/blueprint/dominio-5-testing). A better prompt cannot surface a fact that retrieval never fetched.

---

## Retrieval Levers (hybrid search, reranking, query decomposition)

#### Concept

Even with good chunks, the *search* step can return noise — technically-similar passages that are not what the user meant. Three levers tighten retrieval:

- **Hybrid search** combines semantic (vector) search with keyword (lexical) search. Pure vector search can miss an exact term (a product SKU, an error code) that keyword search nails; combining both covers each other's blind spots.
- **Reranking** runs a second, more precise model (for example Cohere Rerank) over the top-k results and reorders them by true relevance to the question, pushing the best passage to the top. It raises *precision* — fewer irrelevant chunks reach the model.
- **Query decomposition** breaks a multi-part question into sub-questions, retrieves for each, and combines. A question like "what's your return window and does it cover clearance items" is really two retrievals.

Mental model: hybrid search casts two complementary nets; reranking is a strict second reviewer that re-sorts the catch; query decomposition splits a compound request so each part gets its own search.

#### Example

A Northwind customer pastes an order error code and asks what it means. Pure semantic search returns vaguely related "order status" passages but not the exact code's entry — keyword search inside hybrid retrieval finds the literal code. Separately, when retrieval for policy questions keeps surfacing three loosely-related paragraphs, adding a reranker reorders them so the one paragraph that actually answers the question lands first, and the assistant stops padding answers with near-misses.

#### Implementation

Knowledge Bases expose search type and reranking in the retrieval configuration:

```python
agent_rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

hits = agent_rt.retrieve(
    knowledgeBaseId="KB1234567890",
    retrievalQuery={"text": "clearance item warranty"},
    retrievalConfiguration={
        "vectorSearchConfiguration": {
            "numberOfResults": 10,
            # HYBRID combines semantic + keyword; SEMANTIC is vector-only.
            "overrideSearchType": "HYBRID",
            # Reranking reorders results by true relevance (raises precision).
            # confirm exact rerankingConfiguration keys/model ids in boto3 docs
            # "rerankingConfiguration": { ... },
        }
    },
)
```

```text
  question -> [ hybrid search: vector + keyword ] -> top-k candidates
                                                        |
                                            [ reranker reorders by relevance ]
                                                        |
                                          best passages first -> into the prompt
```

#### When & Why

**Add hybrid search** when exact terms matter (codes, SKUs, names) and pure vector search is missing them. **Add reranking (+ semantic chunking)** when retrieval is *noisy* — the right passage is being retrieved but buried under irrelevant ones. That is a *precision* problem (RAGAS Context Precision in [Domain 5](/blueprint/dominio-5-testing)), and the fix is reranking, **not** a bigger generation model — a stronger model cannot fix a noisy context, it just reasons over noise more expensively. **Add query decomposition** for multi-part questions. Distinguish the two failure modes cleanly: missing info that exists = recall = fix chunking/retrieval; noisy/irrelevant retrieved context = precision = rerank + semantic chunking.

---

## Vector Store Selection

#### Concept

The embeddings produced during ingestion have to live somewhere that supports fast similarity search — that is the **vector store**. AWS gives you several, and they trade off managed-effort, scale, search capability, and whether you reuse existing infrastructure. You pick by matching the dominant constraint in the stem to one decisive keyword:

| Store | Decisive keyword |
|---|---|
| **Bedrock Knowledge Bases** | least effort / managed turn-key RAG |
| **OpenSearch Serverless** | hybrid (keyword + semantic) at scale |
| **Aurora PostgreSQL + pgvector** | reuse an existing relational DB |
| **Amazon Kendra** | enterprise doc search with connectors |
| **S3 Vectors** | ultra-large scale, cost-sensitive (not speed) |

Mental model: this is a "what do I already have and what do I care about most" decision. Least effort and you have no infra opinion: Knowledge Bases manages it. Already running Aurora Postgres: add `pgvector` and skip a new system. Need lexical plus semantic at serious scale: OpenSearch Serverless. Billions of vectors and cost beats latency: S3 Vectors.

#### Example

Northwind's platform team already runs Aurora PostgreSQL for the orders database. For a first RAG build they could enable `pgvector` and store document embeddings right next to relational data — no new service to operate. But because the support corpus is large and they want both keyword and semantic matching on messy docs, they instead let the managed `northwind-support-kb` sit on **OpenSearch Serverless** as its vector backend, getting hybrid search at scale without running the cluster themselves. Full reasoning and traps for each option live in the [vector store table](/tablas-decision/decision-vector-stores).

#### Implementation

When you create the Knowledge Base, its `storageConfiguration` names the vector backend:

```python
agent = boto3.client("bedrock-agent", region_name="us-east-1")

agent.create_knowledge_base(
    name="northwind-support-kb",
    roleArn="arn:aws:iam::111122223333:role/KnowledgeBaseRole",
    knowledgeBaseConfiguration={
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            # The embedding model used at INGEST (must match query-time embedding).
            "embeddingModelArn":
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-...",
        },
    },
    storageConfiguration={
        # Swap this block to choose the backend (OpenSearch Serverless, pgvector, etc.)
        "type": "OPENSEARCH_SERVERLESS",
        "opensearchServerlessConfiguration": {
            "collectionArn": "arn:aws:aoss:us-east-1:111122223333:collection/abc123",
            "vectorIndexName": "northwind-index",
            # confirm exact fieldMapping keys in boto3 docs
            "fieldMapping": {
                "vectorField": "embedding",
                "textField": "text",
                "metadataField": "metadata",
            },
        },
    },
)
```

```text
  northwind-support-kb (managed RAG)
        |
        +-- embedding model: Titan Embeddings (ingest == query)
        |
        +-- storage backend (pick ONE):
              OpenSearch Serverless | Aurora pgvector | S3 Vectors | ...
```

#### When & Why

**Knowledge Bases** when the goal is least operational effort and a turn-key managed RAG. **OpenSearch Serverless** when you need hybrid search at scale and are fine letting a managed collection back the KB. **Aurora + pgvector** when you already run that relational DB and want to avoid a new system. **Kendra** when the ask is enterprise document search with built-in connectors (SharePoint, etc.) rather than raw vector plumbing. **S3 Vectors** when the corpus is ultra-large and cost beats latency — explicitly *not* when you need real-time speed. The discriminator is always the single dominant constraint: least effort, reuse, scale+hybrid, connectors, or cost-at-huge-scale.

---

## Prompt Engineering & Governance (Prompt Management vs Prompt Flows)

#### Concept

The prompt is the instruction wrapped around the retrieved context before it reaches the model. Engineering it well — clear role, explicit "answer only from the provided context", a temperature low enough to stay factual — is half of RAG quality. But in production you cannot leave prompts scattered as string literals in code. Two Bedrock features govern them, and the exam insists you not confuse them:

- **Prompt Management** stores prompts as **versioned templates** — named, versioned, editable without a code deploy, and reusable across the app. It is version control for prompts.
- **Prompt Flows** chain and route prompts: a visual/declarative graph where output of one step branches into another, with conditionals. It is orchestration of multiple prompt steps.

Mental model: Prompt Management is the *library of documents* (one prompt, many versions); Prompt Flows is the *flowchart* that wires several prompts together with branches. One stores, the other connects.

A related governance pattern: Northwind will want to **swap the active model without redeploying code**. The clean answer is indirection — keep the model id in **AWS AppConfig**, read it at runtime in a Lambda fronted by API Gateway, and change the config value to switch models live. The model id lives in configuration, not in source.

#### Example

Northwind's support team keeps refining the assistant's system prompt ("be concise, cite the policy section, never promise a refund amount"). Storing it in Prompt Management means a non-engineer can publish a new version and roll back if answers regress — no deploy. Separately, Northwind builds a Prompt Flow: first a prompt classifies the question type, then branches to a returns-specialized prompt or a billing-specialized prompt. And when Northwind wants to A/B a cheaper model next month, ops flips the model id in AppConfig and the running Lambda picks it up — no redeploy.

#### Implementation

A well-governed RAG prompt passed through `converse`, with the model id read from AppConfig rather than hard-coded:

```python
import boto3, json

appconfig = boto3.client("appconfigdata", region_name="us-east-1")
rt = boto3.client("bedrock-runtime", region_name="us-east-1")

# Read the active model id from config -> switching models needs NO code deploy.
# confirm exact appconfigdata session/get-latest call shape in boto3 docs
model_id = "anthropic.claude-3-sonnet-..."   # value comes from AppConfig at runtime

SYSTEM = (
    "You are the Northwind Support Assistant. Answer ONLY using the provided "
    "context. If the answer is not in the context, say you don't know. "
    "Cite the policy section. Never promise a specific refund amount."
)

def answer(question, context_passages):
    resp = rt.converse(
        modelId=model_id,
        system=[{"text": SYSTEM}],
        messages=[{"role": "user", "content": [{"text":
            f"Context:\n{context_passages}\n\nQuestion: {question}"}]}],
        inferenceConfig={"temperature": 0.1, "maxTokens": 400},  # low temp = factual
    )
    return resp["output"]["message"]["content"][0]["text"]
```

```text
  swap model without redeploy:
    API Gateway -> Lambda -> reads model id from AppConfig -> bedrock-runtime
                                 ^ change config value = new model, no deploy
```

#### When & Why

**Use Prompt Management** when the need is versioning, reuse, and editing prompts without deploys — the keyword is *versioned templates*. **Use Prompt Flows** when the need is *branching/routing* across multiple prompt steps. Do not swap them: a stem about "store and version our prompts" is Management; a stem about "route to different prompts based on the question" is Flows. **Use AppConfig indirection** (Lambda + API Gateway + AppConfig) when the requirement is to change the active model with no code deploy — the trap answer is hard-coding the model id and redeploying.

---

## Data Quality & Compliance Fundamentals

#### Concept

RAG inherits the quality of its source data. Garbage documents produce confidently wrong answers — the model faithfully grounds its reply in a bad record. So before data reaches the knowledge base it should be validated. **AWS Glue Data Quality** defines rules (completeness, uniqueness, allowed ranges, freshness) that records must pass; failing records are caught before they poison retrieval. The mental model: a quality gate on the conveyor belt into the knowledge store — bad parts never reach assembly.

On the compliance side, Domain 1 only needs the foundation: encrypt data at rest (KMS) and in transit (TLS), know where your data physically lives (region), and keep provenance so you can answer "where did this answer's facts come from" (the citations RAG returns are part of this). The deeper safety machinery — Guardrails, PII redaction, network isolation, audit trails — is [Domain 3](/blueprint/dominio-3-seguridad); here you just establish that clean, well-governed data is the precondition for a trustworthy assistant.

#### Example

Northwind's shipping-policy document was uploaded with a half-finished draft paragraph and a placeholder "TBD shipping fee." Without validation, RAG would retrieve "TBD" and the assistant would tell a customer the fee is "TBD." A Glue Data Quality rule that flags records containing placeholder tokens or missing required fields catches the draft before ingestion, so only clean, complete policy text reaches `northwind-support-kb`.

#### Implementation

A Glue Data Quality ruleset is written in DQDL and attached to the dataset that feeds ingestion:

```python
glue = boto3.client("glue", region_name="us-east-1")

glue.create_data_quality_ruleset(
    Name="northwind-docs-quality",
    # DQDL rules: reject incomplete/placeholder records before they reach the KB.
    # confirm exact DQDL rule syntax + attach/run API in current AWS docs
    Ruleset='Rules = [ ColumnValues "fee" matches "[0-9]+", Completeness "policy_text" > 0.95 ]',
)
```

A minimal CLI check that a documents bucket enforces encryption at rest (compliance baseline):

```bash
# Verify server-side encryption is configured on the docs bucket.
aws s3api get-bucket-encryption \
  --bucket northwind-support-docs \
  --region us-east-1
```

```text
  S3 raw docs -> [ Glue Data Quality gate: pass/fail rules ]
                         pass |            | fail -> quarantine / fix
                              v
                 clean docs -> ingest -> northwind-support-kb
  (at rest: KMS encryption | in transit: TLS | provenance: RAG citations)
```

#### When & Why

**Use Glue Data Quality** when the requirement is to validate records *before* they enter a pipeline or knowledge store — the exam cue is "bad/incomplete data is reaching the model" or "ensure data quality before retrieval." It is a preventive gate, not a runtime filter on model output (that is Guardrails, in [Domain 3](/blueprint/dominio-3-seguridad)). On compliance, when a stem asks the D1-level question — encryption, region/residency awareness, provenance — reach for KMS/TLS/region and citations; when it escalates to redaction, jailbreak defense, or audit trails, that is Domain 3 territory. "Best practice" framed answers usually align with the Well-Architected [Generative AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html).

---

## Exam traps & discriminators

This table recaps what the arcs above taught — use it as a last-minute review, not as a first read.

| Stem says | Right move | Trap it beats |
|---|---|---|
| "answer from latest internal PDFs, no retraining" | RAG | fine-tuning / higher temperature |
| "won't follow our tone/format even with good prompts" | PEFT/LoRA fine-tuning | RAG / full fine-tuning |
| modest dataset, tone/format goal, fine-tuning chosen | PEFT/LoRA | full fine-tuning |
| trivial task (classify/route) | cheapest capable model | top-tier model (cost trap) |
| embedding setup for RAG | same embedding model at ingest `&` query | mixing embedding models |
| "answers miss info that's in the docs" | fix chunking/retrieval (Context Recall) | rewrite the prompt |
| "retrieval is noisy/irrelevant" | reranking + semantic chunking (Precision) | bigger model |
| exact terms/codes being missed | hybrid search | pure semantic search |
| least-effort managed RAG | Bedrock Knowledge Bases | standing up OpenSearch yourself |
| reuse existing relational DB | Aurora PostgreSQL + pgvector | new dedicated vector service |
| billions of vectors, cost over speed | S3 Vectors | low-latency store |
| "store/version our prompts" | Prompt Management | Prompt Flows |
| "route between prompts by question type" | Prompt Flows | Prompt Management |
| "switch active model, no code deploy" | Lambda + API Gateway + AppConfig | hard-code id + redeploy |
| "bad/incomplete data reaching the model" | Glue Data Quality gate | output-side filtering |

## Self-check

Answer each aloud, in a sentence or two, before looking back.

1. Latest internal PDFs, no retraining — RAG or fine-tuning, and *why* is the other one wrong?
2. You've decided to fine-tune and have a few thousand tone examples — PEFT/LoRA or full, and why is full the trap?
3. A trivial classification step is using a top-tier model. What is wrong, and what connects this to Domain 4?
4. Why must the ingestion and query embedding models be identical, and what breaks if they differ?
5. Answers omit a detail that is present in the source docs — which RAGAS metric, and do you fix the prompt or retrieval?
6. Retrieval keeps returning noisy, loosely-related chunks — which metric, which two levers, and why not a bigger model?
7. Billions of vectors, cost matters more than latency — which store, and which store would be the trap?
8. Prompt Management vs Prompt Flows — one-line distinction, plus how you'd switch the active model without a deploy.

Confirm on AWS docs: current model families/tiers, context windows, embedding-model options, Knowledge Bases chunking/reranking features, and exact API parameters.

Decision tables: [vector stores](/tablas-decision/decision-vector-stores) · [by constraint](/tablas-decision/decision-por-restriccion). Practice: [question bank](/practica/banco-preguntas) · [hands-on labs](/practica/labs-hands-on).
