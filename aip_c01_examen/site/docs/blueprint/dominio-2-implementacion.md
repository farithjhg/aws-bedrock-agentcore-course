---
id: dominio-2-implementacion
sidebar_position: 3
title: Domain 2 — Implementation & Integration (26%)
---

Back to [course home](/) · previous step [Domain 1](/blueprint/dominio-1-fundacion-datos) · cost ripple into [Domain 4](/blueprint/dominio-4-optimizacion) · safety in [Domain 3](/blueprint/dominio-3-seguridad).

In [Domain 1](/blueprint/dominio-1-fundacion-datos) we gave the Northwind Support Assistant KNOWLEDGE: it can retrieve Northwind's policies and answer grounded questions. But a customer who types "cancel my order" still only gets *described* to — the assistant can talk, not act. It can tell you the return policy; it cannot start the return. In this domain we make it ACT. We turn the knowledge-grounded assistant into an **agent with tools** (Action Groups, and MCP tools through AgentCore Gateway), choose how we **deploy and run inference**, add **response streaming** so the chat feels instant instead of frozen, and wire **event-driven orchestration** for multi-step jobs like processing a return. By the end, the assistant can both retrieve and *do*. Keeping all that power safe is [Domain 3](/blueprint/dominio-3-seguridad).

This is the second-heaviest domain (26%). Everything below is taught as the course's four-part arc — Concept, Example, Implementation, When and Why — so you finish able to explain each idea, sketch the call, and pick the right service under a constraint you have not seen before.

---

### From assistant to agent: tools, Action Groups, and the AgentCore components

#### Concept

A plain language model is a brilliant conversationalist with no hands. It can read, reason, and write a paragraph, but it cannot look up *your* order number, call *your* refund API, or write a row to *your* database. An **agent** is that same model given hands: a loop where the model can decide "I need to call a tool", you run the tool, you feed the result back, and the model continues until it has an answer. That loop — reason, act, observe, repeat — is what turns a chatbot into something that gets work done.

The mental model: the model is the *brain*, the tools are the *hands*, and the agent framework is the *nervous system* that carries signals between them. You describe each tool to the model (its name, what it does, what inputs it needs). When the model decides a tool is needed, it does not execute anything itself — it emits a structured request ("call `cancel_order` with `order_id=12345`"). Your code runs the real function and returns the result. The model never touches your systems directly; it only ever *asks*. That indirection is what keeps it safe and testable.

AWS gives you three distinct ways to build this, and the exam leans hard on telling them apart:

- **Bedrock Agents** — a *managed* agent. You define the agent, attach **Action Groups** (groups of tools backed by a Lambda function plus an API schema), and Bedrock runs the reason-act-observe loop for you. Least code, least control.
- **Amazon Bedrock AgentCore** — a *production platform* for agents, organized into five components. It is the answer when the stem is about running agents at production scale with isolation, memory, and observability.
- **Strands Agents** — a *code SDK*. You write the agent loop in Python yourself and keep full control. The answer when the stem says "we want to define the agent in code / in our own framework".

The **five AgentCore components** are a frequent discriminator. Learn them by the problem each one solves:

- **Runtime** — runs each agent session in its own microVM sandbox, so one customer's session cannot bleed into another's. Cue: "per-session isolation", "sandboxed execution".
- **Gateway** — exposes existing APIs and Lambda functions as agent tools, speaking the open **MCP** (Model Context Protocol) standard. Cue: "turn our existing REST APIs into tools", "MCP server".
- **Memory** — remembers context across turns and across sessions, so the assistant knows what the customer said yesterday. Cue: "remember the conversation / preferences".
- **Observability** — traces and monitors every step the agent took, so you can debug why it chose a tool. Cue: "see / debug the agent's steps".
- **Identity** — controls who and what the agent is allowed to call (auth, JWT, delegated access). Cue: "secure which systems the agent can reach".

**MCP** (Model Context Protocol) deserves its own mention: it is an open standard for describing tools so that *any* MCP-aware agent can use them without custom glue. AgentCore Gateway is how AWS turns your existing APIs into MCP tools.

#### Example

A customer opens the Northwind chat and types: "I want to cancel order 100492, it hasn't shipped yet."

With the Domain 1 assistant, the best it could do was retrieve the cancellation policy from `northwind-support-docs` and paraphrase it: "Orders can be cancelled before they ship." Useful, but the customer still has to go find the cancel button themselves. The grounding worked; the *action* did not exist.

Now we give it two tools:

- `check_order_status(order_id)` — reads the order from Northwind's order service.
- `cancel_order(order_id)` — calls Northwind's fulfillment API to cancel.

