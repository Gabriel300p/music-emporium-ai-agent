# Case dataset — public-safe working copy

This folder provides a **functional, schema-compatible supplement to the Artefact technical case**. It allows reviewers to run catalogue, promotion, and order lookup against a dataset larger than the two-customer synthetic demo. It is **NOT** the original complete private submission bundle.

| File | Rows | Origin and changes |
|---|---:|---|
| `categories.csv` | 9 | Original case table; no customer-level fields |
| `products.csv` | 65 | Original case table; no customer-level fields |
| `promotions.csv` | 25 | Original case table; no customer-level fields |
| `order_items.csv` | 22 | Original case table; relational IDs kept, no customer-level fields |
| `customers.csv` | 50 | **Sanitized**: names, phone numbers, emails and cities are replaced with fictitious values; customer IDs preserved for joins |
| `orders.csv` | 20 | **Sanitized**: tracking codes replaced by DEMO values, free-text notes removed; order/customer IDs retained for joins |
| `políticas_da_loja.pdf` | 1 page | **Fully synthetic demonstration document** copied from `demo_data/`; NOT the supplied eight-page, internal/restricted manual |

The original eight-page PDF and identifiable customer records are intentionally **not** in Git history. Its policies are referenced in the architecture explanation; verify interpretations using the authorized, private original. This copy does not contain every real rule.

## Run

```bash
pip install -e ".[dev]"
python -m emporio_agent inspect --data-dir data_public
python -m emporio_agent chat --data-dir data_public --offline --trace
pytest -q
```

For a genuine LLM-based run, configure `OPENAI_API_KEY` in your own local environment and **explicitly** choose either `--data-dir data_public` (sanitized) or `--data-dir data` (private originals). No API-backed test has been run on this repository so far.

## Reproduce

With the authorized case CSVs copied to your local, Git-ignored `data/` directory, run:

```bash
python scripts/prepare_public_data.py --source-dir data --out-dir data_public
```

This script uses deterministic pseudonyms and verifies foreign keys and redaction. Never commit `data/`, full customer identities, private order codes, API keys or the internal PDF. Do not mistake a matching order ID + email in the prototype for strong authentication.

**Integrity note:** Preserving real catalogue names, product details and transaction amounts allows realistic evaluation of query logic, but the orders/clients are de-identified test fixtures; do not treat this as a live business system.
