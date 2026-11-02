# Apple Pay and Google Pay

Two web paths show wallets:

- **Express Checkout**: `ExpressCheckoutElement` inside a `Checkout` handle. Whop prices the variant and charges it; no server code.
- **Payment request**: `whop.payments.paymentRequest`, the wallet sheet behind your own button, for a total you compute. Your server charges the token.

Both need the page's domain to have Apple Pay ready. One ready domain clears both Apple Pay and Google Pay for every element on that page. Whop-hosted checkout pages and whop.com are already approved.

## Register your domain

1. Download `https://whop.com/.well-known/apple-platform-integrator/apple-developer-merchantid-domain-association` and serve it unmodified, over HTTPS and without auth, at `https://<your-domain>/.well-known/apple-developer-merchantid-domain-association`. On Vercel you can rewrite that path to the whop.com URL instead.
2. Register the domain. The API key needs `domain:manage`.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const domain = await whop.domains.create({
  account_id: "biz_xxxxxxxxxxxxx",
  domain: "shop.example.com",
  apple_pay: {},
});

console.log(domain.apple_pay?.state);
```

The state starts `pending`. Retrieve the domain until `apple_pay.state` is `ready`, or `action_required` when Apple couldn't fetch the file; after fixing the file, call `whop.domains.check({ id: domain.id })`. If the account already has the domain, update it with `apple_pay: {}`. The Domains API replaces the deprecated Payment Method Domains API.

## Express Checkout

```tsx
import { Checkout, ExpressCheckoutElement, WhopElements } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function BuyNow() {
  return (
    <WhopElements elements={loadWhop()}>
      <Checkout plan="plan_xxxxxxxxxxxxx" metadata={{ order_id: "order_123" }} returnUrl="https://example.com/checkout/return">
        <ExpressCheckoutElement layout="horizontal" wallets={["apple_pay", "google_pay"]} />
      </Checkout>
    </WhopElements>
  );
}
```

It renders only the wallets the device can pay with, and nothing when none can, so keep a regular checkout on the page. Don't mount `CheckoutElement` on the same handle at the same time. The payment's `payment_method_type` is `apple_pay` or `google_pay`.

## Payment request

In the browser (`whop` from `useWhop()`):

1. `whop.payments.paymentRequest.create({ accountId, currency: "usd", amount: 1000, lineItems: [{ label, amount: 1000 }] })`. **Amounts are minor units**: `1000` is $10.00.
2. Await `canMakePayment()` ahead of time; it returns `{ applePay, googlePay }`. Render a button only for a wallet that came back `true`, using Apple's and Google's button artwork.
3. In the press handler, call `show("apple_pay")` or `show("google_pay")` **before any `await`**; Apple refuses a sheet opened outside the user gesture. It resolves `{ ctok, type, payer }`, or rejects with `payment_request_cancelled` when dismissed.
4. Post `ctok` and your order reference to your server. The sheet's checkmark appears when the token mints, before you charge, so show your server's result.

On the server, charge what the sheet showed. `1000` minor units on the sheet is `initial_price: 10` (major units) here:

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function charge(ctok: string, orderId: string) {
  const payment = await whop.payments.create(
    {
      account_id: "biz_xxxxxxxxxxxxx",
      variant: { currency: "usd", initial_price: 10, billing_type: "one_time" },
      confirmation_token: ctok,
      return_url: "https://example.com/checkout/return",
      metadata: { order_id: orderId },
    },
    { idempotencyKey: randomUUID() },
  );
  return { id: payment.id, status: payment.status, client_secret: payment.client_secret };
}
```

An inline `variant` finds or creates a variant for that price; pass `variant_id` when it already exists. If the status isn't `paid`, the browser calls `handleNextAction({ clientSecret })`. For physical goods, set `requestShipping`, answer changes with `updateWith`, and pass the address as `shipping_address`.

## Testing

Test in production on a real device: Safari on an Apple device for Apple Pay, not a simulator. The sandbox supports cards only. In Framer, load the Elements script through Custom Code in the site header; the Embed component's `srcdoc` iframe blocks Apple Pay in Safari.

## Sources

- https://docs.whop.com/payments/apple-pay.md
- https://docs.whop.com/developer/guides/express-checkout.md
- https://docs.whop.com/developer/guides/payment-request.md
- https://docs.whop.com/elements/latest/checkout/expressCheckout.md
- https://docs.whop.com/elements/latest/payments/paymentRequest.md
- https://docs.whop.com/developer/guides/sandbox.md
- https://docs.whop.com/developer/api/versioning.md
