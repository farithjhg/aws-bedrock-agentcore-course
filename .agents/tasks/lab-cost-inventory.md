# Lab cost inventory: AgentCore course "Nova Assist" (chapters 0–16)

Scope: read-only review of `AgentCore_Formacion_Oct2026/AgentCore_Formacion_Oct2026/` (17 notebooks, `labs/*.py`, `labs/README.md`, `GUIA_FORMADOR.md`, design doc `Analisis_…_v5.md`). No notebook was run and no AWS call was made. Dataset sizes were computed by running `dataset_tiendanova.generar()` and `rag_nova.trocear()` locally (pure Python, no AWS).

Legend: **[S]** = stated in the course material · **[I]** = my inference (token counts, call counts, billing behaviour).

---

## 1. Summary answer

- **Region [S]:** `eu-west-1` (Ireland), fixed in `00_…ipynb` A0/B2 and `lab_utils.DEFAULT_REGION`. Budgets API is called in `us-east-1` (global service).
- **Main model [S]:** **not fixed**. Each student picks one `eu.anthropic.*` system inference profile in ch0 B4 (`MODEL_ID = "eu.anthropic.<MODELO>"`). The design doc only says "Claude vía inference profile `eu.`" (§13.2, line 738). The **same `MODEL_ID` is used for everything model-driven in the notebooks**: the agent, the local LLM judges (ch12 §0, ch14 `evaluar_informe`), the multi-agent team (ch14) and the Code Interpreter "calculadora" (ch11). So total inference cost depends on which Claude tier the student picks (Haiku vs Sonnet vs Opus class).
- **Embedding model [S]:** `amazon.titan-embed-text-v2:0`, 1024 dims, normalised (`rag_nova.py` `MODELO_EMBEDDING`, `DIMENSION`). It is called as an on-demand foundation model in eu-west-1, not through a profile.
- **Memory extraction model / built-in evaluator models [I]:** the course uses the AgentCore built-in strategies (`SEMANTIC,SUMMARIZATION,USER_PREFERENCE`) and built-in evaluators (`Builtin.GoalSuccessRate`, `Builtin.Helpfulness`). No model ID is configured, so AWS manages these models and bills them through AgentCore Memory / Evaluations pricing, not as Bedrock tokens on the student's model.
- **Price constants [S]:** **none are hard-coded.** Ch0 B6 sets `PRECIO_ENTRADA_MTOK = None`, `PRECIO_SALIDA_MTOK = None`. These are **USD per million tokens** (not per 1K): see `lab_utils.precios()` and `_coste()` (`entrada / 1e6 * pe`). The taxímetro shows only token counts until the student fills these in.
- **Budget [S]:** `PRESUPUESTO_USD = 50`, a monthly COST budget called `nova-assist-lab`, with alerts at 50 % and 80 % ACTUAL and 100 % FORECASTED (ch0 cells A0/A3). This is the only USD amount in the material that resembles a cost envelope. **No total cost estimate for the course exists anywhere in the material.**
- **Duration [S]:** **3-day course.** The per-chapter durations add up to about **1,030 min (≈17.2 h)**, plus 5 min of presentation per pair and a 10 min close. The agenda adds up to 18 h (trainer guide) or 18.5 h (design doc).
- **Cost shape [I]:** almost all of the variable cost is **Bedrock inference on the chosen Claude model**. My estimate is ~1–2.5 M input tokens and ~0.1–0.2 M output tokens per student for the whole course, re-runs included. Chapters 12, 14, 6, 16 and (optional) 13 drive most of it. Next come AgentCore Runtime/Memory/Gateway/Evaluations usage, Code Interpreter sessions and CloudWatch telemetry with 100 % span indexing. Idle-between-days costs are small: storage of S3/S3 Tables/S3 Vectors/Memory records/logs, a Cognito M2M app client, and possibly one Secrets Manager secret.

---

## 2. Per-chapter inventory

