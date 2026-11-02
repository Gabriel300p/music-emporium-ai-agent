# Empório da Música — Customer Support Agent (Artefact Technical Case)

> **Status: implementation starter, NOT submission-ready.** The full source dataset (`data/*.csv` and `data/políticas_da_loja.pdf`) has not been supplied yet. Unit tests run against explicitly **synthetic** fixtures only. No live LLM calls or original-data behavior have been validated.

## Goal

A read-only, text-based Brazilian Portuguese customer-support agent for a fictional musical-instrument store in Campo Grande/MS. It handles product availability and prices, order tracking with identity verification, store policies, and out-of-scope requests without inventing store facts.

## Architecture

```
Client (CLI)
     |
     v
OpenAI Responses API (function calling + bounded turn history)
     |
     +---- search_products() --> product CSV (deterministic filtering)
     |
     +---- order_status() ----> order CSV (+ customer email cross-check)
     |
     +---- search_policies() --> store PDF (read-only lexical retrieval + page source)
     |
     v
Grounded answer, explicit uncertainty and human handoff when needed
```

**Why hybrid?** Structured data requires exact, reproducible computation (max price, stock level, order matching). Policies are prose and require text retrieval with citation. A general-purpose SQL agent would give the model unnecessary query power; a vector database would introduce deployment overhead for one small PDF. Simple token-based PDF retrieval is explainable and adequate for a first prototype, although not robust to all paraphrases.

**Why no orchestration framework?** The model calls three small, typed, read-only tools. Explicit orchestration in a few lines keeps logic observable and reviewable. More abstraction can be justified after functional correctness is established.

**LLM:** OpenAI Responses API, configurable via `OPENAI_MODEL`; default `gpt-5.4-mini` for relatively economical function calling. Change model to one available on your API account. A ChatGPT subscription does *not* supply API credits. The application calls external APIs; never include secrets in Git.

**Conversation history:** In-process memory only; no database persistence. This limits complexity and avoids creating long-lived customer records. Process restarts reset the session.

## Quickstart

```bash
# Python 3.11+
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -e ".[dev]"

# Place original, authorized case files into data/ (do not commit PII).
# For the actual submission:
# data/produtos.csv, data/pedidos.csv, ... and data/políticas_da_loja.pdf
python -m emporio_agent inspect --data-dir data

# Set your environment variable, for example:
# Linux/macOS: export OPENAI_API_KEY="..."
# PowerShell: $env:OPENAI_API_KEY="..."
# Optional: export OPENAI_MODEL="gpt-5.4-mini"

python -m emporio_agent chat --data-dir data --trace
```

Run tests (no API key or network required):

```bash
pytest -q
```

For an **offline, synthetic schema inspection** without API calls:

```bash
python -m emporio_agent inspect --data-dir tests/fixtures/data
```

## Available tools and rules

| Tool | Input | Evidence | Safety properties |
|---|---|---|---|
| `search_products` | query, category, max BRL price, in-stock flag | CSV product snapshot | No prices or availability invented; unknown stock excluded from "in stock" filtering |
| `order_status` | order ID **and** purchase email | CSV order row and optional customer join | Never returns order details unless both values match |
| `search_policies` | customer's policy question | PDF excerpts with page numbers | Missing/unrelated policy => no claimed rule; handoff |

The agent does **not** place orders, perform returns, modify stock, or initiate payments.

## CSV schema validation (required before submission)

The original schema is unknown; `store.py` includes PT/EN alias defaults. Inspect actual columns, adjust names and relationships, then test representative products, discounts, stock, and order matching. **Do not claim real-time inventory:** these are CSV snapshots loaded at process start. If promotion data affects final prices, explicitly implement those price rules using the supplied data. Currently this starter does **not** apply promotions.

The policy index expects `políticas_da_loja.pdf` (or ASCII `politicas_da_loja.pdf`) in `data/` and a text-extractable PDF. If extraction is blank, respond with a handoff instead of inventing policy terms. The index is lexical; it is not embeddings-based RAG. Tool outputs are treated as untrusted data, not as instructions.

## Testing

- Unit tests validate BRL price parsing, product/category/budget matching, stock status, order email verification, missing data, PDF page citations, and the LLM tool-call round trip via a fake client.
- Tests do **not** validate current model quality, production data, endpoint availability, exact API cost, or accuracy across the full store-policy PDF.
- After obtaining original data: run manual test matrix for happy paths, ambiguous questions, missing records, wrong customer email, out-of-scope input, and prompt-injection attempts. Inspect answers and tool traces.

## Example conversations (mandatory for final submission)

The case requires **3–5 examples**, including at least one non-trivial data lookup or policy decision. No synthetic fixture conversation is presented as a genuine store result. Once original data and credentials are ready:

```bash
python scripts/record_examples.py --data-dir data --out-dir examples
```

Review each transcript manually and remove sensitive information. The script proposes catalogue, price, hours, return policy and out-of-scope scenarios.

## Known limitations and next steps

- CSV auto-detection/column aliases require adaptation to actual data; no full data schema was provided with the assignment PDF.
- Order verification by a known purchase email is a lightweight prototype measure, **not production-grade authentication**. Production requires authenticated customer sessions or a trusted verification channel.
- Product inventory is a snapshot, not live transactional inventory; simultaneous purchases and stale CSVs are not handled.
- Search is simple lexical retrieval, not semantic retrieval. Policy versioning, evaluation sets, and calibration are future improvements.
- There is no mutation, escalation ticket creation, multilingual support or observability backend.
- Histories are ephemeral and tool-call counts are bounded; long-lived sessions and error retries are future work.
- Original data can contain customer PII; local files must remain outside the public repo.

## Responsible use of coding assistants

This starter implementation, documentation and synthetic tests were prepared with **ChatGPT (OpenAI, GPT-6)**. The candidate must personally review and adapt the code, confirm all behavior against original CSV/PDF files, and be able to explain technical decisions. The final README should disclose any other assistants used during subsequent work and distinguish assistant-generated code from independent validation.

## Submission checklist

- [ ] Load original case CSVs and policy PDF; validate columns/joins.
- [ ] Test live Responses API against the actual dataset.
- [ ] Confirm order-privacy safeguards and the absence of invented policies/prices.
- [ ] Record 3–5 *real* example conversations, with at least one nontrivial case.
- [ ] Keep actual progressive Git commits (do not rewrite history as if work was not assisted).
- [ ] Publish a **public** GitHub repository with code, README and examples, **without PII or API keys**.
- [ ] Send the repo link to the original recruitment thread. The recruitment email also mentions a Google Form and PDF; reconcile and follow that channel too.
- [ ] Do not modify the repository after the submission deadline.