The agent loop now runs: the model reads the request, decides it first needs `check_order_status("100492")`, our Lambda calls the order service and returns `status: "PENDING"`, the model sees the order has not shipped, decides to call `cancel_order("100492")`, our Lambda calls fulfillment, and the model replies "Done — order 100492 is cancelled and a refund is on its way." The same knowledge base is still there for policy questions; we have simply added hands. Each tool is a small, auditable Lambda — exactly the boundary [Domain 3](/blueprint/dominio-3-seguridad) will lock down and human-approval-gate.

#### Implementation

First, the shape of a Bedrock **Agent** plus an **Action Group** on the control plane. An Action Group binds a set of tools (described by an OpenAPI schema) to a Lambda executor.

```python
import boto3

# Control plane client: creates/manages agents, action groups, knowledge bases.
bedrock_agent = boto3.client("bedrock-agent", region_name="us-east-1")

# 1) Create the managed agent. The foundationModel is the "brain".
#    The instruction is the agent's standing system prompt / persona.
agent = bedrock_agent.create_agent(
    agentName="northwind-support-agent",
    # Use a real current model id shape; pin the exact version from docs.
    foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    instruction=(
        "You are Northwind Retail's support assistant. Use the knowledge base "
        "for policy questions and the action group tools to check and cancel orders. "
        "Never cancel an order that has already shipped."
    ),
    agentResourceRoleArn="arn:aws:iam::111122223333:role/northwind-agent-role",
)
agent_id = agent["agent"]["agentId"]

# 2) Attach an Action Group. The actionGroupExecutor points at the Lambda
#    that actually runs the tools; the apiSchema describes the tools to the model.
bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion="DRAFT",
    actionGroupName="order-actions",
    actionGroupExecutor={"lambda": "arn:aws:lambda:us-east-1:111122223333:function:northwind-order-tools"},
    # The schema tells the MODEL what tools exist and their parameters.
    apiSchema={"s3": {"s3BucketName": "northwind-agent-config", "s3ObjectKey": "order-actions-openapi.json"}},
    # confirm exact apiSchema / functionSchema shape in current boto3 docs
)
```

The **Lambda tool executor** receives the model's chosen action and returns a result. Bedrock passes the action group, the API path/function, and the parameters; you dispatch, do the real work, and return a response in the shape Bedrock expects.

```python
# northwind-order-tools Lambda handler.
import json
import urllib.request  # stand-in for Northwind's internal order/fulfillment SDK

def lambda_handler(event, context):
    # Bedrock Agents tells us which tool the model picked and with what params.
    api_path = event.get("apiPath")          # e.g. "/cancel_order"
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    order_id = params.get("order_id")

    if api_path == "/check_order_status":
        status = _get_order_status(order_id)         # real call to order service
        body = {"order_id": order_id, "status": status}
    elif api_path == "/cancel_order":
        # Guard rail in code too: never cancel a shipped order.
        if _get_order_status(order_id) == "SHIPPED":
            body = {"error": "Order already shipped; cannot cancel."}
        else:
            _cancel_order(order_id)                   # real call to fulfillment API
            body = {"order_id": order_id, "result": "CANCELLED"}
    else:
        body = {"error": f"Unknown tool {api_path}"}

    # Return in the response shape Bedrock Agents expects.
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "apiPath": api_path,
            "httpMethod": event.get("httpMethod"),
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": json.dumps(body)}},
        },
    }

def _get_order_status(order_id):
    ...  # call Northwind order service; returns "PENDING" / "SHIPPED" / ...
def _cancel_order(order_id):
    ...  # call Northwind fulfillment API
```

If you prefer to drive the loop yourself without a managed agent, the **Converse API with tool use** gives you the same reason-act-observe loop in code (this is also how the Strands SDK works under the hood):

```python
import boto3, json

rt = boto3.client("bedrock-runtime", region_name="us-east-1")

# Describe tools to the model. The model will REQUEST a call; you execute it.
tool_config = {
    "tools": [{
        "toolSpec": {
            "name": "cancel_order",
            "description": "Cancel a Northwind order that has not yet shipped.",
            "inputSchema": {"json": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            }},
        }
    }]
}

messages = [{"role": "user", "content": [{"text": "Cancel order 100492, it hasn't shipped."}]}]

resp = rt.converse(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    messages=messages,
    toolConfig=tool_config,
)

# If the model asks for a tool, run it and send the result back in the next turn.
if resp["stopReason"] == "tool_use":
    for block in resp["output"]["message"]["content"]:
        if "toolUse" in block:
            tu = block["toolUse"]
            result = _cancel_order(tu["input"]["order_id"])   # your real function
            messages.append(resp["output"]["message"])        # model's tool request
            messages.append({"role": "user", "content": [{
                "toolResult": {
                    "toolUseId": tu["toolUseId"],
                    "content": [{"json": {"result": result}}],
                }
            }]})
    # Second call: model now has the tool result and writes the final reply.
    final = rt.converse(modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        messages=messages, toolConfig=tool_config)
```

