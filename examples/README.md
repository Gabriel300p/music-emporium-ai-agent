# Five reproducible conversation examples

The files in this directory are **outputs of the local deterministic demonstration** (`OfflineAgent`), using the **fully synthetic** fixtures in `demo_data/`. They illustrate source lookup and business rules without revealing the supplied private data. **They are not recordings of a hosted LLM deciding which tool to call.**

| Example | What it demonstrates | Tool / behavior |
|---|---|---|
| [`01_catalogue_budget.md`](01_catalogue_budget.md) | Available violões under R$ 1,000 | `search_products` |
| [`02_model_and_out_of_scope.md`](02_model_and_out_of_scope.md) | Exact model price and unrelated request | `search_products`, scope fallback |
| [`03_promotions.md`](03_promotions.md) | Current/original price, promotional discount and PIX | `search_promotions`, `search_policies` |
| [`04_return_policy.md`](04_return_policy.md) | Buyer's remorse and document page | `search_policies` |
| [`05_order_verification.md`](05_order_verification.md) | Multi-turn order verification and privacy denial | `order_status` |

Recreate them locally:

```bash
python scripts/record_examples.py --data-dir demo_data --out-dir examples
```

The real model path is implemented separately. To produce LLM-generated transcripts, an authorized API test must first be executed using a privacy-safe dataset, followed by a manual review of the outputs. See [`docs/EVALUATION_PLAN.md`](../docs/EVALUATION_PLAN.md).
