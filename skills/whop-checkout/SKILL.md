---
name: whop-checkout
description: >-
  Take payments with Whop: create products and variants (one-time or
  recurring), share a checkout link or checkout configuration, embed the
  Checkout element or Express Checkout with @whop/elements-react, build a form
  with payment elements and card fields, add Apple Pay or Google Pay, save a
  payment method and charge it later, add promo codes and tax IDs, test with
  sandbox cards, and sell from iOS or React Native. Use when: "Whop checkout", "accept payments", "create a
  subscription price", "checkout link", "embed checkout in my page", "Apple Pay
  button", "save a card and charge later", "Whop paywall in my iOS app",
  "test card". Chain with: whop-webhooks to fulfill once the payment succeeds,
  whop-billing for memberships, refunds and invoices after the sale, whop-api
  for client setup. NOT for: cancelling or checking a subscription (use
  whop-billing), connected accounts or charging on behalf of sellers (use
  whop-platforms), apps inside Whop (use whop-apps), moving from Stripe (use
  whop-migrate).
license: Apache-2.0
metadata:
  author: whop
  version: "0.4.0"
---

# Whop Checkout

Whop prices everything through a **variant** (one price of a product). The buyer pays on a Whop-hosted page or in Whop Elements on your page, and your server fulfills when the `payment.succeeded` webhook arrives.

## Before you start

1. Fetch `https://docs.whop.com/developer/guides/accept-payments.md` and the changelog at `https://docs.whop.com/developer/api/versioning.md`, plus the guide for the path you pick below. If they disagree with this skill, follow the docs.
2. Confirm the environment. Sandbox (`https://sandbox-api.whop.com/api/v1`, dashboard at `sandbox.whop.com`) supports cards only: no Apple Pay, Google Pay, or Elements yet. Test cards are in [references/testing.md](references/testing.md).
3. Get the account ID (`biz_...`) and, for an existing price, the variant ID (`plan_...`; variant IDs keep the `plan_` prefix).
4. Server code needs an API key and a client. Set that up with `whop-api`.

## Rules

1. **The API key stays on your server.** Never put it in browser or app code. The Checkout element, Express Checkout and payment elements need no key on the page; the variant sets the price, so the browser never asserts an amount.
2. **Fulfill from the `payment.succeeded` webhook only** (`whop-webhooks`). Not from `onComplete`, not from the return page. `onComplete` fires again when a checkout is restored, and anyone can type `status=succeeded` into a URL.
3. **The return page branches on `status`.** Whop appends `payment` (or `setup`) and `status` (`succeeded`, `failed`, `canceled`, or `processing`) to `returnUrl` whatever the outcome. `returnUrl` must be `https` (`http` only on localhost).
4. **API amounts are major units, Elements amounts are minor units.** `initial_price: 29` and `renewal_price: 29` mean $29.00. `amount: 1000` on a `Payments` handle or a payment request means $10.00.
5. **On a recurring variant, `initial_price` is a setup fee.** Without a trial, checkout charges `initial_price` plus the first `renewal_price`; during a free trial it charges `initial_price` alone. For a plain $29/month subscription set `renewal_price: 29`, `initial_price: 0`. `formatted_price` shows only the renewal price, so a setup fee won't appear in it.
6. **Use current names:** `billing_type` (`one_time` or `renewal`), `variants`, `variant_id`, `account_id`. `billing_period` is in days (30 monthly, 365 yearly). The Elements prop that takes a variant ID is still called `plan`.
7. **Send an `Idempotency-Key` on any call that moves money** (`payments.create`, `setupIntents.create`). In the SDK, pass `{ idempotencyKey }` as the second argument. A key is kept 24 hours; reusing it with a different body returns `400 idempotency_key_mismatch`.
8. **Element options are fixed at mount.** To change the variant or quantity, remount. `CheckoutElement` and `ExpressCheckoutElement` can't share one `Checkout` handle at the same time.

## Pick a path

| You want | Use | Server code to charge | Guide |
|---|---|---|---|
| A link to share, fastest setup | `purchase_url` from a variant or checkout configuration | No | `payments/create-checkout-link` |
| Whop's whole checkout inside your page | `Checkout` + `CheckoutElement` | No | `developer/guides/embed-checkout` |
| One-press Apple Pay / Google Pay for a variant | `Checkout` + `ExpressCheckoutElement` | No | `developer/guides/express-checkout` |
| Your own form design | `Payments` + `PaymentElement` or `CardFields`, then `payments.create` | Yes | `developer/guides/payment-elements` |
| The wallet sheet behind your own button, cart total you compute | `payments.paymentRequest`, then `payments.create` | Yes | `developer/guides/payment-request` |
| Raw card numbers you already hold (PCI scope) | `payments.direct.create` (enabled per account) | Yes | `developer/guides/card-details` |
| Native iOS paywall | `WhopCheckout` Swift package | No | `developer/guides/ios/build-a-paywall` |
| React Native or SwiftUI payment form | `@whop/elements-react-native` / `elements-swift` | Yes | `elements/latest/getting-started` |

