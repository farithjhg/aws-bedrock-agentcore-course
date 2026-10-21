# Exam Format & Test-Taking Strategy

Before you study any content, learn how the exam is scored and how to read it. A Professional-tier exam is often less about knowing an obscure fact and more about **reading a scenario correctly and picking the best-fit answer under time pressure**. This file teaches that discipline.

Back to [course home](../README.md).

## Format & scoring

| Attribute | Value |
|---|---|
| Exam code / level | AIP-C01 / Professional |
| Questions | 75 total — 65 scored + 10 unscored pretest (indistinguishable) |
| Time | 180 minutes (~2.4 min/question) |
| Cost | $300 USD *(confirm at registration)* |
| Pass score | 750 on a 100–1,000 scaled range |
| Scoring | Compensatory — your total counts; no per-domain minimum |
| Question types | Multiple choice (1 correct of 4); multiple response (2+ correct of 5+) |
| Partial credit | **None** on multiple response — all correct options required |
| Blank answers | Scored as incorrect; **no guessing penalty** |
| Delivery | Pearson VUE test center or online proctored |
| Languages | English, Japanese, Korean, Simplified Chinese |
| Validity | 3 years |

**Takeaway:** 10 of your 75 questions do not count, but you cannot tell which. Treat every question as if it counts.

## The all-or-nothing multiple-response rule

Multiple-response questions ask you to "select TWO" (or more) from 5+ options and give **no partial credit** — you must get the full set exactly right. The reliable technique:

- **Treat each option as an independent true/false statement.** Decide for every option whether it is correct *on its own*, ignoring the others.
- A "select TWO" with no partial credit means a 50%-right answer scores the same as a 0%-right answer. These items are high-variance, so slow down on them.
- Watch for options that are individually true but **do not satisfy the scenario's constraint** — true-but-irrelevant is still wrong.

## The clock

75 questions in 180 minutes is about **2.4 minutes per question**. That is enough time to read carefully but not enough to agonize.

- **Flag and move.** If a question costs more than ~3 minutes, pick your best guess, flag it, and come back. Never let one question eat the time of three others.
- **Never leave a blank.** Unanswered = wrong, and there is no guessing penalty, so a guess strictly dominates a blank. Before you submit, confirm zero questions are unanswered.
- Budget a final ~10–15 minutes to revisit flagged questions.

## Compensatory scoring

Compensatory scoring means there is **no minimum per domain** — a weak domain can be offset by strong ones as long as your total clears 750. Consequences for how you study:

- Spend effort where **weight and your weakness overlap**. A 2% gain on a 31% domain is worth far more than mastering an 11% domain you already know.
- Do not panic-cram a low-weight domain at the expense of D1/D2.

## Scenario-reading discipline

Most questions are a short scenario followed by "What should the developer do?" The winning habit:

1. **Read the question stem first**, then the scenario, so you know what you are hunting for.
2. **Find the one decisive constraint keyword.** Most scenarios bury a single governing word that dictates the answer: *lowest cost*, *minimal latency / fastest response*, *least operational overhead*, *must stay private / data residency*, *detect hallucination*, *largest scale*, *compliance / audit*.
3. **Map the keyword to a pattern** using the master table below, then eliminate options that fight the constraint.
4. Beware **distractors that are real AWS services doing a real job** — they are wrong only because they do not serve *this* constraint.

### Constraint keyword → preferred pattern (teaser)

This is a preview. The full lookup you should memorize is [the master decision table](../tablas-decision/decision-por-restriccion.md).

| Constraint keyword in the stem | Preferred pattern (first instinct) |
|---|---|
| Lowest cost / reduce spend | Prompt caching, Batch Inference, model cascading, Intelligent Prompt Routing |
| Lowest latency / fastest first token | Response streaming, Provisioned Throughput, WebSocket API |
| Least operational overhead / minimal effort | Managed services (Bedrock Knowledge Bases, Bedrock Agents) |
| Must stay private / data residency / strict security | PrivateLink VPC endpoints + IAM conditions + Guardrails |
| Detect / prevent hallucination | Contextual Grounding check + RAGAS Faithfulness |
| Ultra-large scale | S3 Vectors, OpenSearch Serverless |
| Compliance / audit trail | Model Invocation Logging + CloudTrail + Audit Manager |

## Out-of-scope topics

These appear as tempting distractors but are **outside AIP-C01's scope**. If an option is one of these, it is almost certainly wrong for a GenAI-developer scenario.

| Out-of-scope topic | Why it is a distractor |
|---|---|
| Training a foundation model from scratch | The exam is about *using/integrating* FMs, not building them |
| Advanced classical ML (algorithm design, tuning) | Not a GenAI-developer task |
| Data / feature engineering pipelines | Beyond GenAI integration scope |
| Writing GPU kernels / low-level compute | Infrastructure concern, not GenAI dev |
| AWS Batch as generic compute | Non-GenAI infra; do not confuse with the Bedrock **Batch Inference API** |
| Amazon Lightsail | Non-GenAI infra distractor |
| Transit Gateway / Direct Connect | Non-GenAI networking distractors |

**Trap alert:** "AWS Batch" (a batch *compute* service) is not the same as the **Batch Inference API** in Bedrock (async bulk model inference at a discount). The exam will put both near each other.

## Exam traps & key discriminators

- **Blank = wrong.** Guessing is free; never submit an unanswered question.
- **"Select TWO" = all or nothing.** Evaluate each option independently; no partial credit.
- **True-but-irrelevant options** are the most common distractor — a valid service that ignores the stem's constraint.
- **Compensatory scoring** means weight your prep by domain weight, not by what feels fun.
- **AWS Batch ≠ Bedrock Batch Inference API.** One is out of scope; the other is a cost lever.
- The **constraint keyword** decides the answer. If you can name it, you can usually eliminate three options.

## Self-check (5–8 questions)

1. How many of the 75 questions are scored, and what is the pass score on what scale?
2. Why should you never leave a question blank?
3. On a "select TWO" item with no partial credit, what technique reduces your error rate?
4. What does compensatory scoring change about how you allocate study hours?
5. Give three constraint keywords and the first-instinct pattern each one points to.
6. Why is "AWS Batch" a trap answer on this exam?
7. Roughly how many minutes per question do you have, and what is the flag-and-move rule?

Next: [Domain 1 — Foundation, Data & Compliance](./dominio-1-fundacion-datos.md). Practice: [question bank](../practica/banco-preguntas.md).
