---
id: labs-hands-on
sidebar_position: 2
title: Optional Hands-On Labs
---

**Optional** and time-boxed. With ~40 hours total, the exam rewards reading scenarios, not building systems — but doing one pass of the Northwind build makes the four-part arcs in the chapters stick. Each lab below **mirrors a step of the Northwind Support Assistant** you read about, so what you built in the console maps straight onto an exam discriminator. Do the **Core** labs if you have ever been unsure what a concept "really" does.

Back to [course home](/) · concepts in [Domain 1](/blueprint/dominio-1-fundacion-datos), [Domain 2](/blueprint/dominio-2-implementacion), and [Domain 3](/blueprint/dominio-3-seguridad).

- **Cost/teardown:** use the cheapest model, tiny inputs, and tear everything down after. The `$300 USD` exam fee dwarfs these costs, but idle resources still add up — delete the Knowledge Base, Guardrail, and agent when done.
- **No real PII or secrets** in any lab. Use obviously fake names and order numbers in your test documents and prompts.
- Placeholders (`northwind-support-docs`, `us-east-1`, account `111122223333`, model ids) are generic — substitute your own and confirm the exact model id in current AWS docs.

## The labs — objective + the discriminator each makes concrete

| Lab | Objective (do this) | The discriminator it proves | Priority | Minutes |
|---|---|---|---|---|
| **1 — Console + Converse + streaming** | Invoke a cheap model with `converse`, then re-run with `converse_stream` | Streaming cuts time-to-first-token (perceived latency), not total compute ([D2](/blueprint/dominio-2-implementacion)) | Core | ~30 |
| **2 — Build `northwind-support-kb` (managed RAG)** | Index a few S3 files, query, then change chunking | Chunking drives Context Recall/Precision ([D5](/blueprint/dominio-5-testing)); Knowledge Bases = least-effort store ([D1](/blueprint/dominio-1-fundacion-datos)) | Core | ~45 |
| **3 — Apply `northwind-support-guardrail`** | Enable a content filter + PII filter; test ANONYMIZE then BLOCK | ANONYMIZE (usable answer) vs BLOCK (halt); Contextual Grounding rejects off-source ([D3](/blueprint/dominio-3-seguridad)) | Do if time | ~30 |
| **4 — Create `northwind-support-agent` + one Action Group** | Agent + a tiny Lambda tool; watch it decide to call it | Action Groups → Lambda is the core agent tool mechanism ([D2](/blueprint/dominio-2-implementacion)) | Do if time | ~45 |

---

## Lab 1 — Converse and streaming (~30 min, Core)

**Story beat:** Northwind wants the chat to *feel* instant. You will see why streaming is the lever, not a bigger model.

1. Pick a cheap text model in `us-east-1` (confirm the exact model id in current AWS docs).
2. Call `converse` once and note how the whole answer arrives at the end.
3. Call `converse_stream` with the same prompt and note the first tokens arriving almost immediately.

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")
model_id = "MODEL_ID_HERE"  # confirm exact model id in current AWS docs

messages = [{"role": "user", "content": [{"text": "In one sentence, what is Northwind's return window?"}]}]

# Non-streaming: the full answer comes back at once.
resp = client.converse(modelId=model_id, messages=messages)
print(resp["output"]["message"]["content"][0]["text"])

# Streaming: tokens arrive incrementally -> lower time-to-first-token.
stream = client.converse_stream(modelId=model_id, messages=messages)
for event in stream["stream"]:
    if "contentBlockDelta" in event:
        print(event["contentBlockDelta"]["delta"].get("text", ""), end="")
```

**What you proved:** streaming changed *perceived* latency (time-to-first-token), not total tokens or cost. That is exactly the [D4](/blueprint/dominio-4-optimizacion) discriminator. **Teardown:** nothing to delete.

## Lab 2 — Build the Knowledge Base `northwind-support-kb` (~45 min, Core)

**Story beat:** this is the D1 "give it KNOWLEDGE" step — grounding the assistant in Northwind's own docs.

1. Create an S3 bucket `s3://northwind-support-docs/` and upload 3–5 small text files (fake return policy, shipping policy, FAQ). **No real PII.**
2. In the Bedrock console, create a Knowledge Base named `northwind-support-kb` pointing at that bucket; let it manage the vector store for least overhead.
3. Query it, then re-ingest with a different chunking strategy and compare which answers improve.

