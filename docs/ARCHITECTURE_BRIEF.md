# Architecture briefing — Music Emporium AI Agent

**Candidate-led review · Draft v1 · 2026-11-02**

## 1. Business problem

The Empório da Música staff handles repetitive questions about catalogue, pricing, stock availability, shipments and store policies. The prototype aims to answer common text messages reliably and to hand off questions that require judgment, a real-time system, or account changes.

**Important:** The brief is a decision-support document, **not proof of performance**. The codebase already exists; decisions that were made during initial implementation must be reviewed by the candidate, rather than presented as candidate-led choices retroactively.

## 2. Product boundaries

- Included: product and promotion lookups, limited read-only order-status checks, policy/returns/payment answers, safe refusal or handoff.
- Excluded: payment collection, refunds, order changes, live inventory, writing customer support tickets, human-impersonation, autonomous external side effects.
- Data reality: CSV files are historical snapshots. The complete eight-page manual is supplied internally; the public checkout contains a synthetic policy demonstration, **not** the restricted source manual.
- Audience: Brazilian Portuguese-speaking customer, on a text/CLI prototype. CLI is a testing surface, not a production WhatsApp integration.

## 3. Strategy chosen with the candidate: **C — pragmatic engineering + applied AI**

Consciously keep deterministic calculations and controlled tool APIs. Reserve complexity (vector embeddings, agent frameworks, SQL, tracing platform, UI) for a measured improvement rather than to increase the tool count.

| Option | Value | Main drawback | Current position |
|---|---|---|---|
| A. Rules-only or full context prompt | Very simple | Stale answers and prompt-bound data operations | Useful baseline, not proposed final agent |
| B. Function calling + deterministic CSV + lexical policy retrieval | Explainable; bounded; low infrastructure | Retrieval paraphrase misses; tool-routing depends on model | **Implementation baseline** |
| C. Framework agent + semantic RAG + SQL agent | Flexible extension path | Cost, latency and complexity without guaranteed gain | **Only if evaluation supports it** |

> Terminology: The **chosen process direction is Option C from the briefing (balanced engineering + AI)**, not necessarily architecture alternative C in the table above. Today's *implemented architecture* remains the B-style hybrid baseline.

## 4. Current request flow

1. The CLI sends a message to `Agent.reply`.
2. The LLM receives a persona/system prompt plus four JSON-schema tool contracts.
3. It may call `search_products`, `search_promotions`, `order_status` or `search_policies`.
4. Python tools perform read-only operations on CSV snapshots or PDF page excerpts.
5. The tool output returns to the LLM, which drafts a customer response.
6. The response should cite pages for policy claims, state when stock/order information is only a snapshot, and admit unknowns.

`--offline` uses a deterministic intent demonstrator, **not** the LLM. The two modes must never be conflated in the technical presentation.

## 5. Decisions reserved for the candidate

| ID | Question | Baseline | Alternative to test | Why it matters |
|---|---|---|---|---|
| D1 | Tool orchestration | Direct Responses API, bounded loop | LangGraph or explicit multi-step planning | Does added state management solve a real failure? |
| D2 | Policy retrieval | Lexical ranking per page | BM25/chunks, embeddings, hybrid reranking | Accuracy of paraphrases, citations, conflicts |
| D3 | Structured data | Python functions reading CSV | SQLite + SQL query layer | Scale, query complexity, determinism, access control |
| D4 | Model/provider | Configurable `gpt-4.1-mini` baseline | Other cost/latency/quality point | Choose after real API evaluation |
| D5 | Conversation/context | In-memory history | Session IDs and summarized state | Privacy, reproducibility, cost |
| D6 | User interface | CLI | Minimal web UI | Does UI help assess agent behavior under deadline? |
| D7 | Order verification | Order ID + matching email | OTP/authenticated customer identity | Do not call the prototype method secure authentication |
| D8 | Evaluation/tracing | Offline pytest + tool trace | Measured scenario suite and live calls | Evidence of tool selection, grounding, safety and cost |

**Status:** D1–D8 are **provisional**. No new architecture or provider has been approved. The candidate should prioritize D2, D4 and D8 after the review.

## 6. What we can substantiate today

- The code runs with synthetic and sanitized CSV snapshots, and local deterministic tests are reproducible.
- Formula-based prices, stock flags and FK joins can be checked by test assertions.
- Source-PDF pages can be retrieved locally when the original is available; public demo policy is synthetic.
- No live LLM request, model-route accuracy score, latency benchmark, or per-call cost has been measured in this work session.

## 7. How to present this in an interview (without invented claims)

Explain: **problem → considered alternatives → chosen constraint → observed evidence → remaining risk**. Example answer template:

> “For structured catalogue data, I chose deterministic functions so the model cannot compute prices or availability from memory. For the short policy manual, I started with page-level lexical retrieval. I'd only add embeddings after showing retrieval failures on a small evaluation set. At this stage I can demonstrate passing offline tests, but live model routing and response quality still need validation.”

State clearly that ChatGPT assisted with the first implementation, and identify which choices were reviewed or changed by the candidate during the subsequent briefing. **Do not claim metrics or authorship that were not observed.**

## 8. Briefing approval gate

Before an architecture change, record: (1) user/customer failure; (2) option A/B/C considered; (3) expected result; (4) acceptance criterion; (5) estimated implementation and evaluation effort; (6) candidate approval. Low-risk documentation and test-fixture improvements may proceed independently.