Each guide is at `https://docs.whop.com/<path>.md`. Element details are in [references/elements.md](references/elements.md), wallets in [references/wallets.md](references/wallets.md), mobile in [references/mobile.md](references/mobile.md).

## Create a price and a checkout link

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const product = await whop.products.create({
  account_id: "biz_xxxxxxxxxxxxx",
  title: "Pro",
});

const variant = await whop.variants.create({
  account_id: "biz_xxxxxxxxxxxxx",
  product_id: product.id,
  billing_type: "renewal",
  billing_period: 30,
  renewal_price: 29,
  initial_price: 0,
  currency: "usd",
});

const checkout = await whop.checkoutConfigurations.create({
  account_id: "biz_xxxxxxxxxxxxx",
  variant_id: variant.id,
  metadata: { customer_id: "user_123_in_your_db" },
  redirect_url: "https://example.com/billing/return",
});

console.log(variant.purchase_url, checkout.purchase_url);
```

`renewal_price` and `initial_price` are dollars (major units of `currency`), not cents. A one-time price is `billing_type: "one_time"` with `initial_price` set and no `billing_period`. `variant.purchase_url` alone is a working link; a checkout configuration (`ch_...`) adds `metadata` that Whop copies to the payment, the membership and their webhooks, plus a `redirect_url`, an `affiliate_code`, or `mode: "setup"`. You can skip the variant call and pass an inline `variant: { billing_type, initial_price, renewal_price, billing_period, currency, product_id }` to `checkoutConfigurations.create`.

Promo codes and buyer tax IDs are in [references/products-and-promos.md](references/products-and-promos.md).

## Embed the Checkout element (React)

```bash
npm install @whop/elements-react @whop/elements
```

```tsx
import { Checkout, CheckoutElement, WhopElements } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function CheckoutPage({ orderId }: { orderId: string }) {
  return (
    <WhopElements elements={loadWhop()}>
      <Checkout
        plan="plan_xxxxxxxxxxxxx"
        metadata={{ order_id: orderId }}
        returnUrl={`https://example.com/checkout/return?order=${orderId}`}
        onComplete={(completion) => {
          if (completion.result === "payment") console.log("analytics only", completion.paymentId);
        }}
      >
        <CheckoutElement />
      </Checkout>
    </WhopElements>
  );
}
```

Needs React 19. Pass `checkoutConfiguration="ch_..."` instead of `plan` to keep presets out of client code, or `promoCode`, `affiliateCode`, `attribution` on the handle. For Express Checkout swap in `<ExpressCheckoutElement wallets={["apple_pay", "google_pay"]} />`; it renders nothing when no wallet is available, so keep a regular checkout on the page. Wallets need your domain registered for Apple Pay ([references/wallets.md](references/wallets.md)). Without React, load `https://cdn.whop.com/elements/amber/elements.js` and mount with `window.WhopElements().checkout.create({...}).create("checkout").mount("#checkout")`. Allow `frame-src https://cdn.whop.com` and `connect-src https://api.whop.com` in your CSP.

## Payment elements: your form, your server charges

The browser creates a single-use confirmation token (`ctok_...`); your server turns it into a payment.

