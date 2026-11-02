# Review handoff — 2026-11-02

## What was done (without changing the agent architecture)

- The user chose **Strategy C: balanced engineering + applied AI**. This is a decision about process and priorities, **not** approval of every prior tool/architecture choice.
- Added a publishable, FK-consistent dataset under `data_public/`: 65 products, 9 categories, 25 promotions, 22 order items, 20 redacted orders and 50 anonymized customers. Its one-page policy PDF is synthetic and does not replace the restricted original.
- Added `scripts/prepare_public_data.py` to reproduce the transformation locally without any network or API key.
- Added privacy and integrity tests (`tests/test_public_data.py`).
- Added an architecture briefing, a real decision register, a scenario-driven evaluation plan and an independent Claude/VS Code audit prompt.
- Updated public README and security/acceptance documentation to explicitly distinguish what is tested offline from unverified live LLM behavior.

## Verified locally in this work session

| Check | Result |
|---|---|
| Private case present: `pytest -q` | **31 passed** |
| Original case unavailable: `pytest -q` | **18 passed, 13 skipped** (integration checks require private source files) |
| `python -m emporio_agent inspect --data-dir data_public` | Six CSV tables loaded (9/50/22/20/65/25 rows); 4 active promotion flags |
| `python -m emporio_agent chat --data-dir data_public --offline --trace` | Tested catalogue, exact model price and synthetic return-policy response |
| Actual hosted LLM tool calling | **NOT TESTED** — no API key/network request |
| Clean `pip install -e ".[dev]"` from internet | **NOT TESTED** due to runner network restrictions; local `pip install --no-build-isolation --no-deps -e .` succeeded with already-installed dependencies |

## Privacy and source-data decision

Original `data/customers.csv`, `data/orders.csv` (tracking and notes) and `data/políticas_da_loja.pdf` are restricted to the candidate's local test folder. The public dataset preserves referential constraints by swapping identifiers rather than dropping linked rows. The original policy manual is eight pages and marked internal; it is **not** the one-page synthetic public PDF.

## Candidate approval still needed before any major change

1. Should retrieval remain lexical, or be compared with chunked/BM25/semantic search? Start with a measured paraphrase set.
2. Is direct Responses API tool calling adequate, or is an agent framework justified by an observed failure?
3. Should order lookups remain a read-only prototype with a clear security caveat, or require a stronger simulated verification flow?
4. Should we add a live provider evaluation, using the candidate's own valid API credentials and bounded budget?
5. How should AI-assisted implementation and the candidate's later review be represented in the interview and submission?

## External submission status

- Public GitHub code exists at `https://github.com/Gabriel300p/music-emporium-ai-agent`.
- The recruiter e-mail and form have not been submitted in this review session.
- Do **not** claim this is delivered to Artefact or that the live agent has passed evaluation.