Model calls are Bedrock Converse/ConverseStream requests on `MODEL_ID`. One user "turn" with a tool usually takes 2–3 model calls (tool_use, then the final answer). Token figures are **[I]** rough estimates: Spanish at about 3.5 chars/token, using the prompt, tool-schema and data sizes I measured (§3).

| Ch | Duration [S] | AWS resources created / used | Agent turns & model calls (from code) [S] → est. tokens [I] |
|---|---|---|---|
| 0 | A 25 min (+10 wait) · B 20 · C 20 = 75 min | **Part A (admin, once per account):** AWS Budget ($50/mo, 3 e-mail alerts); CloudWatch **Transaction Search** (logs resource policy `NovaLabTransactionSearch`, X-Ray destination → CloudWatch Logs, **indexing rule 100 %**); **CDK bootstrap** (`CDKToolkit` stack: S3 staging bucket, ECR repo, IAM roles, SSM param), tagged; optional IAM role `NovaLabParticipant` (shared-account model only); **Glue federated catalog `s3tablescatalog`**. **Part B:** list inference profiles. **Part C:** S3 bucket `nova-lab-{acct}-{region}` (7 policy .md files + `athena/` results); **S3 Tables** table bucket `nova-datos-{acct}`, namespace `tiendanova`, 8 Iceberg tables; **Athena** 2 queries | 1 Converse smoke test ("Responde solo: OK") → ~20 in / ~5 out |
| 1 | 40 | Bedrock only (local Strands agent) | agent without rules ×1 (the notebook says "run several times", so assume 1–3), agent with rules ×1, **10 concurrent Converse calls** with `maxTokens=5`, 1 degradation call → ~15 calls, ~3 k in / ~1–2 k out |
| 2 | 45 | Bedrock only (5 local `@tool`s on the JSON dataset) | 5 turns in **one growing conversation** (`preguntar` ×5) with tool loops, ~10–12 calls → ~25–40 k in / ~2–3 k out |
| 3 | 60 | `agentcore create` (CodeZip, Strands) → **AgentCore Runtime `NovaAgent`** via CDK/CloudFormation (`deploy --dry-run` + `deploy`); CloudWatch logs (`agentcore logs`) | 2 calls with a global agent, 1 `probar_local`, 3 `invocar` to the Runtime → ~10 calls, ~10–15 k in |
| 4 | 45 | **AgentCore Memory `NovaMemory`** with **3 long-term strategies from day 1** (SEMANTIC, SUMMARIZATION, USER_PREFERENCE), 2 deploys | 2 replica calls, 3 `probar_local` (these also write to Memory), 2 `invocar` → ~10 calls, ~10–15 k in; short-term events start accruing, LTM extraction runs on every event from here on |
| 5 | 45 | Memory LTM retrieval config (2 namespaces: `/preferences/{actorId}/` top_k 5, `/facts/{actorId}/` top_k 10); 1 deploy; `list_memory_records` polled ≤10× at 30 s | 5 `invocar` → ~8–10 calls, ~10–20 k in; + LTM extraction and 2 retrievals per turn |
| 6 | 45 | 1 deploy (sliding window 20 msgs, larger structured system prompt) | **8-turn conversation run twice** (before and after the window) = **16 Runtime turns**, ~30 calls; history grows each turn → ~100–150 k in / ~5–8 k out |
| 7 | 85 | **Lambda `nova-pedidos`** (py3.13, 30 s timeout, default memory) + IAM role; **Athena** queries from the Lambda; **Cognito user pool `nova-m2m`** + domain + resource server + **M2M app client with secret** (client_credentials); **AgentCore Gateway `NovaGateway`** (CUSTOM_JWT) + target `PedidosTarget` (5 tools); **AgentCore Identity** credential provider (OAuth M2M, Token Vault); 1–2 deploys | 1 local MCP (stdio) turn, 2 `probar_local`, 2 `invocar` → ~10 calls, ~15–25 k in; 6 direct Lambda test invokes (~8 Athena queries); every later tool call = Lambda + 1–2 Athena queries |
| 8 | 100 | **S3 Tables** table `chunks` (+ appends); **S3 Vectors** bucket `nova-vectores-{acct}` + index `politicas` (1024-d, cosine); **Lambda `nova-politicas`** + IAM role; Gateway target `PoliticasTarget`; 1 deploy; Athena queries | 1 local RAG answer, 3 + 1 + 1 `invocar` → ~12 calls, ~25–40 k in. **Titan embeddings: ~100–110 calls** (27 local + 27 index + ~25 direct queries + 17 recall@k + ~5 poisoned chunks + Lambda calls), ~3–5 k embedding tokens total; ~50 S3 Vectors queries; ~33 vectors written, 6 deleted |
| 9 | 60 | **Cognito user pool `nova-clientes`** + app client + 2 users (C-001, C-002); Runtime **JWT inbound authorizer**; 1 deploy | 2 `probar_local` (1 short-circuits without a model call), 1 rejected + 2 OK `invocar` → ~6 calls, ~10–15 k in |
| 10 | 60 | **AgentCore Policy** engine `NovaPolicyEngine` (ENFORCE) + 2 Cedar policies; **Bedrock Guardrail** `nova-assist-guardrail` (PROMPT_ATTACK HIGH input, PII card BLOCK / IBAN ANONYMIZE) + 1 version; manual Guardrails↔Policy integration; 1 deploy | 6 `invocar` → ~12–15 calls, ~30–45 k in; Policy authorizations per tool call; Guardrail text-unit evaluations if integrated |
| 11 | 40 | **AgentCore Code Interpreter** (built-in `AgentCoreCodeInterpreter` sessions) from the notebook and from the Runtime; 1 deploy | 1 local "calculadora" turn (several calls with code execution), 1 `invocar` → ~6–8 calls, ~15–25 k in (the code_interpreter tool spec is large); ~2–3 CI sessions |
| 12 | 60 | **Observability** (spans → `aws/spans`, `agentcore traces list`, `logs`); **AgentCore Evaluations**: 3 sessions × 2 built-in evaluators on demand; **online evaluation `nova_online_eval`** (GoalSuccessRate + Helpfulness, **no sampling % set in the cell**) that stays on until ch15; S3 Tables table `eval_retrieval`; Athena; 1 deploy | 3 eval turns + 3 judge calls, then **25 golden/adversarial cases** (`eval_casos` for C-001/C-002) via `invocar` → ~31 turns + 3 judges, ~60–80 calls, **~200–300 k in / ~10–15 k out**; 17 embeddings + S3 Vectors queries; ~3 Athena queries |
| 13 | 60 | **Configuration bundles** + **A/B test** in the Gateway (Runtime as `http-runtime` target) reusing online eval. The commands are **mostly commented out / `--help` only**; the guide says it can be run as a trainer demo | Baseline 0 turns. If run for real, the guide suggests "repite el conjunto de prueba varias veces" → e.g. 2×25 = 50 turns, ~300–400 k in, plus online evals on that traffic |
| 14 | 90 | Gateway **Web Search connector target** `WebSearch` (CLI or console); extra Cedar policy `InvestigacionPermitida`; 1 deploy; Athena (3 predefined analyst tools); Code Interpreter; S3 Tables table `informes` | **Graph** (investigator → analyst → editor) once + **Swarm** (`max_handoffs=8`, `max_iterations=12`, 900 s timeout) once + 2 rubric judges → ~20–60 calls, web results inflate context → **~150–400 k in / ~15–30 k out**; ~5–15 web searches; ~6–12 Athena queries; 1–2 CI sessions. These run in the notebook, not in the Runtime |
| 15 | 30 | **Cleanup** (gated by `CONFIRMAR_LIMPIEZA = True`): `agentcore remove all && agentcore deploy`; boto3 deletion of non-CLI resources (see §4) | 0 model calls |
| 16 | 90 + 5/pair | Student-designed "two pieces" on top of everything; appends 3 rows to `eval_casos` | ≥3 eval `invocar` + a 3-turn conversation before **and** after the changes (6) = ≥9 turns, plus free experimentation (assume 10–30) → ~50–150 k in. Online eval still active |

