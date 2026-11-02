---
name: whop-billing
description: >-
  Run Whop billing after the sale: check on the server whether a user has
  access, read and list memberships and members, cancel at period end or
  immediately, pause, resume and extend subscriptions, store membership
  metadata, validate license keys, create and send invoices or charge them to a
  saved method, refund payments, respond to disputes and dispute alerts, and
  write fraud rules. Use when: "check if user has access", "only paying members
  can see this", "cancel subscription at end of period", "pause a membership",
  "refund a Whop payment", "respond to a chargeback", "send an invoice",
  "block risky payments". Chain with: whop-webhooks to react to membership,
  payment and dispute events, whop-checkout for the purchase itself, whop-api
  for client setup. NOT for: creating prices or checkout pages (use
  whop-checkout), verifying webhook signatures (use whop-webhooks), paying out
  sellers (use whop-payouts), access inside a Whop app iframe (use whop-apps).
license: Apache-2.0
metadata:
  author: whop
  version: "0.2.0"
---

# Whop Billing

Checkout creates a **membership** linking a user to a product. Your server asks Whop whether a user has access, changes memberships when customers cancel or pause, and handles invoices, refunds, disputes and fraud rules on the payments behind them.

## Before you start

1. Fetch `https://docs.whop.com/developer/guides/memberships.md` (plus `invoices.md`, `refunds-and-disputes.md` or `manage-fraud.md` under `https://docs.whop.com/developer/guides/` for those tasks) and the changelog at `https://docs.whop.com/developer/api/versioning.md`. If they disagree with this skill, follow the docs.
2. Know how you identify the customer: a Whop user ID (`user_...`) stored on your user record, a membership ID (`mem_...`) or license key, or a member ID (`mber_...`).
3. Get the account ID (`biz_...`) and the product ID (`prod_...`) you gate on.
4. Every call here runs on your server with an API key. Set that up with `whop-api`.

## Rules

1. **Check access on the server, every time.** Call `users.checkAccess` from server code and return `403` when `has_access` is `false`. Never trust a flag the browser sends, and never ship the API key in client or downloadable code.
2. **Ask Whop rather than mirroring billing state.** `checkAccess` follows renewals, cancellations and refunds. If you must decide from a membership, `active`, `trialing` and `completed` (one-time purchases) grant access; `past_due` is the grace period after a failed payment; `canceled` and `expired` don't.
3. **Pass `cancel_at_period_end: true` explicitly to cancel at period end.** Omitting it, or `false`, revokes access immediately; immediate is the default.
4. **Losing access arrives as `membership.updated`** with `previous_attributes.status`, not a deactivation event. Pause, resume and extend don't change status, so no status event fires; retrieve the membership to confirm. Handle events with `whop-webhooks`.
5. **Send an `Idempotency-Key` when money moves**: refunds, invoice issue and send, payment capture. In the SDK, pass `{ idempotencyKey }` as the second argument.
6. **Amounts are major units.** `partial_amount: 5` refunds 5.00 in the payment's currency; a dispute's `amount` is in whole units of its currency.
7. **Use current names:** `variant_id`, `account_id`, `items[].variant_id` on invoices. The SDK sends a current `Api-Version-Date`, which native invoices require (`2026-10-24` or later).

## Pick a task

| Goal | Call | Permission |
|---|---|---|
| Gate a route or feature | `users.checkAccess({ id, resource_id })` | |
| Read a subscription | `memberships.retrieve({ id })` / `memberships.list({ account_id, user_id })` | |
| Cancel | `memberships.cancel({ id, cancel_at_period_end: true })` | |
| Undo a pending cancel | `memberships.update({ id, cancel_at_period_end: false })` | |
| Pause / resume / comp days | `memberships.pause`, `resume`, `extend({ id, days })` | |
| Bill a custom amount or a quote | `invoices.create` then `invoices.send` | `payment:charge` |
| Refund | `payments.refund({ id, partial_amount? })` | `payment:manage` |
| Fight a chargeback | `disputes.update({ id, evidence })` then `disputes.submit({ id })` | `payment:dispute` |
| Block or review risky payments | `paymentRules.create` | `payment:manage` |

## Protect a route

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

async function currentWhopUserId(request: Request): Promise<string | null> {
  return request.headers.get("x-demo-user-id");
}

export async function GET(request: Request): Promise<Response> {
  const whopUserId = await currentWhopUserId(request);
  if (!whopUserId) return new Response("Unauthorized", { status: 401 });

  const access = await whop.users.checkAccess({
    id: whopUserId,
    resource_id: "prod_xxxxxxxxxxxxx",
  });
  if (!access.has_access) return new Response("Forbidden", { status: 403 });

  return Response.json({ premium: true });
}
```

Replace `currentWhopUserId` with your own session lookup; the header stands in for it. `resource_id` is a product (`prod_`), an account (`biz_`) or an experience (`exp_`). `access_level` is `customer`, `admin` (a team member of the account) or `no_access`; gate dashboard views on `admin`.

To get the Whop user ID onto your user record, put your own user ID in checkout `metadata` (`whop-checkout`), then on `membership.activated` save `data.user_id` against `data.metadata.customer_id`. That event also fires on renewals, so make the write repeatable. License keys for downloadable software are in [references/memberships.md](references/memberships.md).

## Cancel, pause, extend

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.memberships.cancel({
  id: "mem_xxxxxxxxxxxxx",
  cancel_at_period_end: true,
  reason: "Requested by customer",
});

await whop.memberships.update({ id: "mem_xxxxxxxxxxxxx", cancel_at_period_end: false });

await whop.memberships.pause({ id: "mem_xxxxxxxxxxxxx", until: "2026-12-01T00:00:00Z" });
await whop.memberships.resume({ id: "mem_xxxxxxxxxxxxx" });

await whop.memberships.extend({ id: "mem_xxxxxxxxxxxxx", days: 14 });

await whop.memberships.update({ id: "mem_xxxxxxxxxxxxx", metadata: { tier: "gold" } });
```