```bash
# Minimal ingestion source setup (confirm exact CLI params in current AWS docs).
aws s3 mb s3://northwind-support-docs/ --region us-east-1
aws s3 cp ./return-policy.txt s3://northwind-support-docs/
# Create the Knowledge Base + data source in the Bedrock console (least-effort path),
# or via the bedrock-agent control-plane API. Confirm exact params in boto3 docs.
```

```python
import boto3

agent_rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

# Retrieve-and-generate: grounded answer from northwind-support-kb.
resp = agent_rt.retrieve_and_generate(
    input={"text": "What is the holiday return window?"},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "KB_ID_HERE",  # from the console after creation
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/MODEL_ID_HERE",  # confirm id in docs
        },
    },
)
print(resp["output"]["text"])
```

**What you proved:** Knowledge Bases is the least-effort managed RAG store ([D1](/blueprint/dominio-1-fundacion-datos)), and changing chunking visibly changes retrieval quality — the Context Recall/Precision link from [D5](/blueprint/dominio-5-testing). **Teardown:** delete the Knowledge Base, its vector store, and the S3 bucket.

## Lab 3 — Apply the Guardrail `northwind-support-guardrail` (~30 min, Do if time)

**Story beat:** the D3 "make it SAFE" step — the assistant can answer, now it must not leak PII or go off-source.

1. Create a Guardrail named `northwind-support-guardrail` with a content filter, a Sensitive Information (PII) filter, and a Contextual Grounding check.
2. Set the PII action to **ANONYMIZE**, send a prompt containing a fake phone number, and confirm a usable answer with the number masked.
3. Switch the action to **BLOCK** and confirm the response is halted instead.

```python
import boto3

rt = boto3.client("bedrock-runtime", region_name="us-east-1")

# Standalone ApplyGuardrail works even for non-Bedrock / self-hosted models.
resp = rt.apply_guardrail(
    guardrailIdentifier="GUARDRAIL_ID_HERE",   # from the console
    guardrailVersion="DRAFT",
    source="OUTPUT",
    content=[{"text": {"text": "Call the customer back at 555-0100."}}],
)
print(resp["action"])        # GUARDRAIL_INTERVENED or NONE
print(resp.get("outputs"))   # masked text when ANONYMIZE
```

**What you proved:** ANONYMIZE returns a usable, masked answer while BLOCK halts — the exact [D3](/blueprint/dominio-3-seguridad) discriminator — and `apply_guardrail` is the standalone path for models outside Bedrock. **Teardown:** delete the Guardrail.

## Lab 4 — Create the agent `northwind-support-agent` + one Action Group (~45 min, Do if time)

**Story beat:** the D2 "make it ACT" step — the assistant stops only describing and starts doing.

1. Write a tiny Lambda that returns a canned order status for a fake order id.
2. Create a Bedrock Agent named `northwind-support-agent` and attach an Action Group whose executor is that Lambda, with a small function schema (`get_order_status(order_id)`).
3. Ask "where is order 12345?" and watch the agent decide to call the tool.

```python
import boto3

agent_rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

# Invoke the agent; it reasons, then calls the Action Group -> Lambda when needed.
resp = agent_rt.invoke_agent(
    agentId="AGENT_ID_HERE",
    agentAliasId="AGENT_ALIAS_HERE",
    sessionId="demo-session-1",
    inputText="Where is order 12345?",
)  # confirm exact params/response streaming shape in boto3 docs
```

**What you proved:** Action Groups → Lambda is the standard agent tool-invocation mechanism ([D2](/blueprint/dominio-2-implementacion)). **Teardown:** delete the agent, the Action Group, and the Lambda.

## Reuse your existing AgentCore repo (Domain 2)

You already have a working, deployable agent in `intro_4h_agentcore`. For the heavier D2 hands-on (Runtime isolation, Memory, tools), redeploy and inspect it instead of rebuilding — it covers most of what Domain 2 teaches:

- **Runtime** — [`agent/main.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/main.py)
- **Memory (short + long-term)** — [`agent/memoria.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/memoria.py)
- **Tools (Action-Group-style)** — [`agent/herramientas.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/herramientas.py)
- Start here: [`intro_4h_agentcore` README](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md)

Resources: [resources](/recursos). Back to [plan](/plan-estrategico).