Exposing an *existing* API as an MCP tool through **AgentCore Gateway** is a configuration step, not a rewrite — the open-source `intro_4h_agentcore` repo in this workspace already wires tools this way:

```bash
# Conceptual: register an existing API as an MCP tool via AgentCore Gateway.
# The Gateway fronts your API and advertises it to any MCP-aware agent.
aws bedrock-agentcore create-gateway-target \
  --gateway-id northwind-gw \
  --name order-service \
  --target-type openapi \
  --openapi-s3 s3://northwind-agent-config/order-service-openapi.json
# confirm exact command/params in current AWS CLI docs
```

Architecture sketch of the agent loop:

```text
Customer ──"cancel order 100492"──▶ Agent (brain = FM)
                                      │  1. reason: "need order status"
                                      ▼
                           Action Group / MCP tool (hands)
                                      │  2. Lambda calls Northwind order API
                                      ▼
                               order status = PENDING
                                      │  3. model reasons: safe to cancel
                                      ▼
                           Action Group / MCP tool: cancel_order
                                      │  4. Lambda calls fulfillment API
                                      ▼
   Knowledge Base ◀── (policy lookups still available) ──┘
                                      │  5. model writes final reply
                                      ▼
                     "Done — order 100492 cancelled, refund on its way."
```

#### When & Why

**When to turn the assistant into an agent:** the moment it needs to *do* something, not just answer — look up live data, call an API, change state. If every requirement can be met by retrieving a document and paraphrasing it, you do not need tools; stay with plain RAG from Domain 1 and avoid the extra moving parts.

**Which builder to pick:**

- Choose **Bedrock Agents** when you want AWS to manage the loop and you are happy defining tools as Action Groups — fastest path, least code. This beats hand-rolling when the team is small and the orchestration is standard.
- Choose **AgentCore** when the stem stresses *production* concerns: per-session isolation (Runtime), cross-session memory, step-level observability, identity/auth, or exposing many existing APIs as MCP tools (Gateway). It beats bare Bedrock Agents when the cue is operational maturity, not just "make an agent".
- Choose **Strands** when the requirement is to define the agent *in code / our own framework* with full control. It beats the managed options when control and portability matter more than hand-holding.

**Match the AgentCore component to the cue, do not swap:** "microVM / per-session isolation" is always **Runtime**; "expose existing APIs / MCP" is always **Gateway**; "remember across sessions" is always **Memory**; "debug the steps" is always **Observability**; "auth / who can it call" is always **Identity**.

**A near-neighbor the exam loves — where does tool code run?** Put bursty, short-lived tools on **Lambda** (scale-to-zero, you pay per invocation; perfect for a `cancel_order` call that runs for a second). Put **long-running or stateful** tool servers (a persistent MCP server, a process holding a big model or a warm connection pool) on **ECS/Fargate**. Pick Lambda when load is spiky and each call is short; pick ECS when the server must stay up or hold state between calls.

**Another near-neighbor — agent memory vs app state.** Use **AgentCore Memory** when the requirement is *conversational/preference memory for the agent* ("remember the customer's earlier messages"). Use **DynamoDB** for general application state (order records, session tokens, a shopping cart). They look similar; the deciding word is whether it is the *agent's* memory or the *app's* data.

---

### Converse API vs InvokeModel: one call shape for every model

#### Concept

Every foundation model speaks a slightly different dialect. Anthropic Claude wants its messages shaped one way; Amazon Titan and Meta Llama want theirs shaped another. If you call the raw `InvokeModel` API, *you* are responsible for building the exact JSON body each model family expects and for parsing each model's bespoke response. Swap models and you rewrite your request-building code.

The **Converse API** is Bedrock's answer to that pain: one unified, model-agnostic request and response shape that works across model families. You hand it a list of messages and, optionally, a tool config; Bedrock translates to and from whatever the underlying model needs. Switching from Claude to Llama becomes a one-line `modelId` change instead of a rewrite. Converse also standardizes multi-turn conversations and **tool use** (the agent loop above) across models.

The mental model: `InvokeModel` is speaking each model's native language directly; **Converse is a universal translator** sitting in front of all of them. You learn one grammar and talk to every model.