Approximate deploy count [I]: ~14–16 `agentcore deploy` runs (CloudFormation via CDK) in ch3–ch15.

---

## 3. Sizes that drive token counts (measured locally from the code)

| Item | Value | Source |
|---|---|---|
| `clientes` / `productos` / `pedidos` / `lineas_pedido` / `envios_eventos` / `devoluciones` / `documentos` / `eval_casos` rows | 200 / 22 / 1,205 / 1,638 / 5,795 / 107 / 7 / 26 | `dataset_tiendanova.generar()` defaults (n_clientes=200, n_pedidos=1200 + 5 anchors) |
| Full dataset JSON | ~1.6 MB (Iceberg/Parquet smaller) | `datos/tiendanova.json` |
| Policy documents for RAG | 7 docs, ~4.7 k chars | `DOCUMENTOS` |
| RAG chunks | **27** (avg ~206 chars, ~5.6 k chars total, MAX_CHARS 900). The trainer guide also says "unos 27 fragmentos" | `rag_nova.trocear` |
| Eval cases run in ch12 | 25 (C-001/C-002), 17 with an expected document (recall@k) | `_eval_casos` |
| One `pedido` tool result | ~460 chars (~150–200 tokens) | measured |
| System prompt | ch1–5: ~300 chars (~90 tok). ch6+: ~1 k chars (~300 tok) + session context | `prompts.py` cells |
| Tool schemas | 5 order tools (~800 tok), + `buscar_politicas` (ch8), + `code_interpreter` (ch11, large), + Web Search tools (ch14) | `tools.json`, `politicas_tools.json` |
| Sliding window | 20 messages (ch6+) | `SlidingWindowConversationManager(window_size=20)` |
| LTM retrieval | 2 namespaces, top_k 5 and 10 | ch5 `LTM_NAMESPACES` |

