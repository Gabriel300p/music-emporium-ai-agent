# From Requirements to a Working Prototype with AI-Assisted Engineering

**Artefact AI Engineer case | Music Emporium | Evidence-backed interview narrative | 2026-11-02**

> **Claim boundary:** The initial prototype was built using ChatGPT as an AI coding and tool-use collaborator with human-supplied goals and source files. It is **not evidence of an unsupervised production agent**, nor of validated end-to-end LLM response quality.

## Why this is a relevant AI Engineering story

The assignment started with a three-page specification, six related CSV tables and an eight-page internal customer-service policy manual. Instead of manually producing a full implementation first, I explored how far an AI-assisted tool workflow could convert those inputs into a concrete, reviewable foundation.

ChatGPT helped inspect the materials, generate a Python codebase, wire bounded read-only tools, create tests and examples, write the README and publish successive commits to GitHub. The result was an executable **foundation** rather than merely a proposal or a set of mockups. This is a practical demonstration of using AI not only to generate snippets, but to coordinate a scoped engineering workflow with artifacts and verification.

The important second part of the story is **human ownership**. The assistant took many initial technical decisions before I had actively evaluated the alternatives. I recognized this as a process gap and deliberately changed the workflow: establish a product/architecture briefing, select a balanced engineering + applied AI strategy, compare alternatives, require evidence, and approve major changes before implementation. The current code is a provisional baseline, not a claim that I designed every element of it.

## Relationship to Pandora (prior project experience)

Pandora is a separate, ongoing initiative through which I have explored AI-agent orchestration, structured tool use, context and knowledge management, audit trails, and evidence-based validation. That experience shaped **the questions I ask** about agent autonomy: what actions an agent can take, how to constrain them, how to recover context, how to distinguish output from verified results, and when a person needs to make the decision.

This Music Emporium exercise provided a smaller, easier-to-review example of those ideas. It is **conceptual transfer**, not a claim that Pandora's runtime, agents or source code executed this assignment or were integrated into the retailer prototype. Do not infer production reliability or measured time savings from the existence of a functioning scaffold.

## What happened, and what evidence supports it

| Stage | What happened | Evidence / limitation |
|---|---|---|
| Inputs and problem framing | A customer-service case specification was paired with structured operation data and written store policies | Assignment and private materials supplied for the exercise; original customer records and internal manual are not public |
| AI-assisted foundation | ChatGPT generated the initial Python CLI, Responses API tool loop, CSV lookup tools, policy retrieval, tests and documentation | `src/emporio_agent/`, `tests/`, `README.md`, Git commit history; **live hosted LLM not tested** |
| Reproducible checks | Deterministic queries and policy lookup were exercised; a public-safe set of related data was prepared | `reports/VALIDATION.md`: **31 passed** with locally supplied original data; **18 passed, 13 skipped** without it; these counts are offline tests, not model-quality metrics |
| Transparency and privacy | Sensitive identities, tracking details and the restricted original PDF were excluded from public Git history | `data_public/README.md`, `docs/SECURITY.md`, `tests/test_public_data.py`; public policy PDF is synthetic |
| Governance course correction | I explicitly requested an architecture briefing after noticing the assistant had made design choices for me | `docs/ARCHITECTURE_BRIEF.md`, `docs/DECISION_REGISTER.md`; Strategy C was candidate-approved, initial architectural details remain provisional |
| Independent review (next) | Claude in VS Code should challenge code, assumptions and claimed results before we revise architecture | `docs/CLAUDE_VSCODE_REVIEW_PROMPT.md`, `docs/EVALUATION_PLAN.md`; review and real LLM evaluation are **not yet claimed completed** |

## What this demonstrates — and what it does not

**Demonstrates:**
- Translating a problem statement and heterogeneous materials into testable software with AI assistance.
- Applying a bounded tool-based design that separates deterministic business-data operations from language generation.
- Maintaining an auditable trail of code, decisions, limitations and offline test evidence.
- Recognizing an AI workflow failure mode — building too much before the candidate approves architecture — and introducing human decision gates.
- Using prior Pandora experience to ask stronger questions about reliability and agent boundaries.

**Does not demonstrate yet:**
- An AI support agent independently handling real customers.
- A live model choosing the correct tool and producing grounded answers across the scenario set.
- A measured uplift in support performance, development speed, quality, costs, or hiring outcomes.
- Production-ready authentication, compliance, observability or live inventory synchronization.
- The candidate having personally authored all baseline code or made all initial implementation choices.

## Interview pitch: 45–60 seconds (English)

> “One interesting part of this Artefact case was the development process itself. I'd been exploring agent orchestration, tool use and evidence-based validation in my Pandora project, and I wanted to see how those principles could work in a smaller, concrete challenge. Starting from the brief, six CSV tables and a policy document, I used ChatGPT's coding and tool workflows to turn the materials into a working Python foundation: read-only data tools, policy retrieval, automated tests and a public repository. The offline tests passed, but I don't confuse that with validating live LLM behavior. I also noticed that the assistant had made architectural choices before I had reviewed them. So I introduced a briefing and decision register, chose a pragmatic AI-engineering direction, and set up an independent review before making changes. For me, the key learning is that AI can accelerate implementation, but engineering ownership comes from understanding, testing and governing the result.”

## Interview pitch: 20 seconds (English)

> “I used an AI-assisted workflow to transform Artefact's documentation and datasets into a runnable Python agent foundation, building on lessons from my Pandora agent-orchestration project. It passed deterministic tests, but the real LLM still needs evaluation. I then introduced a human-led architecture review because generating working code is not the same as owning the engineering decisions.”

## Follow-up questions to prepare for

1. **“What did you personally do?”** I framed the goal, supplied and reviewed the source material, chose the balanced strategy, recognized the ownership gap and initiated the decision/evaluation process. Initial implementation and many choices were generated with AI assistance.
2. **“Was this fully autonomous?”** No. It was a human-directed, tool-assisted workflow with substantial automated execution and explicit constraints. No unsupervised production agent or uninterrupted end-to-end autonomy has been verified.
3. **“What worked?”** Offline data operations and scripted checks; refer to exact results in `reports/VALIDATION.md`. Be prepared to reproduce them.
4. **“What isn't proven?”** Hosted LLM routing, response faithfulness, live costs/latency and production security. A locally tested code scaffold is not proof of those properties.
5. **“How did Pandora contribute?”** Primarily as prior experience and a framework for thinking about tool permissions, context, traceability and verification. No direct code/runtime integration is claimed.
6. **“What would you change first?”** First run the bounded live evaluation and inspect observed failures. Compare lexical vs more advanced retrieval only if the scenario suite shows meaningful errors; protect privacy and make explicit decisions with acceptance criteria.

## Reviewer instructions

Before reusing this case study in an Artefact submission or live interview, check the corresponding code, tests, artifacts, and commit history. Replace any claim not supported by evidence with a qualified statement. Preserve the distinction between AI-generated foundation, candidate-approved decisions, offline validation and pending live evaluation. Do not add invented outcome percentages or attribution.