So why does `InvokeModel` still exist? Because sometimes you need a model-specific feature or body field that the unified shape does not surface, or you are doing a simple single-shot call and do not care about portability. And `invoke_model_with_response_stream` is the streaming variant you reach for when you need raw token-by-token output (covered next).

#### Example

Northwind's chat backend started on Claude. A cost review in [Domain 4](/blueprint/dominio-4-optimizacion) later suggests routing simple FAQ questions to a cheaper small model and only hard questions to Claude. If the backend had been built on `InvokeModel`, every model would need its own request-builder and response-parser, and the routing layer would be a tangle of per-model special cases. Because Northwind built on **Converse**, the router just changes `modelId` per request — the message shape, the tool config, and the parsing all stay identical. The portability the exam keeps asking about is exactly this: Converse made the "cheapest model that clears the bar" decision cheap to *implement*.

#### Implementation

A single Converse call, model-agnostic:

```python
import boto3

rt = boto3.client("bedrock-runtime", region_name="us-east-1")

resp = rt.converse(
    # Change ONLY this line to switch model families — body shape stays the same.
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    messages=[
        {"role": "user", "content": [{"text": "What is Northwind's holiday return window?"}]}
    ],
    # Optional: standard inference controls, same keys across models.
    inferenceConfig={"maxTokens": 512, "temperature": 0.2},
)

# Unified response shape regardless of model family.
answer = resp["output"]["message"]["content"][0]["text"]
print(answer)
```

The same intent with raw `InvokeModel` requires you to hand-build the model-specific body — shown here only to feel the contrast:

```python
import boto3, json

rt = boto3.client("bedrock-runtime", region_name="us-east-1")

# Model-SPECIFIC body: this JSON shape is Anthropic's; Titan/Llama differ.
body = {
    "anthropic_version": "bedrock-2023-05-31",  # confirm current value in AWS docs
    "max_tokens": 512,
    "messages": [{"role": "user", "content": "What is Northwind's holiday return window?"}],
}

resp = rt.invoke_model(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    body=json.dumps(body),
)
# You must also parse the model-SPECIFIC response shape yourself.
payload = json.loads(resp["body"].read())
answer = payload["content"][0]["text"]
```

#### When & Why

**Use Converse** as the default for any new chat/agent backend, especially when the stem mentions *portability across models*, *model-agnostic*, *tool use*, or *multi-turn conversation*. It wins because it decouples your code from any one model family and standardizes tool use — the enabler for cascading and routing in Domain 4.

**Use `InvokeModel`** when you need a model-specific body field Converse does not expose, or for a one-off single-shot call where portability is irrelevant. **Use `invoke_model_with_response_stream`** when you specifically want raw streaming tokens and are not using the Converse streaming variant.

**The trap:** a stem that says "we want to swap models without rewriting our integration" and offers `InvokeModel` as a distractor. The portability answer is always **Converse**.

---

### Response streaming: make the chat feel instant

#### Concept

A model generates an answer token by token. If you wait for the *entire* answer before showing anything, the user stares at a frozen screen for several seconds, then the whole paragraph appears at once. **Streaming** sends each token to the client as it is produced, so words start appearing almost immediately — the same way a person types a reply while thinking.

The key insight, and the single most tested point here: streaming improves **time-to-first-token (TTFT)** and therefore *perceived* latency. It does **not** make the model compute faster, does **not** reduce total tokens, and does **not** reduce cost. The total generation time and the bill are the same; the user just *feels* it as responsive because something appears right away instead of after a long silence.

The mental model: streaming is not a faster chef, it is a waiter who brings each dish the moment it is ready instead of holding the whole meal until dessert is plated. The kitchen (the model) works at the same speed; the table just feels busier and faster.

Because of this, streaming is the answer to "the chat feels slow to *start*" — and the *wrong* answers are "use a bigger model" (bigger is usually slower) and "use Provisioned Throughput" (that addresses throughput/consistency, not time-to-first-token).

#### Example

Northwind's first chat UI used a non-streaming call. A customer asks "walk me through how to return a defective blender", the model needs to produce a six-step answer, and the UI shows a spinner for several seconds before the whole block appears. Support testers reported it "feels broken" even though the answer was correct and total latency was fine.

Switching the backend to `converse_stream` changed nothing about the model or the cost — the first words ("Sure, here's how to return a defective blender...") now appear almost immediately and the rest fills in as the customer reads. Same total time, completely different feel. The tokens are pushed to the browser over a WebSocket (or Server-Sent Events) fronted by API Gateway.

#### Implementation