- Period-end cancel sets `cancel_at_period_end: true`; the customer keeps access until `current_period_end`, then `membership.updated` fires with the status it left.
- Pausing stops renewals; `until` (future, ISO 8601) resumes automatically, and only works for memberships Whop bills.
- `extend` pushes the next renewal by `days` (1 to 1095).
- `metadata` merges into the existing metadata; pass `{}` to clear it.
- Customers can manage billing themselves at `https://whop.com/@me/settings/orders`; each membership also has a `manage_url`.

Statuses, listing filters and members are in [references/memberships.md](references/memberships.md).

## Invoices

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const draft = await whop.invoices.create(
  {
    account_id: "biz_xxxxxxxxxxxxx",
    email_address: "dana@example.com",
    customer_name: "Dana Lee",
    items: [{ variant_id: "plan_xxxxxxxxxxxxx", quantity: 2 }],
    due_at: "2026-11-30T17:00:00Z",
    billing_address: { line1: "123 Main St", city: "New York", state: "NY", postal_code: "10001", country: "US" },
    metadata: { order_id: "ord_1042" },
  },
  { idempotencyKey: randomUUID() },
);

const sent = await whop.invoices.send({ id: draft.id }, { idempotencyKey: randomUUID() });
console.log(sent.id, sent.status);
```

A draft charges nothing. `send` issues it (final tax, status `open`) and emails it; `issue` opens it without emailing. Put a saved `payment_method_id` on the draft to charge it off session instead of emailing. Invoice IDs are `pay_...`: fulfill from `payment.succeeded` for that ID; native invoices don't send `invoice.*` events. Details in [references/invoices.md](references/invoices.md).

## Refunds and disputes

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.payments.refund({ id: "pay_xxxxxxxxxxxxx", partial_amount: 5 }, { idempotencyKey: "refund-pay_xxxxxxxxxxxxx-1" });

await whop.disputes.update({
  id: "dspt_xxxxxxxxxxxxx",
  evidence: {
    product_description: "Annual subscription to Acme Pro, purchased 2026-01-15.",
    access_activity_log: "Customer logged in 47 times across 8 sessions before disputing.",
  },
});
await whop.disputes.submit({ id: "dspt_xxxxxxxxxxxxx" });
```

Omit `partial_amount` for a full refund. A disputed payment can't be refunded, and a lost dispute creates no refund record. Evidence can be staged repeatedly until `submit`, which locks it; submit before `evidence_due_at`. Alerts, statuses and fraud rules are in [references/disputes.md](references/disputes.md) and [references/fraud.md](references/fraud.md).

## Verify

1. Call your protected route with a user who has an active membership (`200`) and one without (`403`).
2. In sandbox, buy with test card `4242 4242 4242 4242`, cancel with `cancel_at_period_end: true`, and confirm the membership still grants access with `cancel_at_period_end` set.
3. Refund a sandbox payment and confirm `refunded_amount` and the `refund.created` webhook.
4. Create an invoice, send it, and pay the emailed link with a test card; confirm `payment.succeeded` for its `pay_` ID.

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| Customer lost access right away after "cancel" | `cancel_at_period_end` omitted, so the cancel was immediate | Pass `cancel_at_period_end: true` whenever you mean period end |
| `has_access` false for a paying user | Wrong `resource_id`, or a user ID from another environment | Use the `prod_` you sell; sandbox and production IDs differ |
| No webhook after pause or extend | Status didn't change | Retrieve the membership |
| Refund rejected: "This payment has been disputed" | Payment has a dispute | Respond to the dispute instead |
| `429 invoice_send_limit_reached` | Fourth send in 24 hours | Wait, or share the checkout link yourself |
| Invoice calls behave like the legacy API | `Api-Version-Date` older than `2026-10-24` | Use the current SDK; don't pin an older date |
| `400 idempotency_key_mismatch` | Same key, different request | One key per distinct request |

More in [references/troubleshooting.md](references/troubleshooting.md).

## References

- [references/memberships.md](references/memberships.md): read when listing memberships or members, interpreting statuses, or validating license keys.
- [references/invoices.md](references/invoices.md): read when billing with invoices, scheduling sends, or invoicing a subscription.
- [references/disputes.md](references/disputes.md): read when handling refunds, disputes, evidence, or dispute alerts.
- [references/fraud.md](references/fraud.md): read when writing payment rules or reviewing held payments.
- [references/troubleshooting.md](references/troubleshooting.md): read when a billing call fails or access looks wrong.
