---
type: llm
---

PASS if the final answer says all of these:
- `api_version_date` pins the shape of the event payload (`data`) and of the envelope, so it stays stable when the API changes.
- Pins from `2026-08-14` carry `account_id`; older or unpinned webhooks get `company_id` instead.
- Leaving it out means the webhook keeps its initial payload shape.
- It links https://docs.whop.com/developer/guides/webhooks (no `.mdx` extension).

FAIL if any is missing or wrong, or if it presents a guess as the docs' answer.
