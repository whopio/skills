# Refunds, disputes and dispute alerts

## Refunds

Refund through the payment, not the refunds resource. Needs `payment:manage`.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const full = await whop.payments.refund({ id: "pay_xxxxxxxxxxxxx" }, { idempotencyKey: "refund-pay_xxxxxxxxxxxxx" });

const partial = await whop.payments.refund(
  { id: "pay_yyyyyyyyyyyyy", partial_amount: 5 },
  { idempotencyKey: "refund-pay_yyyyyyyyyyyyy-5" },
);

console.log(full.refunded_amount, partial.refunded_amount);

const refunds = await whop.refunds.list({ account_id: "biz_xxxxxxxxxxxxx", payment_id: "pay_xxxxxxxxxxxxx" });
for await (const refund of refunds) console.log(refund.id);
```

- `partial_amount` is in the payment's currency, major units (`5` = 5.00 USD). Omit it for a full refund.
- The response is the payment, with `refunded_amount`. The membership updates automatically.
- Refunds go back through the original processor. Events: `refund.created`, `refund.updated`.
- Read a refund with `refunds.retrieve({ id })` (`ref_...`); reading needs `payment:basic:read`.
- A disputed payment can't be refunded: the call fails with "This payment has been disputed. Therefore, it cannot be refunded."

## Disputes

A dispute (chargeback, `dspt_...`) opens when the buyer's bank challenges a payment. Events: `dispute.created` (response window starts) and `dispute.updated` (status changes).

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const dispute = await whop.disputes.retrieve({ id: "dspt_xxxxxxxxxxxxx" });

if (dispute.evidence_editable) {
  await whop.disputes.update({
    id: dispute.id,
    evidence: {
      customer_name: "Jane Doe",
      customer_email_address: "jane@example.com",
      product_description: "Annual subscription to Acme Pro, purchased 2026-01-15.",
      service_date: "2026-01-15",
      refund_policy_disclosure: "Customer agreed to the no-refunds policy at checkout.",
      notes: "Customer used the product 47 times across 8 sessions before disputing.",
    },
  });
  await whop.disputes.submit({ id: dispute.id });
}
```

- Stage evidence with `update` as often as you like; `submit` sends it to the processor and locks it. Submit before `evidence_due_at`.
- Evidence fields: `customer_name`, `customer_email_address`, `product_description`, `service_date` (ISO 8601), `billing_address`, `customer_communication_attachment`, `cancellation_policy_attachment` / `cancellation_policy_disclosure`, `refund_policy_attachment` / `refund_policy_disclosure`, `refund_refusal_explanation`, `access_activity_log`, `uncategorized_attachment`, `notes`. Attachment fields take an uploaded file as `{ id: file.id }`; upload it first with the Files API.
- To concede instead, `disputes.accept({ id })` works only while `acceptable` is `true` (a chargeback still awaiting a response, before `evidence_due_at`, on a processor that supports it; inquiries never are).
- A dispute's `amount` is in whole units of its `currency`.
- Permissions: `payment:dispute:read` to read, `payment:dispute` to update or submit.

### Statuses

| Status | Meaning |
|---|---|
| `warning_needs_response` | Pre-dispute alert open; you can preempt it with a refund or response |
| `warning_under_review` | You responded to the alert; the processor is deciding |
| `warning_closed` | Alert resolved without a dispute |
| `needs_response` | Formal dispute; submit evidence before the window closes |
| `under_review` | Evidence submitted; the processor is deciding |
| `won` | Funds stay with you |
| `lost` | Funds go back to the buyer; Whop reverses the payment. No refund record is created and you can't create one |
| `prevented` | The customer was refunded before any ruling (Visa RDR or an earlier refund). Settles like `lost` |

## Dispute alerts

A dispute alert (`dspa_...`, event `dispute_alert.created`) is an issuer's early warning about a settled payment, before any chargeback. Not every alert becomes a dispute.

| `type` | Meaning |
|---|---|
| `early_fraud_warning` | Fraud report |
| `dispute_alert` | Pre-dispute notice |
| `rapid_dispute_resolution` | Visa RDR case the network already closed by refunding |

`category` is `fraud` (the cardholder says they didn't pay) or `customer_dispute` (they paid but dispute it), or `null`. `auto_refunded` says whether the payment was refunded automatically. `amount` is in whole units of `currency`. List with `disputeAlerts.list({ account_id, payment_id?, type? })`.

While an alert is at `warning_needs_response` you can preempt it with a refund or a response before it escalates. Once a payment is disputed, refunds are refused.

## Sources

- https://docs.whop.com/developer/guides/refunds-and-disputes.md
- https://docs.whop.com/api-reference/beta/disputes/dispute.md
- https://docs.whop.com/api-reference/beta/dispute-alerts/dispute-alert.md
- https://docs.whop.com/api-reference/beta/refunds/refund.md
- https://docs.whop.com/developer/api/versioning.md
- https://docs.whop.com/developer/guides/manage-fraud.md
