# Technical decision register

The point of this register is to make the **implemented baseline**, its **provenance**, and the **next decision** visible. Code produced through AI assistance is not retroactively presented as a fully candidate-designed architecture.

| ID | Decision area | State / owner | Reasoning and next evidence |
|---|---|---|---|
| ADR-001 | Balance pragmatic engineering and applied AI | **Accepted by candidate, 2026-11-02** | Prefer minimal working scope; add tools/frameworks only when evidence calls for them |
| ADR-002 | Direct Responses API tool calling | **Implemented in AI-assisted baseline; candidate review pending** | Small read-only tool set; evaluate live tool selection before adding orchestration |
| ADR-003 | Page-level lexical policy retrieval | **Implemented in baseline; candidate review pending** | Eight-page manual; compare chunked/BM25/hybrid only on actual retrieval misses |
| ADR-004 | Python queries over CSV instead of SQL agent | **Implemented in baseline; candidate review pending** | Bounded source tables and deterministic arithmetic; revisit if relational complexity grows |
| ADR-005 | Keep private source data outside public Git history | **Accepted publication constraint** | Original customer identities, tracking information and restricted PDF excluded; public test data is documented |
| ADR-006 | CLI instead of a UI | **Implemented in baseline; candidate review pending** | CLI is permitted by the exercise and makes behavior inspectable |
| ADR-007 | Provider/model selection | **Open** | `gpt-4.1-mini` is a configurable baseline, not an evaluated winner; compare after approved live tests |
| ADR-008 | Stronger retrieval, agent state and observability | **Open** | Adopt only if fixed-scenario evaluation establishes a need |
| ADR-009 | Explain AI-assisted implementation and Pandora context accurately | **Accepted as narrative direction; factual claims require evidence** | The initial scaffold was substantially AI-generated; Pandora informed approach, not code reuse |

## Ownership rule

The development workflow exposed a useful constraint: an AI assistant can generate an executable foundation before its human collaborator has reviewed every technical choice. That is why the next phase is an architecture briefing and independent, reproducible review. **Strategy C is approved; individual baseline architecture choices are not automatically approved.**

Use this record for material changes:

```text
Decision / owner / date:
Problem and user impact:
Alternatives and trade-offs:
Current evidence (test, source and reproducible steps):
Choice and why:
Acceptance criterion:
New limitation or risk:
```
