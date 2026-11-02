# Whop Elements for checkout

Elements is Whop's embeddable UI (`@whop/elements` and `@whop/elements-react`, version 1.9.0 at the time of writing). Two handles take payments:

- **`Checkout`** runs Whop's whole checkout. Mount `CheckoutElement` or `ExpressCheckoutElement` in it. No server code.
- **`Payments`** owns a charge you confirm yourself. Mount `PaymentElement`, `CardElement` or `CardFields`, plus `EmailElement`, `AddressElement`, `TaxIdElement` and the required `BrandingElement`. Your server charges the confirmation token.

Both mount inside `WhopElements`.

## Setup

```bash
npm install @whop/elements-react @whop/elements
```

React 19 is required. Without React, add the script tag `<script src="https://cdn.whop.com/elements/amber/elements.js" data-whop-elements></script>` and call `window.WhopElements()`.

CSP: allow `frame-src https://cdn.whop.com` and `connect-src https://api.whop.com` (`sandbox-api.whop.com` for sandbox). `contentSecurityPolicy()` from `@whop/elements` returns every source you need.

`environment` is `"production"` (the default) or `"sandbox"`; the sandbox environment is not generally available yet. Never put an API key in browser code; the elements that need a token get it from your server.

## Checkout handle options

| Option | Notes |
|---|---|
| `plan` | Variant ID (`plan_...`). The prop keeps its old name |
| `quantity` | Units of `plan` |
| `items` | `[{ plan, quantity }]` for a cart |
| `checkoutConfiguration` | A `ch_...` you created on the server; keeps presets out of client code |
| `promoCode`, `affiliateCode` | Prefill a code |
| `attribution` | UTM fields, `trackingLinkId`, `funnelId`, `source` |
| `metadata` | Up to 40 string pairs; copied to the payment and every webhook about it |
| `returnUrl` | `https` page the buyer lands on after an off-site step (`http` allowed on localhost) |
| `onComplete` | Fires once per completion: `result` is `payment` (`paymentId`), `waitlist_entry` (`entryId`), or `setup` (`setupIntentId`). Analytics only |

Options can't change after mount; remount to change them. Mount `CheckoutElement` or `ExpressCheckoutElement`, never both at once on one handle.

A checkout configuration created with `mode: "setup"` saves a payment method instead of charging; the redirect carries `setup_intent_id`.

## Payments handle options

| Option | Notes |
|---|---|
| `accountId` | `biz_...` that receives the payment |
| `mode` | `payment` (default) or `setup` |
| `plan` | Variant ID; the price comes from the variant |
| `currency` + `amount` | Lowercase currency and **amount in minor units** (`1000` = $10.00). Pass this or `plan`, never both |
| `setupFutureUsage` | `off_session` or `on_session` to save the method while paying |
| `returnUrl` | Where off-site steps return |
| `paymentMethodConfiguration` | Restrict which methods show |

`createConfirmationToken({})` returns `{ confirmationToken }` (`ctok_...`), a single-use stand-in for the method. Card data never touches your page. Send it to your server and call `payments.create` with `confirmation_token`. If the payment isn't `paid`, call `whop.payments.handleNextAction({ clientSecret })` in the browser; it returns `{ redirected, status, lastPaymentError }`.

## Card fields

Split card inputs you lay out yourself:

```tsx
import { BrandingElement, CardCvcElement, CardExpiryElement, CardFields, CardNumberElement, Payments, WhopElements } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function CardForm() {
  return (
    <WhopElements elements={loadWhop()}>
      <Payments accountId="biz_xxxxxxxxxxxxx" plan="plan_xxxxxxxxxxxxx" returnUrl="https://example.com/checkout/return">
        <CardFields>
          <CardNumberElement />
          <CardExpiryElement />
          <CardCvcElement />
        </CardFields>
        <BrandingElement />
      </Payments>
    </WhopElements>
  );
}
```

In plain JS: `payments.create("cardFields")`, then `.create("cardNumber")`, `.create("cardExpiry")`, `.create("cardCvc")` on it. `CardElement` is the single-field version, with `layout` `stacked` or `compact`.

`BrandingElement` is required on every form that collects a payment: the payment, card and card-field elements stay loading until it mounts, and `createConfirmationToken` refuses without it.

## Return page

Whop appends `payment` (the `pay_` ID) and `status` to `returnUrl`, and keeps your own query parameters. Branch on `status`: `succeeded` gets a thank-you, `failed` or `canceled` gets "you weren't charged" and a link back, anything else (such as `processing`) gets "we'll confirm by email". Card declines show inline and never reach the return page. The page is display only; fulfillment comes from the webhook.

## Sources

- https://docs.whop.com/elements/latest/getting-started.md
- https://docs.whop.com/elements/latest/checkout/overview.md
- https://docs.whop.com/elements/latest/payments/overview.md
- https://docs.whop.com/elements/latest/payments/cardFields.md
- https://docs.whop.com/elements/latest/payments/card.md
- https://docs.whop.com/elements/latest/payments/branding.md
- https://docs.whop.com/developer/guides/embed-checkout.md
- https://docs.whop.com/developer/guides/payment-elements.md
