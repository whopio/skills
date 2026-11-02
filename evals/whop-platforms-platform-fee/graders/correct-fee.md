---
type: llm
focus: { source: file, path: server/create-checkout.ts }
---

PASS if all of these hold in the file:
- It creates the checkout with `checkoutConfigurations.create` on the seller's connected account (`account_id` set to the seller's `biz_` ID), with an inline variant whose `initial_price` is the price in dollars (not cents) and `billing_type` is `"one_time"`.
- It sets `application_fee_amount` on that variant to a dollar amount equal to 10% of the price (for example `priceUsd * 0.1`, rounded to cents), not the number `10` and not a fraction like `0.1`.
- It returns the response's `purchase_url`.

FAIL if it collects on the platform's own account and transfers later, sends the fee as a percentage or in cents, uses `company_id`, or creates a plan with a separate plans API call.
