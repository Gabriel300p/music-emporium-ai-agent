# Security and data handling

1. `data/` is excluded from public Git history. The original policy PDF is explicitly marked as an internal document; customer rows contain identifying fields and must not be redistributed.
2. Demo files are independently generated 100% synthetic examples (`demo_data/`) with `example.test` addresses.
3. All business queries are read-only Python functions. The model cannot execute arbitrary SQL, Python, shell commands or file writes.
4. Order status requires matching both order number and purchase email in the provided CSV; wrong and unknown order/e-mail pairs return the same generic denial. This is **not production authentication**.
5. Only product information or verified order details are returned; tool traces log only the tool name and status. Customer personal names, e-mails and telephone numbers are never returned as order data.
6. Policy chunks are treated as lower-trust evidence; system instructions explicitly reject embedded instructions and prompt injections in source files.
7. The OpenAI API receives user messages and retrieved policy data. Deployments with real customer data require consent/legal basis, data-processing review, vendor controls and credential management.
8. The app does not persist conversations to disk and calls `responses.create(..., store=False)`; retention behavior may still depend on external provider policies and deployment choices.
9. Before publication, audit `git status`, `git ls-files`, example content and every commit for sensitive data or credentials. Do not push source CSVs/PDFs or `.env`.
10. Error and fallback paths must avoid inventing prices, discounts, return decisions or unsupported promises to customers.
