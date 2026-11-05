# Moving from another processor

How to find the payment code in an existing codebase and map each piece to the Whop object that plays the same role. The Whop side of every row comes from Whop's docs; for anything a row doesn't cover, fetch the docs page it names rather than assuming the other processor's behavior carries over.

## 1. Scan the codebase

Run these from the repo root and keep the output; it is your migration checklist.

```bash
# SDKs and client libraries in dependency files
rg -n -i -g '!node_modules' -g '!*.lock' -e 'stripe' -e 'braintree' -e 'paypal' -e 'adyen' -e 'square' -e 'paddle' -e 'lemonsqueezy' -e 'chargebee' -e 'recurly' \
  package.json requirements*.txt pyproject.toml Gemfile go.mod composer.json 2>/dev/null

# Every file that imports or calls a processor
rg -l -i -g '!node_modules' -e 'from ["'"'"']stripe' -e 'require\(["'"'"']stripe' -e '@stripe/' -e 'import stripe' -e 'Stripe::' -e 'braintree' -e 'paypal' -e 'adyen' -e 'paddle'

# Webhook endpoints and signature checks
rg -n -i -g '!node_modules' -e 'webhook' -e 'signature' -e 'constructEvent' -e 'endpoint_secret' -e 'whsec_'

# Stored processor IDs in schemas and migrations
rg -n -i -g '!node_modules' -e 'customer_id' -e 'subscription_id' -e 'price_id' -e 'payment_intent' -e 'checkout_session' -e 'connected_account' -e 'payout'

# Money units: amounts stored or sent in cents
rg -n -i -g '!node_modules' -e 'cents' -e 'amount_in_cents' -e '\* *100' -e '/ *100'
```

For each hit, note what it does (sells, charges, stores a customer, grants access, refunds, pays someone out) and whether it is server or client code. That list drives step 2.

## 2. Map each piece to Whop

| What the code does today | Whop object | Whop call or event |
|---|---|---|
| Defines something to sell | Product (`prod_`) | `products.create({ title, ... })` |
| Defines a price, one-time or recurring | Variant (`plan_`): `billing_type` `one_time` or `renewal`, `billing_period` in days, prices in dollars | `variants.create`, or an inline `variant` on a checkout configuration |
| Creates a hosted checkout session and redirects | Checkout configuration (`ch_`), which returns `purchase_url` | `checkoutConfigurations.create({ variant \| variant_id, metadata, redirect_url })` |
| Embeds a checkout or card form on your page | Checkout element, payment elements, express checkout | `whop-checkout` |
| Attaches your order ID to a payment | `metadata` on the checkout configuration, copied to the payment and membership | Read `data.metadata` in the `payment.succeeded` webhook |
| Stores a customer record | Member (`mber_`), a user (`user_`) seen as your customer | `members.list({ query })` or `members.list({ user_ids })` |
| Tracks a subscription or paid access | Membership (`mem_`) with a `status` | `memberships.list`, `users.checkAccess({ id, resource_id })` |
| Cancels a subscription | Membership cancel | `memberships.cancel({ id, cancel_at_period_end: true })` keeps access until renewal; omit it to revoke now |
| Sends customers to a billing portal | `manage_url` on the membership | Retrieve the membership |
| Saves a card without charging | Setup intent, or a checkout configuration with `mode: "setup"` | `whop-checkout` |
| Charges a saved card later | Payment with a member and payment method | `payments.create({ member_id, payment_method_id, ... })` (`off_session: true` when the buyer isn't present) |
| Looks up a charge | Payment (`pay_`). "Charge" is the card network's word; the API object is the payment | `payments.retrieve`, `payments.list` |
| Issues a refund | Refund on a payment | `payments.refund({ id, partial_amount })`, amount in the payment's currency, dollars |
| Handles chargebacks | Dispute | `whop-billing` |
| Verifies webhook signatures | Standard Webhooks signature, verified with `unwrapWebhook` from `@whop/sdk/helpers` | `whop-webhooks` |
| Fulfills on "payment succeeded" / "checkout completed" | `payment.succeeded` | Fulfill from the webhook, never from the browser redirect |
| Reacts to a subscription starting or renewing | `membership.activated` | |
| Reacts to a subscription ending or changing | `membership.updated` | `previous_attributes.status` holds the status it left |
| Recovers a failed renewal | `payment.failed` | Send the buyer `recovery_url` when present |
| Tracks refunds and disputes | `refund.created`, `refund.updated`, `dispute.created`, `dispute.updated` | |
| Onboards sellers and splits payments | Subaccounts | `whop-platforms` |
| Moves money between balances or to a bank | Transfers, payouts | `whop-payouts` |
| Uses test-mode keys | The sandbox environment, separate keys and dashboard | `environment: WhopEnvironment.Sandbox` |
| Pins an API version | `Api-Version-Date` header (the SDK sends it) | `whop-api` |
| Sends idempotency keys | `Idempotency-Key` header on `POST` | `{ idempotencyKey }` request option |

## 3. Store Whop IDs beside the old ones

Add columns for the Whop IDs you will read back (`mem_`, `mber_`, `user_`, `pay_`, `plan_`) rather than reusing the old processor's columns. Keep the old IDs and the old webhook handler until the subscriber migration below is reconciled.

## 4. Move existing subscribers

Don't recreate subscribers by charging them again on Whop. Whop's dashboard has a Stripe migration at **Settings → Payments → Migrations → Stripe**:

- Preview the customers, amounts and renewal dates before confirming, and follow the payment-method transfer instructions it shows (including inviting the unique Whop email with the Data migration specialist role).
- Eligible subscriptions are active or trialing, paid by card, have a customer email, and charge at least $1. Link, ACH and SEPA payments are excluded.
- Whop sets migrated Stripe subscriptions to cancel at the end of the current period, and Whop handles future renewals and billing communications.
- When it finishes, reconcile the result report with your plan and give each exception an owner.
- Moving subscriptions doesn't move processing statements or historical ads data.

The pages this skill was written from describe only the Stripe migration. For another processor, check the current docs or ask Whop before building your own import.

## Sources

- https://docs.whop.com/developer/concepts.md
- https://docs.whop.com/developer/quickstart.md
- https://docs.whop.com/developer/guides/accept-payments.md
- https://docs.whop.com/developer/guides/memberships.md
- https://docs.whop.com/developer/guides/save-payment-methods.md
- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/payments-and-billing/manage-billing/billing-portal.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
- https://docs.whop.com/partners.md
