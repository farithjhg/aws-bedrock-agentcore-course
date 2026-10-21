# AIP-C01 Exam-Prep Course

A self-contained, English-language study course built for one purpose: help you pass the **AWS Certified Generative AI Developer – Professional (AIP-C01)** exam on a tight timeline. It is ruthlessly optimized for the exam, not for deep mastery.

## Who this is for

You if you:

- Have **basic** GenAI and AWS knowledge (you know what a prompt and an S3 bucket are, but not every Bedrock feature).
- Can spend about **5 hours per week**.
- Want a week-by-week plan that ends at a real exam date, not an open-ended syllabus.

Every AWS service is defined in one clause the first time it appears in a file, so you are never assumed to already know it.

## Honest framing: this is a stretch goal

Be honest with yourself before you start. AIP-C01 is a **Professional-tier** exam. AWS positions its ideal candidate as someone with 2+ years of production AWS experience plus about a year of hands-on generative AI work. You are starting from a basic base and budgeting roughly **40 hours over 8 weeks** (5h/week, Oct 21 → Dec 15, 2026).

That gap is real. This course closes it by **optimizing for a pass, not for completeness**: we drill the highest-weight domains, memorize decision patterns, and rehearse scenario-reading rather than trying to learn everything AWS GenAI can do. Forty hours is enough to give you a genuine shot **if** you follow the plan and hit the practice targets. It is not enough to make you an expert.

There is a built-in honesty check: the **readiness gate** around Dec 8 (see [practica/simulacro-final.md](practica/simulacro-final.md)). If your mixed full-length practice scores are not trending toward a pass by then, the right move may be to reschedule rather than burn the $300 attempt. This course will tell you that plainly.

## What the exam is

AIP-C01 is a 75-question, 180-minute, $300 proctored exam. 65 questions are scored and 10 are unscored pretest items you cannot identify. You pass at **750 on a 100–1,000 scaled score** with **compensatory scoring** — there is no per-domain minimum, so your total is what matters. Unanswered questions count as wrong and there is no guessing penalty, so **never leave a question blank**. Full mechanics and test-taking strategy are in [blueprint/00-vision-examen.md](blueprint/00-vision-examen.md).

### Exam at a glance

| Attribute | Value |
|---|---|
| Exam code | AIP-C01 |
| Level | Professional |
| Questions | 75 total (65 scored + 10 unscored pretest) |
| Time | 180 minutes (~2.4 min/question) |
| Cost | $300 USD *(confirm current price at registration)* |
| Pass score | 750 on a 100–1,000 scaled range |
| Scoring model | Compensatory (no per-domain minimum) |
| Question types | Multiple choice (1 of 4); multiple response (2+ of 5+, all correct required, no partial credit) |
| Blank answers | Count as incorrect; no guessing penalty |
| Delivery | Pearson VUE test center or online proctored |
| Languages | English, Japanese, Korean, Simplified Chinese |
| Credential validity | 3 years |

### Domain weights

| Domain | Name | Weight | Study emphasis |
|---|---|---|---|
| D1 | Foundation Model Integration, Data Management & Compliance | 31% | Highest — deepest study |
| D2 | Implementation & Integration | 26% | Second — heavy study |
| D3 | AI Safety, Security & Governance | 20% | Solid coverage |
| D4 | Operational Efficiency & Optimization | 12% | Targeted |
| D5 | Testing, Validation & Troubleshooting | 11% | Targeted |

**D1 + D2 = 57% of the exam.** More than half your weighted score comes from two domains, so more than half your effort goes there.

## How to use this course

1. **Start with [PLAN-ESTRATEGICO.md](PLAN-ESTRATEGICO.md).** It drives everything — follow it week by week.
2. **Blueprint files = theory.** Read the domain file for the week, focusing on the tables and the "Exam traps" section.
3. **Decision tables = memorize.** The [tablas-decision/](tablas-decision/decision-por-restriccion.md) files turn a scenario's constraint keyword into the right answer. Memorize them cold.
4. **Practice = rehearse.** Work [practica/banco-preguntas.md](practica/banco-preguntas.md) under time pressure, then run the full mock in [practica/simulacro-final.md](practica/simulacro-final.md).

## Table of contents

- [PLAN-ESTRATEGICO.md](PLAN-ESTRATEGICO.md) — the 8-week calendar-anchored plan
- Blueprint (theory)
  - [blueprint/00-vision-examen.md](blueprint/00-vision-examen.md) — exam format & test-taking strategy
  - [blueprint/dominio-1-fundacion-datos.md](blueprint/dominio-1-fundacion-datos.md) — Domain 1 (31%)
  - [blueprint/dominio-2-implementacion.md](blueprint/dominio-2-implementacion.md) — Domain 2 (26%)
  - [blueprint/dominio-3-seguridad.md](blueprint/dominio-3-seguridad.md) — Domain 3 (20%)
  - [blueprint/dominio-4-optimizacion.md](blueprint/dominio-4-optimizacion.md) — Domain 4 (12%)
  - [blueprint/dominio-5-testing.md](blueprint/dominio-5-testing.md) — Domain 5 (11%)
- Decision tables (memorize)
  - [tablas-decision/decision-vector-stores.md](tablas-decision/decision-vector-stores.md) — pick a vector/search store
  - [tablas-decision/decision-despliegue.md](tablas-decision/decision-despliegue.md) — pick a deployment/inference mode
  - [tablas-decision/decision-por-restriccion.md](tablas-decision/decision-por-restriccion.md) — constraint keyword → preferred pattern (master table)
- Practice (rehearse)
  - [practica/banco-preguntas.md](practica/banco-preguntas.md) — ~50 original scenario questions
  - [practica/labs-hands-on.md](practica/labs-hands-on.md) — optional time-boxed labs
  - [practica/simulacro-final.md](practica/simulacro-final.md) — final mock & readiness gate
- [recursos.md](recursos.md) — curated official & third-party resources

## Accuracy & sources note

This course states AWS service **behaviors** plainly, but it deliberately avoids inventing precise figures. Where a specific number or version could drift — exact pricing percentages, exact model context windows, exact model version strings — the text gives the concept and flags **"confirm in current AWS docs."** Always verify current price, exam date, and the official exam guide revision at registration. Sources are collected in [recursos.md](recursos.md).

All practice questions are **original**. This course does not reproduce or imitate real AWS exam items.