Streaming with the Converse API — iterate the event stream and forward each chunk:

```python
import boto3

rt = boto3.client("bedrock-runtime", region_name="us-east-1")

stream = rt.converse_stream(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    messages=[{"role": "user", "content": [{"text": "How do I return a defective blender?"}]}],
)

# Each event carries a small delta. Push it to the client as it arrives.
for event in stream["stream"]:
    if "contentBlockDelta" in event:
        token = event["contentBlockDelta"]["delta"].get("text", "")
        push_to_client(token)        # e.g. send over the WebSocket to the browser
    elif "messageStop" in event:
        break
# confirm exact event keys in current boto3 docs
```

The lower-level `invoke_model_with_response_stream` when you are not on Converse:

```python
import boto3, json

rt = boto3.client("bedrock-runtime", region_name="us-east-1")

resp = rt.invoke_model_with_response_stream(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",  # confirm current value in AWS docs
        "max_tokens": 512,
        "messages": [{"role": "user", "content": "How do I return a defective blender?"}],
    }),
)

for chunk in resp["body"]:           # EventStream of byte chunks
    data = json.loads(chunk["chunk"]["bytes"])
    if data.get("type") == "content_block_delta":
        push_to_client(data["delta"].get("text", ""))
# confirm exact chunk shape in current boto3 docs
```

Architecture sketch of streaming delivery:

```text
Browser ◀── token ── token ── token ──  (words appear as they arrive)
   ▲ WebSocket / SSE
   │
API Gateway  (WebSocket API, or HTTP with SSE)
   ▲
   │  forwards each delta
Lambda / backend  ── converse_stream ──▶  Bedrock model
                   ◀── contentBlockDelta stream ──
```

#### When & Why

**Use streaming** whenever a human is watching a non-trivial answer appear in real time — chat UIs, long explanations, anything where "it feels slow to start" is the complaint. It is the correct fix for *perceived* latency.

**Do NOT reach for streaming** when nothing is waiting on the first token: batch jobs, backend-to-backend calls where you need the whole response before doing anything, or when you must parse the full JSON before acting. Streaming adds client-side complexity (you must reassemble tokens and handle partial output) for no benefit there.

**Choosing vs near-neighbors:** if the problem is *time-to-first-token / perceived slowness*, pick **streaming**. If the problem is *inconsistent throughput or cold starts under steady load*, that is **Provisioned Throughput** (next section), not streaming. If the problem is *the answer itself is wrong*, no delivery mechanism helps — that is a Domain 1 model/retrieval issue. Deliver streamed tokens to the browser over **WebSockets or SSE via API Gateway**.

---

### Deployment and inference modes: how you buy capacity

#### Concept

Choosing a model is half the decision; the other half is *how you run it*. The same model can be served several ways, and the right one depends on your traffic shape, your latency needs, and your budget. These modes are a reliable source of exam questions because the keywords map cleanly to the answer.

Think of it like buying compute the way you buy electricity or a car:

- **On-Demand** — pay per token as you go, no commitment. Like metered electricity. Great for variable, unpredictable traffic; you never pay for idle capacity.
- **Provisioned Throughput** — you reserve a guaranteed amount of model capacity for a committed term and pay for it whether or not you use it. Like leasing a dedicated line. It buys *consistent low latency and no cold starts* for steady, mission-critical traffic — and it is wasteful (you pay for idle) when traffic is spiky.
- **SageMaker endpoints** — host *your own* model weights (a fine-tuned or open-source model Bedrock does not serve) on managed infrastructure, with scale-to-zero options. The answer when the cue is "host our custom / open-source weights".
- **Batch Inference API** — submit a large pile of inputs for *asynchronous* bulk processing at a lower per-token price (confirm the discount in current AWS docs). You trade latency (results come later) for cost. The answer for offline, no-one-is-waiting jobs.
- **Model Cascading** — send every request to a cheap small model first and only escalate the hard cases to an expensive model. A cost pattern more than a hosting mode; it pairs with Domain 4's routing.

The mental model: On-Demand is a taxi (pay per ride), Provisioned Throughput is leasing a car (pay monthly, always available), SageMaker endpoints are building your own garage for a car AWS does not rent, Batch is mailing a stack of letters overnight instead of couriering each one, and Cascading is trying the cheap tool first and reaching for the expensive one only when needed.

#### Example

Northwind has three distinct workloads, and each wants a different mode:

