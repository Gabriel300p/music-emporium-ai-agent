# Validation record

**Scope:** tests and checks performed locally against the supplied case files, synthetic public fixtures and deterministic agent components. The project does **not** claim a live-model evaluation.

## Current test results — 2026-11-02

| Environment | Command | Observed result |
|---|---|---|
| Authorized original data available in local ignored `data/` | `pytest -q` | **31 passed** (re-run on 2026-11-02) |
| Clean public-only dataset (no original private `data/`) | `pytest -q` | **18 passed, 13 skipped** (the skipped checks require original files) |
| Public datasets | `python -m emporio_agent inspect --data-dir data_public` | Six CSV tables loaded; active promotion flags: **4** |
| Public offline demonstration | `python -m emporio_agent chat --data-dir data_public --offline --trace` | Catalogue and policy retrieval routes executed with deterministic demo logic |
| Hosted LLM and model-driven responses | Real API call | **NOT RUN / NOT VERIFIED** |
| Clean internet-connected setup | `pip install -e ".[dev]"` | **Not validated in an internet-enabled clean environment** |

The local environment's regular pip install needed network for build isolation; using existing dependencies with `--no-build-isolation --no-deps` succeeded. A clean machine should follow the README and verify installation separately.

## Source inventory and relational checks

| File | Records | Relevant check |
|---|---:|---|
| `products.csv` | 65 | Product status/stock, prices, category keys |
| `categories.csv` | 9 | Category key joins |
| `promotions.csv` | 25 | Product link, active campaign flags |
| `orders.csv` | 20 | Customer foreign keys and status |
| `order_items.csv` | 22 | Order/product joins |
| `customers.csv` | 50 | Purchase-email match in read-only order lookup |
| Original policies PDF | 8 pages | Page-level text retrieval tested locally |

No orphan foreign keys were found in the expected joins. The original PDF is internal; the public one-page document is **synthetic** and does not reproduce the full source rules. The public CSVs preserve non-personal catalogue data and sanitize customer identities and tracking information; see [`data_public/README.md`](../data_public/README.md).

## Reproducible deterministic examples

| Scenario | Observed result | Important boundary |
|---|---|---|
| Available violões up to R$ 1,000 | **12** matches in the case snapshot, eight shown by default | Snapshot only; not live inventory |
| Takamine GD20 lookup | R$ 2,199.00 in original product file | CSV value, not model memory |
| Crafter HT-100 active promotion | R$ 2,399.00 → R$ 1,967.18 after 18% | No additional 5% PIX on promotions |
| Unavailable products | Discontinued, coming-soon and zero-stock cases filtered appropriately | No guarantee of current availability |
| Order ID with correct/incorrect email | Generic denial for invalid match; verified response for matching pair | Not production authentication |
| Policy retrieval | Returns source pages for returns, payments, shipping, privacy | Manual contains ambiguities needing human confirmation |
| Unrelated question | Returns `no_evidence` or an offline scope response | Not proof of LLM refusal behavior |

The source manual contains different contact channels (pages 2 and 6) and separate exchange/warranty rules (pages 4 and 7). The assistant must not collapse these into unsupported promises.

## What the tests cannot establish

- The model's accuracy in choosing tools, following the prompt, generating answers and citing pages.
- End-to-end quality, latency, token costs, reliability over repeated attempts or user satisfaction.
- Real-time inventory, production privacy compliance, secure customer identity verification or deployment readiness.

**Next measurement:** run the fixed scenarios from [`docs/EVALUATION_PLAN.md`](../docs/EVALUATION_PLAN.md) with an explicitly authorized provider and bounded budget. Record actual tool traces and answer-level evidence, then address observed failures before adopting additional frameworks.
