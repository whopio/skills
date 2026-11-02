# Save a payment method and charge it later

Two ways to save a method:

| | Save without charging | Save while charging |
|---|---|---|
| How | Payment elements in `mode="setup"` + `setupIntents.create`, or a `mode: "setup"` checkout configuration | Payment elements with `setupFutureUsage="off_session"` + `payments.create` |
| Webhook | `setup_intent.succeeded` | `payment.succeeded` (its `payment_method_id` is the saved method) |

Saved methods are `payt_...` IDs that belong to a member (`mber_...`).

## Save with a setup intent

Browser: mount `<Payments accountId="biz_xxxxxxxxxxxxx" mode="setup" currency="usd" returnUrl="https://example.com/billing/saved">` with `EmailElement`, `PaymentElement` and `BrandingElement`, then `createConfirmationToken({})`. A token from a payment-mode form is refused by setup intents.

Server:

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function save(confirmationToken: string, customerId: string) {
  const setupIntent = await whop.setupIntents.create(
    {
      account_id: "biz_xxxxxxxxxxxxx",
      confirmation_token: confirmationToken,
      currency: "usd",
      return_url: "https://example.com/billing/saved",
      metadata: { customer_id: customerId },
    },
    { idempotencyKey: randomUUID() },
  );
  return { id: setupIntent.id, status: setupIntent.status, client_secret: setupIntent.client_secret };
}
```

Statuses: `succeeded` (method saved, `payment_method_id` set), `requires_action` (browser runs `handleNextAction({ clientSecret })`), `processing` (saving in the background; wait for the webhook), `canceled` (read `last_setup_error`). The `setup_intent.succeeded` webhook carries `payment_method_id`, `payment_instrument` and your `metadata`; webhooks pinned before `2026-09-22-1` carry `payment_method.id` instead.

## Save with a hosted page

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const config = await whop.checkoutConfigurations.create({
  account_id: "biz_xxxxxxxxxxxxx",
  mode: "setup",
  redirect_url: "https://example.com/billing/saved",
  metadata: { customer_id: "user_123_in_your_db" },
});

console.log(config.purchase_url);
```

Redirect to `purchase_url`, or mount `<Checkout checkoutConfiguration={config.id}>` with a `CheckoutElement`. Nothing is charged; the redirect carries `setup_intent_id`.

## Charge a saved method

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const methods = await whop.paymentMethods.list({ member_id: "mber_xxxxxxxxxxxxx" });
const method = methods.data[0];

const payment = await whop.payments.create(
  {
    account_id: "biz_xxxxxxxxxxxxx",
    variant_id: "plan_xxxxxxxxxxxxx",
    member_id: "mber_xxxxxxxxxxxxx",
    payment_method_id: method.id,
    off_session: true,
  },
  { idempotencyKey: "renewal-order_123" },
);

console.log(payment.id, payment.status);
```

- The response is the payment as opened; the result arrives as `payment.succeeded` or `payment.failed`.
- **`off_session`**: pass `true` when the buyer isn't there (renewals on your schedule). Since `2026-10-07-1`, a saved-method charge with a `return_url` and no `off_session` treats the buyer as present, so an issuer challenge leaves it `requires_action`.
- `line_items` mixes items; each takes exactly one of `variant_id` or an inline `variant` (`initial_price` in major units). `promo_code_id` applies one of your promo codes.
- Creating a variant inline needs `plan:create` as well as `payment:charge`.
- Use a stable idempotency key per charge (for example your order ID) so a retry never charges twice.

## Save while charging

Pass `setupFutureUsage="off_session"` on the `Payments` handle; the elements show the save consent. Create the payment with the confirmation token as usual. `payment_method_id` is set on the payment and on `payment.succeeded` once the charge completes, and stays `null` when nothing was saved.

## Raw card details

If you already hold card numbers and are PCI-compliant, `payments.direct.create` charges them and `setupIntents.direct.create` saves them. It's enabled per account (ask your Whop contact; a 404 means it isn't), requests go to the vault host (`vault-api.whop.com`, sandbox `sandbox-vault-api.whop.com`) which the SDK picks for you, so don't set a custom base URL. Renewal variants need `setup_future_usage: "off_session"`, and `off_session: true` needs a `network_transaction_id`. Fetch `https://docs.whop.com/developer/guides/card-details.md` before building it.

## Sources

- https://docs.whop.com/developer/guides/save-payment-methods.md
- https://docs.whop.com/developer/guides/card-details.md
- https://docs.whop.com/developer/api/idempotency.md
- https://docs.whop.com/developer/api/versioning.md
- https://docs.whop.com/elements/latest/payments/overview.md
