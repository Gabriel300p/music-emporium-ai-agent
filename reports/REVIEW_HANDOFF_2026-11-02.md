# Engineering handoff — current state (2026-11-02)

This is a **working record for follow-up review**, not a second project README. The public-facing explanation is in the [root README](../README.md) and the [engineering journey](../docs/AI_ASSISTED_ENGINEERING_CASE_STUDY.md).

## Implemented and available

- Python CLI with direct Responses API function-call contracts and four read-only tools.
- CSV lookup logic for catalogue, promotions, order status and customer relation checks.
- PDF policy retrieval, basic grounding instructions and bounded tool loop.
- Public-safe case dataset with original non-personal catalogue rows, de-identified order/customer fields and a **synthetic one-page** policy fixture.
- Five deterministic example transcripts and repeatable offline tests.
- Architecture/decision notes, security limitations and a fixed scenario evaluation plan.

## Verification recorded locally

- 31 tests passed with original files available in a private ignored directory.
- Public-only: 18 passed, 13 skipped because the private source data was not present.
- No real hosted-model evaluation, clean online dependency installation, customer deployment or production metrics have been established.

## Open engineering gates

1. Re-run setup and tests on a clean machine or VS Code workspace.
2. Perform an authorized, bounded live evaluation of tool selection and answer grounding.
3. Examine failures and decide whether retrieval, orchestration or data-layer changes are justified.
4. Replace the minimal order verification with stronger authentication before any production use.
5. Confirm candidate understanding and sign-off for material architecture decisions before changes.

## Attribution and source handling

The first implementation was generated with ChatGPT assistance, and subsequent work included explicit human-led review direction and test/decision documentation. The separate Pandora project informed the approach conceptually; no Pandora runtime or code was integrated. Original private customer data and the restricted manual remain outside the Git repository.

**Submission is separate:** the candidate must review the final artifact and comply with the recruiter-provided delivery instructions. Do not change the repository after the stated submission cut-off.
