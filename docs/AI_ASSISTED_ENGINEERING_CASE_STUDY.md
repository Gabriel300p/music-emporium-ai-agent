# From a technical brief to a testable AI-agent foundation

**Music Emporium · An AI-assisted engineering workflow, with explicit human review**

## The opportunity

The Artefact challenge provided an initial specification, six related operational CSV tables and a store-policy manual. The engineering problem was not simply to produce fluent customer replies: the assistant needed to choose **when to inspect structured data, when to retrieve written rules, and when to acknowledge a limitation**.

I used this bounded exercise to explore two complementary ideas: **how much of an initial engineering workflow can be accelerated with AI assistance**, and **how to verify and take responsibility for the resulting software**.

## A concrete foundation, not just a proposal

Starting from the materials supplied for the assessment, a ChatGPT-assisted development workflow generated an initial Python project with:

- An OpenAI Responses API tool-calling loop and four read-only lookup functions.
- Relational CSV lookups for products, promotions and orders, including deterministic pricing rules.
- Page-based lexical retrieval over a PDF, with source-page references.
- A CLI, repeatable offline examples, automated tests and documented constraints.
- A public Git history and a privacy-safe dataset that preserves testable relationships.

That converted written requirements and static files into **runnable software artifacts**. The documented checks verify local deterministic behavior, **not** the quality of actual hosted-model responses.

## Where Pandora contributed

My separate **Pandora** project exposed me to ideas around agent orchestration, tool permissions, context, traceability and verification. I brought that perspective to the evaluation of the Music Emporium foundation: a useful agent needs controlled actions, grounded evidence and observable failure paths—not just a plausible answer.

This was a transfer of **engineering experience and questions**, not a reuse of Pandora's runtime, agents or source code. No direct integration is claimed.

## The engineering decision that followed

The AI-assisted baseline was created **before I had personally reviewed all its architectural choices**. I subsequently recognized a gap: automated execution can create working code faster than a developer can establish ownership of every decision. The corrective action was to make those decisions explicit rather than retroactively claim authorship.

I selected a **balanced engineering + applied AI** direction. The existing implementation remains a reviewable baseline while the decision register records alternatives and an evaluation plan defines what would justify additional complexity, such as semantic retrieval or an orchestration framework.

The resulting workflow is:

**Brief and source material → AI-assisted implementation → reproducible checks → human architecture review → evidence-based iteration.**

## What is proven, and what is next

| Evidence today | Boundary |
|---|---|
| **31 automated tests passed** with the authorized original material available locally | These are offline code and data tests, **not** a hosted-model quality score |
| **18 passed, 13 skipped** on a public-only checkout | The skipped checks need the original private files |
| Structured catalogue and promotion queries, local policy retrieval and scripted examples run | No live inventory, production authentication or customer-facing deployment |
| Read-only function contracts and a bounded model loop are implemented | Live LLM tool selection, answer grounding, cost and latency still require evaluation |

The next engineering milestone is a small, fixed **live evaluation set**: validate whether the model chooses the expected tools, uses the returned evidence, cites policy pages and refuses unsafe disclosures. A failed test should drive a targeted change—not an automatic jump to LangGraph, embeddings or a vector database.

## Why this experience matters

The distinctive outcome is not a claim that AI independently developed a production system. It is a reproducible example of **AI accelerating the creation of a software foundation while the engineer remains responsible for verifying results and approving the architecture**.

That is the lesson I want to carry into future applied-AI projects: prototype quickly, make the implementation inspectable, and use measurable evidence and human judgment to decide what earns its way into the system.

**Transparency:** ChatGPT contributed substantially to initial code, tests and documentation. The technical review of the baseline is ongoing. I do not claim that I manually authored all code, that Pandora was integrated, or that a live LLM evaluation has passed.

**Further evidence:** [README](../README.md) · [architecture](ARCHITECTURE_BRIEF.md) · [decision register](DECISION_REGISTER.md) · [validation](../reports/VALIDATION.md) · [evaluation plan](EVALUATION_PLAN.md).
