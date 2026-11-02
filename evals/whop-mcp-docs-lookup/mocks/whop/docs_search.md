Title: Webhooks
Page: developer/guides/webhooks
Link: https://docs.whop.com/developer/guides/webhooks
- **`api_version_date`** — the dated API version that sets the shape of `data` and of the envelope itself (for example, pins from `2026-08-14` carry `account_id` where older pins carry `company_id`). It operates the same as the `Api-Version-Date` header on REST reads. Set it when you create a webhook with the API. Then the payload shape stays stable when the API changes. Webhooks without a pin keep their initial payload and envelope shape. Exception: resources that exist only on the current API (cards, variants, transfers, swaps, deposits, exports) always receive the latest `data` shape — the envelope still follows the pin.

Title: Webhooks
Page: developer/guides/webhooks
Link: https://docs.whop.com/developer/guides/webhooks
The envelope follows your webhook's `api_version_date` pin, the same way `data` does. Webhooks pinned before `2026-08-14` — and webhooks without a pin — receive the account field as `company_id` instead of `account_id`.