- **The live chat assistant** has bursty daytime traffic that drops to almost nothing overnight. On-Demand fits — Northwind never pays for idle capacity, and the per-token price is fine at this volume.
- **Black Friday** is coming. For that week the chat must have guaranteed low latency with zero cold starts under sustained heavy load, and the traffic is predictable. Northwind reserves **Provisioned Throughput** for the peak window and releases it afterward. If they had left that on all year, they would be paying for idle capacity — which is exactly the spiky-traffic trap.
- **Overnight, Northwind re-summarizes 200,000 product descriptions** for better retrieval. No customer is waiting; it just has to be done by morning and cost matters. That is the **Batch Inference API**.

Separately, a plan to escalate only hard questions to Claude while cheap FAQs go to a small model is **Model Cascading**, and hosting a fine-tuned Llama that Bedrock does not serve would need a **SageMaker endpoint**.

#### Implementation

Submitting a **Batch Inference** job (offline bulk, cost over latency):

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")

# Batch reads a JSONL file of records from S3 and writes results back to S3.
job = bedrock.create_model_invocation_job(
    jobName="northwind-nightly-resummarize",
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    roleArn="arn:aws:iam::111122223333:role/northwind-batch-role",
    inputDataConfig={"s3InputDataConfig": {
        "s3Uri": "s3://northwind-support-docs/batch/input/descriptions.jsonl"}},
    outputDataConfig={"s3OutputDataConfig": {
        "s3Uri": "s3://northwind-support-docs/batch/output/"}},
)
print(job["jobArn"])
# confirm exact create_model_invocation_job params in current boto3 docs
```

Buying **Provisioned Throughput** for the peak window (control plane):

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")

# Reserve dedicated capacity (model units) for consistent latency / no cold starts.
pt = bedrock.create_provisioned_model_throughput(
    provisionedModelName="northwind-chat-peak",
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # confirm exact model id in current AWS docs
    modelUnits=1,                 # confirm sizing in current AWS docs
    # commitmentDuration controls the committed term; omit for no-commitment where allowed.
)
# Then call the returned provisioned model ARN as the modelId in converse/invoke_model.
# confirm exact create_provisioned_model_throughput params in current boto3 docs
```

On-Demand needs no provisioning at all — it is simply calling `converse` / `invoke_model` with a base model id, as in the earlier sections. SageMaker endpoint hosting uses the `sagemaker` / `sagemaker-runtime` clients to deploy and invoke your own weights; the cue is simply "custom/open-source weights".

Architecture sketch of the mode decision:

```text
                       ┌──────────────────────────────────────────────┐
  Is anyone waiting?   │                                              │
        │  no          ▼                                              │
        └────────▶ Batch Inference API  (bulk, cheaper, async)        │
        │  yes                                                        │
        ▼                                                             │
  Traffic shape? ── spiky/variable ──▶ On-Demand (pay per token)      │
        │                                                             │
        └── steady + low-latency + mission-critical ──▶ Provisioned   │
        │                                                Throughput   │
        └── our own fine-tuned/OSS weights ──▶ SageMaker endpoint     │
        └── mostly easy, few hard ──▶ Model Cascading (cheap→escalate)│
                       └──────────────────────────────────────────────┘
```

Full picker and traps: [deployment table](/tablas-decision/decision-despliegue).

#### When & Why

- **On-Demand** when traffic is variable/bursty and you want no commitment. It beats Provisioned whenever there is meaningful idle time, because Provisioned bills for idle.
- **Provisioned Throughput** when traffic is steady and the workload is mission-critical with strict, consistent latency and no tolerance for cold starts. It beats On-Demand only when utilization is high and predictable; on spiky traffic it is the classic *wrong* answer (you pay for capacity you are not using).
- **SageMaker endpoints** when Bedrock does not serve the model you need — your fine-tuned or open-source weights. It beats Bedrock On-Demand precisely when the model is not a Bedrock-hosted one.
- **Batch Inference API** when the job is offline, large, and latency-insensitive and cost matters. It beats On-Demand for bulk because of the lower per-token price; it is wrong whenever a user is waiting. (Trap: AWS *Batch* the compute service is out of scope — the answer is the **Bedrock Batch Inference API**.)
- **Model Cascading** when most requests are easy and only a few are hard; it caps cost by spending the expensive model only when needed. It pairs with Intelligent Prompt Routing in [Domain 4](/blueprint/dominio-4-optimizacion).

---

### Event-driven orchestration: Step Functions vs EventBridge

#### Concept

Some agent tasks are a single call. Others are a *process*: "process this return" means validate the order, check warranty, issue a refund, schedule a pickup, email the customer — several steps, some of which can fail and need a retry, some of which branch on a condition, and one of which might need a human to approve a large refund. You do not want the agent itself babysitting that whole multi-step flow; you want an orchestrator built for it.