**Course-wide inference total [I]:** about 120–200 agent turns. Summing the per-chapter estimates gives ~0.9–1.3 M input and ~60–100 k output tokens for a clean run. Allowing 1.5–2× for re-runs and debugging, a realistic envelope is **~1–2.5 M input / ~0.1–0.2 M output tokens** on `MODEL_ID`, plus ~5 k Titan embedding tokens. The course never enables prompt caching (ch6 only prepares a stable prefix).

---

## 4. What keeps accruing between chapters/days, and what ch15 removes

Resources live from creation until ch15. The trainer guide says not to clean up before ch16 if ch16 runs on another day (`GUIA_FORMADOR.md` ch15 tip). In practice that means **until the end of day 3**.

| Resource | Created | Idle / between-day cost driver [I] | Removed by ch15? [S] |
|---|---|---|---|
| AgentCore Runtime `NovaAgent` | 3 | Billed per active session (vCPU/memory per second). Sessions stay open until their idle timeout, so memory-time may accrue for minutes after each session [I, verify on the pricing page] | ✅ `agentcore remove all` + deploy |
| AgentCore Memory `NovaMemory` (STM events + LTM records, 3 strategies) | 4 | Events created, LTM records stored per month, retrievals | ✅ CLI |
| Gateway `NovaGateway` + Pedidos/Politicas/(WebSearch) targets | 7/8/14 | Per MCP operation; no idle cost | ✅ CLI. ⚠️ A WebSearch target added through the **console** is not in `agentcore.json` [I] |
| Identity credential provider (OAuth M2M) | 7 | The client secret probably sits in a Secrets Manager secret (~monthly per secret) [I] | ✅ CLI (should go with the provider) [I] |
| Policy engine + 3 Cedar policies | 10/14 | Per authorization request | ✅ CLI |
| Online eval `nova_online_eval` | 12 | **Keeps evaluating every Runtime session** (ch13/16 traffic) with LLM judges until removed; sampling not set | ✅ CLI |
| Config bundles / A/B | 13 | Per use | ✅ CLI |
| Lambdas `nova-pedidos`, `nova-politicas` + roles | 7/8 | None idle | ✅ boto3 cell 2.2 |
| S3 Vectors bucket + index | 8 | Tiny storage (~33 × 4 KB vectors) | ✅ |
| S3 Tables bucket, namespace, ~11 tables (8 + chunks, eval_retrieval, informes) | 0/8/12/14 | Small storage + per-table maintenance | ✅ (lists and deletes tables) |
| Lab S3 bucket (docs + Athena results) | 0 | Tiny storage | ✅ emptied and deleted |
| Cognito `nova-m2m` (domain, M2M client) and `nova-clientes` (2 users) | 7/9 | **M2M app client / token requests may carry a charge**; 2 MAUs fall in the free tier [I, verify Cognito M2M pricing] | ✅ |
| Bedrock Guardrail | 10 | None idle | ✅ |
| AWS Budget `nova-assist-lab` | 0 | Notification-only budgets are normally free [I] | ⚠️ Only in admin cell 2.3 (`CONFIRMAR_LIMPIEZA_CUENTA = False` by default) |
| IAM role `NovaLabParticipant` | 0 (shared model only) | none | ⚠️ admin cell 2.3 only |
| Glue catalog `s3tablescatalog` | 0 | none | ❌ by default (`BORRAR_CATALOGO_S3TABLES = False`) |
| **CDKToolkit stack** (S3 staging bucket with CodeZip assets from every deploy, ECR repo) | 0 / first deploy | Storage of ~15 deploy zips [I] | ❌ kept explicitly ("CDKToolkit y Transaction Search se conservan") |
| **Transaction Search** (X-Ray → CW Logs, **100 % indexing**, logs resource policy) | 0 | Span ingestion + indexing on every traced request | ❌ kept explicitly |
| **CloudWatch log groups** (`/aws/bedrock-agentcore/runtimes/...`, `/aws/lambda/nova-*`, `aws/spans`, `/aws/application-signals/data`) | 3+ | Ingestion during the course; storage afterwards (default retention = never expire) | ❌ not addressed |
| Local `lab_state.json` | 0 | — | archived to `.json.bak` |

