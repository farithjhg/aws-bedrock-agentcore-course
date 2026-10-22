---
id: vision-examen
sidebar_position: 1
title: Exam Format & Strategy
---

The domain chapters teach you the AWS content. This page teaches the other half of a Professional-tier pass: **how to read a dense scenario under time pressure and eliminate the near-correct distractors** that are engineered to look right. That skill is learnable, so this page actually walks you through it rather than just asserting it.

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

## Finding the governing qualifier (the one skill this page teaches)

A Pro-tier stem is usually a paragraph of realistic-but-mostly-irrelevant context wrapped around **one decisive word**. Several answers will be real AWS services that genuinely do something; only one of them serves the word the question actually turns on. Train the following four-step read until it is automatic.

1. **Read the final sentence (the ask) first, then the scenario.** The last line is almost always "which approach / service is MOST [something]?" Know what you are hunting for before the story can distract you.
2. **Underline the one governing qualifier.** Most stems bury a single decisive phrase: *lowest cost*, *fastest first token*, *least operational overhead*, *must stay private / data residency*, *detect hallucination*, *largest scale*, *compliance / audit*. If you can only keep one phrase from the whole question, keep this one.
3. **Say the qualifier out loud as a constraint, then map it to a pattern** with the [master decision table](/tablas-decision/decision-por-restriccion). "Must stay private" means "keep traffic off the public internet" means PrivateLink + IAM conditions — do that translation before you look at the options.
4. **Eliminate every option that fights the qualifier, even valid services.** A real AWS service that ignores the stem's constraint is still wrong — "true but irrelevant" is the single most common Pro-tier distractor.

### Worked example (how the read looks in practice)

Read this the way you would on exam day:

> *"Northwind runs a real-time customer-chat assistant on Bedrock. During evening peaks the bill spikes. Leadership wants to reduce spend. Which approach is MOST cost-effective?"* One option offers the Batch Inference API.

- Step 1 — the ask: *most cost-effective.*
- Step 2 — governing qualifier: **"reduce spend"**, but note the context word **"real-time."**
- Step 3 — map it: cost → caching / cascading / routing / Batch.
- Step 4 — eliminate: Batch Inference is a genuine cost lever, so it is tempting — but it is **non-real-time**, and the scenario is a real-time chat. It fights a hard context constraint, so it is out. The answer is a real-time-compatible cost lever (prompt caching, cascading/routing), not Batch.

That is the entire game: translate the qualifier, then let it kill options.

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

## Time budget — the ~2.4 min/question discipline

180 minutes over 75 questions is **~2.4 minutes each**, and that average is the plan, not a target to hit every time.

- **Three-pass rhythm.** First pass: answer everything you know in under ~2 minutes; if a question is still open at ~3 minutes, pick your best current guess, flag it, and move on. The flagged guess protects you if you run out of time. Second pass: return to flagged items with the clock pressure gone. Third pass: confirm **zero blanks** before submitting.
- **Never leave a blank.** A guess strictly beats a blank — there is no guessing penalty, and a blank is scored wrong anyway. Confirm every item has an answer before submit.
- **Hold back ~10–15 minutes** at the end for the flagged-item pass; do not let early questions eat it.
- **Spend effort where weight and weakness overlap.** Compensatory scoring means the total is all that matters, so a 2% gain on D1 (31%) is worth more than perfecting an 11% domain you already know.

## Multiple-response is all-or-nothing — the tactic that cuts errors

"Select TWO" (or more) gives **no partial credit**: getting one of two right scores exactly the same as getting none. These are high-variance, so slow down and use a deliberate technique instead of a gut pick.

1. **Judge each option independently as a standalone true/false**, as if each were its own one-answer question. Ignore the other options while you rate one.
2. **An option can be individually true yet wrong** because it ignores the stem's constraint. Re-apply the governing qualifier to each candidate before you keep it.
3. **If the stem says "select TWO," you must end with exactly two true-and-relevant options.** If three survive, one of them is true-but-irrelevant — re-read the qualifier and drop it. If only one survives, you were too strict on another; re-check.
4. **Watch for paired symptoms.** A stem that describes two problems ("slow to start" and "invents facts") usually wants two independent fixes, one per symptom — not two fixes for the same symptom.

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
2. Walk the four-step scenario read on a stem of your choice — what is the governing qualifier and how does it eliminate an option?
3. On a "select TWO" with no partial credit, what technique cuts your error rate, and what do you do if three options survive?
4. What is the three-pass time rhythm, and what is the flag-and-move rule at ~3 minutes?
5. Give three constraint keywords and the first-instinct pattern each points to.
6. Why is "AWS Batch" a trap, and what is it confused with?
7. What does compensatory scoring change about where you spend study hours?

The rest of the mechanics (delivery, languages, validity, retake policy) are on the AWS exam guide — confirm there via [resources](/recursos).

Next: [Domain 1](/blueprint/dominio-1-fundacion-datos). Practice: [question bank](/practica/banco-preguntas).
