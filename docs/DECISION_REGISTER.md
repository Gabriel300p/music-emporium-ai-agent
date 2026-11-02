# Architecture decision register

This records **provenance and ownership** of decisions. A working implementation is not the same as a candidate-approved architecture. Update this register only after actual discussion and validation.

| ADR | Topic | State | Who/when | Evidence |
|---|---|---|---|---|
| ADR-001 | Project strategy: balanced engineering + applied AI, avoid gratuitous complexity | **Accepted** | Candidate choice on 2026-11-02 | Briefing conversation; `ARCHITECTURE_BRIEF.md` |
| ADR-002 | Keep the current hybrid direct-function-calling implementation as a reviewable baseline | **Provisional** | Initially implemented with AI assistance | README + source/tests; requires candidate review |
| ADR-003 | Use lexical PDF retrieval rather than vector RAG | **Provisional** | Initial implementation, not candidate-approved | Requires evidence from paraphrase retrieval evaluation |
| ADR-004 | Retain Python CSV query functions rather than SQL agent | **Provisional** | Initial implementation, not candidate-approved | Current CSV sizes; evaluate query needs |
| ADR-005 | Protect original identifiable customers, order tracking and internal policy PDF | **Accepted for public publication** | Safe publication decision 2026-11-02 | `data_public/README.md`, export script and privacy tests |
| ADR-006 | Use the present CLI rather than add UI | **Provisional** | Initial implementation, not candidate-approved | Technical assignment explicitly permits CLI |
| ADR-007 | Select final provider and model | **Open** | Candidate decision pending | No live API benchmark |
| ADR-008 | Decide whether to invest in semantic retrieval/observability | **Open** | Candidate decision pending | Evaluation plan first |
| ADR-009 | Use the ChatGPT-assisted transformation from source materials to tested foundation as an evidence-backed interview case, with Pandora as prior conceptual experience | **Accepted as narrative direction; specific claims remain subject to review** | Candidate request 2026-11-02 | `AI_ASSISTED_ENGINEERING_CASE_STUDY.md` + commit/test evidence; no claim of fully autonomous production execution |

## Engineering ownership and attribution

The first executable baseline was generated with AI assistance before the candidate had reviewed every implementation decision. The candidate selected **balanced engineering + applied AI (Strategy C)** and requested a change in process: **specification → AI-assisted baseline → reproducible checks → candidate briefing → explicit architecture choices → independent review**.

Documenting this workflow as an interview case does **not** retroactively make the initial design decisions candidate-authored. Pandora is referenced as prior experience and a source of engineering principles; it is not claimed to have supplied a runtime to this application.

## ADR template for future candidate decisions

```text
Decision ID:
Business/technical problem:
Alternatives A/B/C:
Selection and reasoning:
Expected measurable improvement:
Test evidence (command/output/date):
Risks and limitations:
Owner / approval date:
```
