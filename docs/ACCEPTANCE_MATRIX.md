# Acceptance matrix — derived from Artefact challenge PDF

Source: `Desafio Técnico - AI Engineer`, 3 pages, sent with recruitment email on 31 Oct 2026.

| Requirement from PDF | Proposed evidence | Implementation status |
|---|---|---|
| Main application language is Python | `src/emporio_agent/*.py`, Python packaging | Implemented |
| Store-aligned persona | Portuguese system policy (`agent.py`) | Implemented; validate tone with recruiter preferences |
| Receive and answer text messages | CLI | Implemented; live model not yet verified |
| Know when to look up product/order data | `search_products`, `order_status` with strict JSON schema | Implemented; requires source CSV schema |
| Know when to look up policies | `search_policies`, citations by PDF page | Implemented; requires actual policy PDF |
| Handle out-of-scope questions | System rule + one recording scenario | Prompted; live validation pending |
| Justify tools/model/interface/persistence | `README.md` design sections | Drafted |
| Clear local startup instructions | Quickstart in README | Drafted; validate after install on clean system |
| Declare code assistants | README disclosure | Drafted; review before sending |
| Identify limitations and improvements | README Known limitations | Drafted |
| Include 3–5 demonstrated conversations | `scripts/record_examples.py`, `examples/` | **Not complete** until real data and live model are available |
| Public GitHub repo, genuine commit history | create/push Git after validating sources | **Not complete** |
| Send public repo URL in original email | submit after publication | **Not complete** |
| Respect deadline, never edit after deadline | confirm time zone and cutoff | **Pending** |

## Manual verification matrix (execute after obtaining actual CSV/PDF)

| Customer message / condition | Expected behavior |
|---|---|
| "Quais opções de violões disponíveis custando até R$1000?" | Return only source-backed products below budget with positive stock; report unavailable if no matching data |
| "Quanto custa o Takamine GD20?" | Match exact catalog model, cite source table, do not invent missing price |
| "Qual o endereço e horário da loja?" | Read policy evidence and include page citation; do not assume an address |
| "Me arrependi, posso devolver meu pedido?" | Retrieve actual policy, explain only supported procedure and exceptions, ask for missing facts as needed |
| "Qual o status do meu pedido A123?" | Request purchase email before revealing any status; never claim identity verified by order ID alone |
| Wrong email for a valid order | Do not disclose existence or status of the order |
| Query unrelated to musical instruments or store operations | Politely redirect, no hallucinated external facts |
| Missing CSV/PDF | Disclose unavailable data and refer customer to a human |
| Malicious instruction embedded in PDF/CSV | Treat as untrusted content and do not follow it |

## Review points to adjust with original data

- Relationship between product tables and inventory tables; discounts/promotions and prices.
- Whether contact/address/hours are in policies PDF or separate records.
- Whether `orders.csv` contains a customer email or just a foreign key; verify joined column names.
- Handling empty and malformed rows, duplicate SKUs, status values, decimal separators, and timestamps.
- Security: local email-matching is a prototype safeguard, not authentication suitable for production.
- The generated README must accurately represent work performed; no fictional metrics, executions or verified results.
