# Example interactions — pending real source data and live API validation

The source CSV files and store policy PDF were **not** part of the supplied assignment PDF. Therefore, this starter project intentionally does not claim to provide real sample interactions.

Once the original files are available and the agent is running with a configured LLM provider, generate the five examples using:

```bash
python scripts/record_examples.py --data-dir data --out-dir examples
```

Review the output, confirm that factual claims are grounded in the source, and remove or redact any sensitive personal data before making a GitHub repository public.

The final application must provide 3–5 real example conversations. The artificial test fixtures in `tests/fixtures/` are **not** valid as production source data.
