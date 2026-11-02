---
type: llm
---

PASS if all of these hold:
- Checkout Sessions are replaced by a Whop checkout configuration (`checkoutConfigurations.create` / `POST /checkout_configurations`), sending the buyer to its `purchase_url` or an embedded Whop checkout, with prices in dollars rather than cents.
- Fulfillment moves to a verified Whop webhook: `payment.succeeded` (or `membership.activated`) to turn access on, and `membership.updated` (or checking the membership's status) to turn it off, verified on the raw body with the `ws_` webhook secret, for example via `unwrapWebhook`. The answer doesn't fulfill from the browser redirect.
- Existing subscribers move with Whop's Stripe migration in the dashboard (Settings → Payments → Migrations → Stripe), not by asking customers to buy again or by charging them on Whop while Stripe still bills them.

FAIL if any of these is missing, if it invents Whop event names that copy Stripe's (such as `checkout.session.completed` or `customer.subscription.deleted` on Whop), or if it puts the Whop API key in browser code.