Statement in the material [S]: ch15 §2.3 says Transaction Search and the CDK bootstrap "pueden quedarse: no generan coste relevante sin uso" (`15_produccion_y_limpieza.ipynb`, markdown cell before the account-cleanup code).

---

## 5. Duration

| Source | Breakdown | Total |
|---|---|---|
| Per-chapter durations, `GUIA_FORMADOR.md` lines 130–682 (same figures in design doc §15.4, lines 1135–1328) | 75 + 40 + 45 + 60 + 45 + 45 + 45 + 85 + 100 + 60 + 60 + 40 + 60 + 60 + 90 + 30 + 90 min | **1,030 min ≈ 17.2 h** (+5 min/pair presentations, +10 min close) |
| Agenda, `GUIA_FORMADOR.md` lines 77–86 | D1 4 h + 2.5 h · D2 4.5 h + 2.5 h · D3 2 h + 2.5 h | **18 h over 3 days** |
| Agenda, design doc §15.2 (~line 1098) | same, except D2 morning = **5 h** | 18.5 h over 3 days |

The course is designed for **3 days** (`### Agenda (3 días)`), and Part A of ch0 is meant to run the day before. Inconsistency: chapters 7–10 add up to 305 min (5.1 h). The guide says 4.5 h; the design doc's 5 h is the closer figure.

---

## 6. Explicit cost statements in the material (quoted)