AWS gives two tools that look similar but solve opposite problems, and the exam punishes swapping them:

- **AWS Step Functions** — a *workflow orchestrator*. You define an explicit state machine: step 1, then step 2, retry step 3 three times on failure, branch here, wait for a human approval token there. It *tracks state* across the whole process and knows where it is. Use it when the flow has **ordered steps, retries, branches, or a human-approval gate**.
- **Amazon EventBridge** — an *event bus*. A thing happens ("order cancelled"), you publish an event, and any number of independent consumers react to it — asynchronously, decoupled, fire-and-forget. It does not track a multi-step flow or wait for a result. Use it for **async decoupling and fan-out**.

The mental model: Step Functions is a *recipe with checkboxes* — it knows the order, re-does a step that failed, and pauses for the chef's approval. EventBridge is a *public address announcement* — "order 100492 was cancelled!" — and whoever cares (refund service, analytics, email service) acts on their own, with no one tracking whether they all finished.

#### Example

A customer confirms "yes, process the return for order 100492." That is a *process*, so Northwind uses **Step Functions**: validate the return is in policy → check warranty → *if the refund is over a threshold, pause for a human approval* → issue the refund → schedule a carrier pickup → notify the customer. Each step can be retried on a transient API error, the flow branches on the refund amount, and the whole thing has a visible, auditable state. That human-approval gate is the same pattern [Domain 3](/blueprint/dominio-3-seguridad) uses for sensitive actions.

Compare that to the moment an order is simply cancelled. Northwind publishes one **EventBridge** event, `OrderCancelled`, and three unrelated systems react independently: the analytics pipeline logs it, the inventory service restocks the item, the email service sends a confirmation. Northwind does not care about ordering or retries across those three — they are decoupled consumers reacting to a fact. That is fan-out, not a workflow.

#### Implementation

A **Step Functions** state machine (Amazon States Language) for the multi-step return — note the retry and the human-approval wait:

```json
{
  "Comment": "Northwind: process a customer return",
  "StartAt": "ValidateReturn",
  "States": {
    "ValidateReturn": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:111122223333:function:validate-return",
      "Retry": [
        { "ErrorEquals": ["States.TaskFailed"], "MaxAttempts": 3, "BackoffRate": 2.0 }
      ],
      "Next": "RefundNeedsApproval"
    },
    "RefundNeedsApproval": {
      "Type": "Choice",
      "Choices": [
        { "Variable": "$.refundAmount", "NumericGreaterThan": 200, "Next": "HumanApproval" }
      ],
      "Default": "IssueRefund"
    },
    "HumanApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "request-human-approval",
        "Payload": { "taskToken.$": "$$.Task.Token", "input.$": "$" }
      },
      "Next": "IssueRefund"
    },
    "IssueRefund": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:111122223333:function:issue-refund",
      "Next": "SchedulePickup"
    },
    "SchedulePickup": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:111122223333:function:schedule-pickup",
      "End": true
    }
  }
}
```

An **EventBridge** publish for the decoupled, fire-and-forget fan-out:

```python
import boto3, json

events = boto3.client("events", region_name="us-east-1")

# Publish one fact; independent consumers (analytics, inventory, email) subscribe
# via their own rules. The publisher does not wait or track completion.
events.put_events(Entries=[{
    "Source": "northwind.orders",
    "DetailType": "OrderCancelled",
    "Detail": json.dumps({"order_id": "100492", "reason": "customer_request"}),
    "EventBusName": "northwind-bus",
}])
# confirm exact put_events shape in current boto3 docs
```

Architecture sketch — orchestration (ordered, stateful) vs eventing (decoupled fan-out):

```text
STEP FUNCTIONS (process a return — ordered, retried, can pause):
  Validate ─▶ refund > $200? ──yes──▶ Human approval ─▶ Issue refund ─▶ Schedule pickup
                 └────no───────────────────────────────▲

EVENTBRIDGE (order cancelled — fan-out, fire-and-forget):
                       ┌─▶ Analytics pipeline
  OrderCancelled ──────┼─▶ Inventory restock
   (one event)         └─▶ Email service
```

#### When & Why

**Use Step Functions** when the stem describes an ordered, multi-step process with **retries, branching, error handling, or a human-approval gate**, and you need to know the state of the flow. It beats EventBridge because EventBridge has no concept of "step 2 after step 1", no built-in retry-of-a-step, and no waiting for an approval token.

**Use EventBridge** when the need is **asynchronous decoupling / fan-out** — one thing happened, many independent consumers react, and no one is tracking an overall result. It beats Step Functions here because a state machine would be heavyweight overkill for "announce a fact and move on", and it does not match the fire-and-forget, many-consumers shape.

