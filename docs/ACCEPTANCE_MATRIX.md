# Artefact assignment: acceptance traceability

| Assignment requirement | Implementation / evidence | Validation status |
|---|---|---|
| Python language | `src/emporio_agent/*.py`; `pyproject.toml` | Confirmed |
| Persona fitting store voice | `agent.py` prompt: cordial, informal/professional, PT-BR | Prompt audited; live model not tested |
| Text interactions | `cli.py` interactive terminal | Offline demo executed |
| Product and stock lookups | `CSVStore.search_products()` with real joins/status | Real-data integration tests passed |
| Prices and promotions | `Decimal` discount calculation, no PIX stacking | Real-data integration tests passed |
| Order status | `CSVStore.order_status()` with order ID and purchase-email matching | Real-data integration tests passed; prototype-only security |
| Policies, opening hours and returns | `PolicyIndex.search()` with source page references | Real PDF retrieval tests passed |
| Out-of-scope questions | `agent.py` instructions + `offline.py` demo | Offline demo passed; live model not tested |
| Technical choices justified | Root README architecture/design decisions | Documented |
| Environment instructions | README quickstart (Python, API, CLI) | Offline mode executed |
| Known limitations / improvements | README risks section | Documented |
| Use of AI assistant disclosed | README AI-assistance section | Documented honestly |
| 3–5 example conversations | Five captured demo examples | Executed offline, visibly marked non-LLM |
| Public Git repository | Prepared GitHub-safe source only; original internal data excluded | **Requires publication** |
| Progressive Git history | Local staged source history may be provided with archive | Verify after publication |
| Respond to e-mail / Google Forms | Recruiter delivery procedure | **Requires candidate action / approval** |