1. `labs/00_configuracion_cuenta_aws.ipynb`, cell A0: `PRESUPUESTO_USD = 50  # presupuesto mensual de la cuenta para la formación`. Cell A3 then creates a MONTHLY COST budget with alerts at ACTUAL 50 %, ACTUAL 80 % and FORECASTED 100 %.
2. Same notebook, cell A4: `# Volumen de laboratorio: indexamos el 100 % de los spans. En producción, ajusta este porcentaje (coste).`
3. Same notebook, cell B6: `PRECIO_ENTRADA_MTOK = None   # ← USD por millón de tokens de entrada`. No default price.
4. Design doc line 179 (Code Interpreter): quotes **0.0895 USD per vCPU-hour and 0.00945 USD per GB-hour** from "el documento original", with a caveat to check the current pricing page.
5. Design doc line 450 and `12_observabilidad_evaluacion.ipynb` §4: LLM evaluators on 100 % of traffic "puede duplicar el consumo de inferencia… Muestrea."
6. Design doc line 752 and `labs/README.md` line 134: the chapters consume paid resources (inference, Runtime, Memory, Gateway, Evaluations, S3 Vectors, Athena). Use a sandbox account, set the ch0 budget and run ch15 when done.
7. Design doc §8.1 (lines 553–564): qualitative list of cost sources. It says inference is "normalmente la partida más grande" and gives no figures ("consultar siempre la página oficial de precios").
8. `15_produccion_y_limpieza.ipynb` §2.3: Transaction Search and CDK bootstrap "no generan coste relevante sin uso".
9. `GUIA_FORMADOR.md` line 674: check *Cost Explorer* the day after cleanup.

No file contains a per-student or per-course USD estimate.

---

## 7. Conclusions and recommendations (nothing implemented)

**For the estimate**
- Price **Bedrock inference on the chosen `eu.anthropic.*` profile** as the dominant line, using the §3 token envelope (~1–2.5 M in / 0.1–0.2 M out). Show at least two scenarios: a Haiku-class and a Sonnet-class choice. The course leaves the choice to the student, and that choice changes the total several-fold.
- Add AgentCore line items using the counts above: Runtime (~100–150 sessions of a few seconds to a few minutes of active time), Memory (~300–700 STM events, LTM extraction, ~150–250 retrievals), Gateway (a few hundred MCP calls), Policy (a few hundred authorizations), Evaluations (6 on-demand plus online evals on every Runtime session from ch12 onward), Code Interpreter (~4–6 sessions), Web Search (~5–15 queries).
- Small or negligible lines [I]: Titan embeddings (~5 k tokens), Athena (~100–300 queries at the 10 MB minimum), S3 / S3 Tables / S3 Vectors storage (MB scale), Lambda, Guardrails (a few dozen text units), CloudWatch ingestion (likely under 1 GB). Verify Cognito M2M and Secrets Manager line items.
- Compare the result to the course's own **$50/month budget** as an upper reference.

**Gaps/risks worth fixing in the course**
- Set a default `MODEL_ID` recommendation and default `PRECIO_*_MTOK` values in ch0 B6, so the taxímetro shows USD from chapter 1.
- `agentcore add online-eval` in ch12 sets no sampling percentage, which contradicts the course's own "Muestrea" warning. Pass an explicit low sampling rate.
- Ch15 leaves Transaction Search at **100 % indexing**, CloudWatch log groups with no retention, and the CDK staging bucket with all deploy zips. Add steps to set the indexing back to the default, set log retention or delete the `nova`/AgentCore log groups, and optionally empty the CDK assets bucket.
- A Web Search target created in the console (ch14) may not be removed by `agentcore remove all`. Add a check or a boto3 delete.
- Ch16's footer ("ejecuta el capítulo 15 (limpieza) si no lo has hecho") conflicts with the numbering, since ch15 comes before ch16. State clearly that cleanup runs after ch16.
- The day-2 morning agenda (4.5 h) is shorter than its chapters (5.1 h). Align it with the design doc (5 h).
