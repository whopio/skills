# Invoices

An invoice is a numbered bill for one or more of your variants, addressed to one customer. Its ID is `pay_...` (it's a payment). Native invoices need `Api-Version-Date: 2026-10-24` or later; the current SDK sends a newer date by default. An older date reaches the legacy invoice API, which works differently.

Lifecycle: **create a draft** (charges nothing, emails no one), then **issue** (final tax, status `open`, `payment.created` fires) or **send** (issues and emails in one call). The customer pays through the hosted checkout, or Whop charges a saved method.

## Draft fields

| Field | Notes |
|---|---|
| `account_id` | Required |
| `items` | 1 to 50, each `{ variant_id, quantity? }` or an inline `{ variant: { product_id, billing_type, initial_price, currency }, quantity? }` (prices in major units). Inline variants need `plan:create` |
| `member_id` or `email_address` (+ `customer_name`) | The customer; one of the pair. Optional on a draft, required to issue. From API version `2026-11-02-1`, once a draft has a customer, updating it with a different `member_id` (or `null`) returns `400`: void the draft and create a new invoice to bill someone else |
| `billing_address` or `mailing_address_id` | `billing_address` is `{ line1, city, postal_code, country (ISO alpha-2), state?, line2?, name?, phone? }`. Needed to issue when tax applies |
| `due_at` | ISO 8601. Sets `overdue` and reminder dates |
| `payment_method_id` | A saved `payt_` of the customer, charged off session on issue or send |
| `recipient_emails` | Up to 50 extra addresses; defaults to the customer's email. Empty means Whop emails nobody |
| `buyer_fee_percentage` | 0 to 100, two decimals; returned as `buyer_fee_amount` |
| `metadata` | Up to 50 string pairs, copied onto the membership and the charge |

Item rules: buy-now variants of your account only (installment plans refused), each variant once (use `quantity`), quantity above 1 only for variants allowing multiple quantities. The draft keeps each variant's price from when you saved the items.

## Getting paid

| | Saved method | Hosted checkout |
|---|---|---|
| Customer present | No (off session) | Yes |
| You need | `payment_method_id` on the draft | The issued invoice's `checkout_link` |
| 3D Secure | Can't complete a challenge | Customer completes it |
| Your payment rules | `block` and `allow` apply | All four actions apply |

- A saved method is charged at the `charge_at` you pass to `issue` or `send`, else on `due_at` while it's ahead, else right away. `scheduled_charge_at` shows a pending charge. The response doesn't say whether the charge succeeded.
- A declined charge leaves the invoice `open`; Whop emails the pay link to the recipients so the customer can pay through checkout.
- `checkout_link` is `pay_xxx.<signature>`, set only while `open`. Build the URL as `https://whop.com/checkout/<id>/?token=<encoded part after the first ".">`. Only the invoice's customer can pay through it; they can't add a promo code.

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const issued = await whop.invoices.issue({ id: "pay_xxxxxxxxxxxxx" }, { idempotencyKey: randomUUID() });

if (issued.checkout_link) {
  const token = issued.checkout_link.slice(issued.checkout_link.indexOf(".") + 1);
  console.log(`https://whop.com/checkout/${issued.id}/?token=${encodeURIComponent(token)}`);
}
```

## Send, schedule, remind

- `invoices.send({ id })` emails it (issuing a draft first). Each invoice can be emailed 3 times in 24 hours; a fourth is `429 invoice_send_limit_reached`.
- `invoices.send({ id, send_at })` schedules a draft (future time); editing is locked until it sends or you call `invoices.unschedule({ id })`.
- Sending an invoice with a `due_at` schedules reminders 3, 7, 14, 30 and 60 days after it, while it stays `open`.

## Statuses

`draft` (editable, estimated totals), `open` (issued, final totals), `paid`, `uncollectible`, `void`. `status` can also show a payment state such as `pending` mid-payment. `invoices.void({ id })` cancels a draft, open or uncollectible invoice; `invoices.markUncollectible({ id })` works only on `open`.

## Subscriptions

A recurring variant on an invoice starts a subscription when the invoice is paid. The invoice bills the first period at the renewal price (the variant's trial and initial fee don't apply; add a setup fee as a one-time item). Recurring items have quantity 1 and must belong to a product. Renewals charge the method that paid the invoice.

## Fulfillment

Save the invoice's `id` with your order, then fulfill on the `payment.succeeded` webhook whose `data.id` matches (`whop-webhooks`). Native invoices don't send `invoice.*` events. Renewals have their own `pay_` IDs.

## Permissions

Every write (create, update, issue, send, unschedule, void, mark uncollectible) needs `payment:charge`; every read needs `payment:basic:read`. Some fields come back `null` without their own permission: `member:basic:read` (`member_id`, `customer_name`), `member:email:read` (`email_address`, `recipient_emails`), `payment:charge` (`checkout_link`). The legacy `invoice:*` permissions don't apply.

## Sources

- https://docs.whop.com/developer/guides/invoices.md
- https://docs.whop.com/developer/api/versioning.md
- https://docs.whop.com/developer/api/idempotency.md