**The trap, stated plainly:** "retries + fallback + human approval" is always **Step Functions**; "async fan-out, fire-and-forget" is always **EventBridge**. Do not swap them. (They also *compose* — an EventBridge event can start a Step Functions workflow — but the exam cue picks one as the primary answer.)

**Cost ripple into [Domain 4](/blueprint/dominio-4-optimizacion):** multi-step agent flows and ReAct loops improve reasoning but **multiply token cost**, because every reasoning step is more tokens. The correct exam answer usually pairs them with a Domain 4 mitigation — **model cascading** or **Intelligent Prompt Routing**. Teaching the assistant to *act* is powerful; it also makes every request more expensive, which is the problem Domain 4 exists to solve.

---

## Reuse what you already built

You do not have to build the agent from scratch to practice this domain. The companion repo `intro_4h_agentcore` in this workspace already demonstrates the AgentCore components end to end: Runtime ([`agent/main.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/main.py)), Memory ([`agent/memoria.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/memoria.py)), and tool wiring ([`agent/herramientas.py`](https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/herramientas.py)). Redeploy it and read those three files against the four arcs above instead of rebuilding — the guided steps are in [labs](/practica/labs-hands-on).

---

## Exam traps & discriminators

This table recaps what the arcs above taught — read it as a summary, not as the lesson.

| Stem says | Right move | Trap it beats (and why) |
|---|---|---|
| "chat feels slow to start" | Response streaming (cuts time-to-first-token) | Provisioned / bigger model — those change throughput or quality, not perceived start latency |
| "retries + fallback + human-approval gate" | Step Functions (stateful workflow) | EventBridge alone — no ordered steps, no step retry, no approval wait |
| "async fan-out, fire-and-forget" | EventBridge (event bus) | Step Functions — overkill; no multi-step state to track |
| "expose existing APIs as agent tools" | AgentCore Gateway (MCP) | rewriting the API as a model — Gateway fronts what you already have |
| "per-session microVM isolation" | AgentCore Runtime | the other four components — isolation is Runtime's job |
| "remember across turns/sessions" | AgentCore Memory | DynamoDB — that is general app state, not agent memory |
| "host our fine-tuned / open-source weights" | SageMaker endpoint | Bedrock On-Demand — Bedrock does not serve your custom weights |
| "steady, mission-critical, no cold starts" | Provisioned Throughput | On-Demand — but Provisioned is the trap on *spiky* traffic (pays for idle) |
| "nightly bulk job, cost over latency" | Bedrock Batch Inference API | AWS Batch (out of scope) and On-Demand (no bulk discount) |
| "swap models without rewriting integration" | Converse API | `InvokeModel` — model-specific body defeats portability |
| "bursty/short tool" vs "long-running/stateful tool server" | Lambda vs ECS/Fargate | swapping them — scale-to-zero vs always-on state |
| "multi-agent / ReAct raised our cost" | pair with cascading / Intelligent Prompt Routing | accept the cost — more steps means more tokens |

Full pickers: [deployment](/tablas-decision/decision-despliegue) · [by constraint](/tablas-decision/decision-por-restriccion).

## Self-check

Answer each out loud; if you cannot, re-read the matching arc above.

1. Which AgentCore component gives per-session microVM isolation, and which exposes existing APIs as MCP tools?
2. "The chat feels slow to start" — what is the best implementation change, and why is a bigger model or Provisioned Throughput wrong here?
3. A workflow with retries, a fallback, and a human-approval gate: which orchestration service, and why not EventBridge?
4. When would you pick a SageMaker endpoint over Bedrock On-Demand?
5. What does the Converse API give you that raw `InvokeModel` does not, and when would you still use `InvokeModel`?
6. Where do long-running, stateful tool servers run versus bursty short-lived tools, and why?
7. Northwind's traffic is spiky all year except a predictable one-week peak — which inference mode(s) for which part, and what is the trap if you reserve Provisioned Throughput year-round?
8. Why do multi-agent and ReAct loops raise cost, and which two Domain 4 levers mitigate it?

Confirm on AWS docs: current AgentCore components, Converse API tool-use shape, Bedrock Agents / Action Group schema, Batch Inference and Provisioned Throughput parameters, and exact model ids.

Decision tables: [deployment](/tablas-decision/decision-despliegue) · [by constraint](/tablas-decision/decision-por-restriccion). Labs: [hands-on](/practica/labs-hands-on). Practice: [question bank](/practica/banco-preguntas).
