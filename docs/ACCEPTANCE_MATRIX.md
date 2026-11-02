# Artefact technical-case requirements — evidence matrix

This table separates **implemented behavior**, **local test evidence** and **remaining verification**. The five recorded examples are deterministic offline runs, not hosted-LLM transcripts.

| Requirement from the assignment | Where to inspect | Evidence / status |
|---|---|---|
| Python as primary language | `src/emporio_agent/`, `pyproject.toml` | **Implemented** |
| Store-appropriate text persona | `src/emporio_agent/agent.py` (`SYSTEM`) | **Implemented prompt; live-model tone not tested** |
| Text interaction | `src/emporio_agent/cli.py` | **CLI tested offline** |
| Data lookups for stock, pricing and order | `store.py`, `tests/test_store.py`, `tests/test_case_dataset.py` | **Deterministic checks passed** |
| Policies vs structured data | `agent.py` tool contracts, `policies.py` | **Tools implemented; actual model-routing decision not tested** |
| Out-of-scope behavior | `agent.py`, `offline.py`, `docs/EVALUATION_PLAN.md` | **Offline demonstrator tested; live response pending** |
| Architecture choices and justification | `README.md`, `docs/ARCHITECTURE_BRIEF.md`, `docs/DECISION_REGISTER.md` | **Documented, with candidate review provenance** |
| Setup and execution | `README.md`, `data_public/README.md` | **Offline locally executed; clean online installation not tested** |
| Limits and possible improvements | `README.md`, `docs/SECURITY.md`, `docs/EVALUATION_PLAN.md` | **Documented** |
| Use of AI coding assistants | `README.md`, `docs/AI_ASSISTED_ENGINEERING_CASE_STUDY.md` | **Disclosed** |
| Three to five example conversations | `examples/01_...` through `05_...` | **Five reproducible offline transcripts, not LLM output** |
| Public repository with progressive commits | GitHub main branch and commit history | **Published** |
| Recruiter delivery | Reply to the recruiter and follow the form/PDF instructions when applicable | **Separate candidate action; not a feature of this repository** |

**Known gap:** No hosted-model API request has been executed, so the most important model-driven capability—selecting the appropriate tool and producing a grounded final answer—remains **unverified end to end**. See [validation](../reports/VALIDATION.md) and [evaluation plan](EVALUATION_PLAN.md).