```tsx
import { BrandingElement, EmailElement, PaymentElement, Payments, WhopElements, usePayments, useWhop } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function Page() {
  return (
    <WhopElements elements={loadWhop()}>
      <Payments accountId="biz_xxxxxxxxxxxxx" plan="plan_xxxxxxxxxxxxx" returnUrl="https://example.com/checkout/return">
        <PayForm />
      </Payments>
    </WhopElements>
  );
}

function PayForm() {
  const payments = usePayments();
  const whop = useWhop();
  async function pay() {
    if (!payments || !whop) return;
    const { confirmationToken } = await payments.createConfirmationToken({});
    const payment = await (await fetch("/api/pay", { method: "POST", body: JSON.stringify({ confirmationToken }) })).json();
    if (payment.status !== "paid") await whop.payments.handleNextAction({ clientSecret: payment.client_secret });
  }
  return (<><EmailElement /><PaymentElement /><BrandingElement /><button onClick={pay}>Pay</button></>);
}
```

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function POST(request: Request): Promise<Response> {
  const { confirmationToken } = await request.json();
  const payment = await whop.payments.create(
    {
      account_id: "biz_xxxxxxxxxxxxx",
      variant_id: "plan_xxxxxxxxxxxxx",
      confirmation_token: confirmationToken,
      return_url: "https://example.com/checkout/return",
      metadata: { order_id: "order_123" },
    },
    { idempotencyKey: randomUUID() },
  );
  return Response.json({ id: payment.id, status: payment.status, client_secret: payment.client_secret });
}
```

`BrandingElement` is required; the other payment elements stay loading without it. `client_secret` is safe to send to the browser; the API key never is. `handleNextAction` returns `{ redirected, status, lastPaymentError }`: a dismissed 3DS dialog leaves `requires_action` with no error, so a missing error never means success. Generate the idempotency key once per order and reuse it on retries. Card fields and the full option list are in [references/elements.md](references/elements.md).

## Save a payment method and charge it later

Mount `<Payments mode="setup" currency="usd">`, create a token, then `setupIntents.create({ account_id, confirmation_token, currency: "usd" })` on the server. Later, charge with `payments.create({ account_id, variant_id, member_id, payment_method_id, off_session: true })`. Full flow, statuses and the hosted alternative are in [references/saved-methods.md](references/saved-methods.md).

## With the Whop MCP server

The `whop` MCP tools act on the signed-in user's **live** account and can't reach sandbox (`whop-api` covers connecting, `intent`/`intent_id`, and prepare-and-confirm). Its `docs_search` and `docs_query` read the docs pages this skill links. Use the tools to fill in and debug the code, not to replace it:

- Get the IDs the checkout needs: `products_list` and `variants_list` (pass `account_id`), `checkout-configurations_list`.
- Debug a live payment: `payments_get`, `payments_status`, `payments_fees`.
- Create a product or variant with `products_create` / `variants_create` only when the user wants it in their live account. App code still references or creates them with the SDK, tested in sandbox.
- `payments_create`, `payments_refund`, `payments_void` and `setup-intents_create` are prepare-and-confirm tools that touch real money: show the preview and wait for the user's yes.

## Verify

1. In sandbox, open the variant's `purchase_url`, pay with `4242 4242 4242 4242` (any future expiry, any CVC), and confirm your `payment.succeeded` handler ran once.
2. Repeat with `4000 0000 0000 0002` and confirm nothing was fulfilled.
3. Use `5385 3083 6013 5181` (enter `Checkout1!`) to exercise 3DS.
4. Elements and wallets have no sandbox yet: test embedded checkout, the return page, Express Checkout and Apple Pay in production, on a real device in Safari for Apple Pay.

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| Buyer charged $58 for a $29/month plan, or charged $29 at the start of a "free" trial | `initial_price: 29` on a recurring variant is a setup fee | Set `initial_price: 0` |
| Price is 100× too high | Cents passed to an API price field | API prices are major units: `29`, not `2900` |
| Payment elements stay loading | No `BrandingElement` | Mount `BrandingElement` inside `Payments` |
| Express Checkout renders nothing | No wallet on the device, or domain not ready for Apple Pay | Keep a regular checkout; register the domain ([references/wallets.md](references/wallets.md)) |
| `payment.status` is `requires_action` | The issuer wants 3DS | Call `handleNextAction` with `client_secret` |
| `400 idempotency_key_mismatch` | Same key, different body | One key per distinct request |
| Variant created with the wrong billing model | Old pre-variant field name used | Use `billing_type` (`one_time` or `renewal`) |
| 404 on `payments.direct.create` | Card details not enabled on the account | Ask your Whop contact |

More in [references/troubleshooting.md](references/troubleshooting.md).

## References

- [references/elements.md](references/elements.md): read when configuring the Checkout handle, Payments handle, card fields, or the script-tag setup.
- [references/wallets.md](references/wallets.md): read when adding Apple Pay or Google Pay, Express Checkout, or a payment request.
- [references/saved-methods.md](references/saved-methods.md): read when saving a card for later, charging a saved method, or charging raw card details.
- [references/products-and-promos.md](references/products-and-promos.md): read when creating variants, promo codes, or handling tax IDs.
- [references/mobile.md](references/mobile.md): read when selling from an iOS or React Native app.
- [references/testing.md](references/testing.md): read when testing in sandbox.
- [references/troubleshooting.md](references/troubleshooting.md): read when a checkout or charge fails.
