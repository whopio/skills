# Fraud rules

Payment rules add your own conditions on top of Whop's fraud controls. They run after Whop's controls and never loosen them. A fraudulent payment costs the money plus a $15 dispute fee.

## Actions

| `action` | What happens | Precedence |
|---|---|---|
| `allow` | Skips your other rules (never Whop's controls) | Beats all three |
| `block` | Declined before authorization; the buyer sees a generic decline | Beats `review`, `enforce_3ds` |
| `review` | Eligible card authorized without capture; auto-captured 48 hours later unless you act | Beats `enforce_3ds` |
| `enforce_3ds` | Buyer confirms with their bank through 3D Secure | Lowest |

Where you're unsure, challenge (`enforce_3ds`) rather than block; a block also turns away real buyers.

## Create a rule

Needs `payment:manage` (reading needs `payment:basic:read`).

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const rule = await whop.paymentRules.create({
  account_id: "biz_xxxxxxxxxxxxx",
  name: "Review large orders from abroad",
  action: "review",
  conditions: {
    all: [
      { field: "amount_in_usd", operator: "gte", value: 250 },
      { field: "card_country", operator: "neq", value: "US" },
    ],
  },
});

console.log(rule.id);
```

- Conditions are ANDed under `all`. Documented fields: `risk_score`, `amount_in_usd` (major units: `250` = $250), `card_country`, `card_bin` (first six digits), `customer_email`, `ip_address`. The List Fields endpoint returns the operators and values each field accepts.
- Operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `starts_with`, `contains`, `ends_with`, `in_cidr`.
- A rule's action and conditions are fixed once created. To change them, `paymentRules.replace({ id, action, conditions })` deletes the old rule and creates a successor with a new ID that keeps its name, `metadata` and active state.
- Pause with `paymentRules.deactivate({ id })`, resume with `activate`, retire with `delete` (it stays readable with `status: "deleted"`).

## Reviewed payments

A `review` hold reads `status: "authorized"`, `substatus: "requires_capture"`, and sends `payment.authorized`. The buyer gets access at authorization. Act within 48 hours or Whop captures automatically:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.payments.capture({ id: "pay_xxxxxxxxxxxxx" }, { idempotencyKey: "capture-pay_xxxxxxxxxxxxx" });
await whop.payments.void({ id: "pay_yyyyyyyyyyyyy" }, { idempotencyKey: "void-pay_yyyyyyyyyyyyy" });
```

- Capture makes it `paid` and sends `payment.succeeded` (fulfill then). Capture is all or nothing; refund afterwards to return part.
- Void releases the hold, revokes access, returns stock and sends `payment.canceled`.
- Only on-session cards can be held. Apple Pay, Google Pay, bank, balance and off-session payments (renewals, saved-method invoice charges) skip review; the match is still recorded.
- Payments created with `capture: false` keep their own schedule.

## Measure

Each payment lists the rules that matched in `payment_rule_matches`. Disputes on payments with no matches mean a rule is too narrow; a rule matching far more than you were losing is too broad. The Stats API metrics `payment_rule_matches` and `payment_rule_matched_volume` give totals over time.

## Sources

- https://docs.whop.com/developer/guides/manage-fraud.md
- https://docs.whop.com/api-reference/beta/payment-rules/payment-rule.md
- https://docs.whop.com/developer/guides/invoices.md
