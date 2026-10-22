---
id: vision-examen
sidebar_position: 1
title: Exam Format & Strategy
---

You know the AWS content from the official prep. What that prep does not drill is **how to read a Pro-tier scenario under time pressure and eliminate near-correct distractors**. That is this file.

Back to [course home](/).

## Format & scoring (once — this file owns the mechanics table)

| Attribute | Value |
|---|---|
| Questions | 75 total — 65 scored + 10 unscored pretest (indistinguishable) |
| Time | 180 minutes (~2.4 min/question) |
| Cost | `$300 USD` *(confirm at registration)* |
| Pass | 750 on a 100–1,000 scaled range |
| Scoring | Compensatory — total counts, no per-domain minimum |
| Question types | Multiple choice (1 of 4); multiple response (2+ of 5+) |
| Partial credit | **None** on multiple response — the full set must be exactly right |
| Blank answers | Scored wrong; no guessing penalty — so never leave one blank |

Note: 10 of 75 do not count and you cannot tell which — treat every item as scored.

## Scenario-reading discipline (the point of this page)

1. **Read the question stem first, then the scenario.** Know what you are hunting for before you read the story.
2. **Find the one governing qualifier.** Most stems bury a single decisive word: *lowest cost*, *fastest first token*, *least operational overhead*, *must stay private / data residency*, *detect hallucination*, *largest scale*, *compliance / audit*.
3. **Map the keyword to a pattern** via the [master decision table](/tablas-decision/decision-por-restriccion), then eliminate options that fight the constraint.
4. **A real AWS service that ignores this stem's constraint is still wrong.** True-but-irrelevant is the most common distractor.

### Constraint keyword teaser (full table is the master)

| Qualifier in the stem | First instinct |
|---|---|
| Lowest cost / reduce spend | Prompt caching, Batch Inference, cascading, Intelligent Prompt Routing |
| Fastest first token / lowest latency | Response streaming, Provisioned Throughput |
| Least operational overhead | Managed (Bedrock Knowledge Bases, Bedrock Agents) |
| Must stay private / data residency | PrivateLink VPC endpoints + IAM conditions |
| Detect / prevent hallucination | Contextual Grounding + RAGAS Faithfulness |
| Compliance / audit trail | Model Invocation Logging + CloudTrail + Audit Manager |

Memorize the full lookup: [master decision table](/tablas-decision/decision-por-restriccion).

## Time budget

- **~2.4 min/question.** Over ~3 minutes → pick a best guess, flag, move on.
- **Never blank.** A guess strictly beats a blank; confirm zero unanswered before submit.
- Keep a final **~10–15 min** to revisit flagged items.
- Compensatory scoring → spend effort where **weight and your weakness overlap**. A 2% gain on D1 (31%) beats mastering an 11% domain you already know.

## Multiple-response = all or nothing

- Judge **each option independently** as a standalone true/false.
- 50%-right scores the same as 0%-right. Slow down on these; they are high-variance.
- An option can be individually true yet wrong because it ignores the stem's constraint.

## Out-of-scope distractors (near-neighbor traps)

These look plausible but sit outside AIP-C01's GenAI-developer scope — if an option is one of these, it is almost certainly wrong.

| Distractor | Why it is wrong here |
|---|---|
| **AWS Batch** (generic compute) | Out of scope; do not confuse with the Bedrock **Batch Inference API** (async discounted model inference). The exam places both near each other on purpose. |
| Training a foundation model from scratch | Exam is about *using/integrating* FMs, not building them |
| Amazon Lightsail | Non-GenAI infra distractor |
| Transit Gateway / Direct Connect | Non-GenAI networking distractors |

## Self-check

1. Why treat every one of the 75 as scored?
2. On a "select TWO" with no partial credit, what technique cuts your error rate?
3. What does compensatory scoring change about where you spend study hours?
4. Give three constraint keywords and the first-instinct pattern each points to.
5. Why is "AWS Batch" a trap, and what is it confused with?
6. Minutes per question, and the flag-and-move rule?

The rest of the mechanics (delivery, languages, validity, retake policy) are on the AWS exam guide — confirm there via [resources](/recursos).

Next: [Domain 1](/blueprint/dominio-1-fundacion-datos). Practice: [question bank](/practica/banco-preguntas).
