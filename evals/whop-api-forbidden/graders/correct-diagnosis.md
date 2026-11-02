---
type: llm
---

PASS if all of these hold:
- It says a `403` means the key is valid but isn't allowed to do this action (as opposed to a bad or missing key, which is `401`).
- It tells the developer to add the missing permission to the API key (for listing payments, a payment read permission such as `payment:basic:read`) in the dashboard, rather than to create a new key or change the auth header.
- It tells the developer to check that the account ID sent with the request (`account_id` / `biz_...`) belongs to the key's own business or one of its connected accounts.

FAIL if any of these is missing, if it says to retry the same request unchanged or with backoff, or if it suggests putting the key in client-side code.
