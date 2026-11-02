---
type: llm
---

PASS if all of these hold:
- The server code either creates an account link with `use_case: "payouts_portal"` for the seller's `biz_` account, or mints an access token with `accessTokens.create` that sets an explicit `scoped_actions` list for that account.
- It identifies the account with `account_id`, not `company_id`.
- The Whop API key is used only on the server, and the answer says the page either redirects the seller to the link's `url` or mounts Wallet elements (such as `BalanceElement` / `WithdrawElement`) with the token.

FAIL if it sends the API key to the browser, mints a token without `scoped_actions`, invents a use case other than `account_onboarding` or `payouts_portal`, or builds its own withdraw form that calls `payouts.create` from the page.
