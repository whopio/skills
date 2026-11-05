# Balances, activity, stats and settlement currency

Read-only calls for showing money and reconciling it, plus the one setting that changes which balance new sales land in.

## Balances

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const ledger = await whop.ledgerAccounts.retrieve({ id: "biz_xxxxxxxxxxxxx" });

for (const b of ledger.balances) {
  console.log(b.currency, b.balance, b.pending_balance, b.reserve_balance);
}
```

- `id` accepts a `biz_`, `user_` or `ldgr_` ID.
- There is one balance per currency. Balance amounts are numbers in major units.
- To react to balance changes instead of polling, subscribe to `ledger_account.funds_available` (see `whop-webhooks`).

## Financial activity (statement, reconciliation)

Every movement in or out of a balance: payments, payouts, refunds, transfers, deposits, swaps, card transactions. Each row has a typed `resource` and `source`.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

let cursor: string | undefined;
do {
  const page = await whop.financialActivity.list({
    account_id: "biz_xxxxxxxxxxxxx",
    currency: "usd",
    posted_after: "2026-10-01T00:00:00Z",
    cursor,
  });
  for (const row of page.data) {
    console.log(row.posted_at, row.line_type, row.amount, row.currency);
  }
  cursor = page.page_info.has_next_page ? page.page_info.end_cursor ?? undefined : undefined;
} while (cursor);
```

- `amount` is a decimal string in major units.
- Useful filters: `direction` (`money_in` / `money_out`), `payment_id` (a payment with its refunds, disputes and fees), `resource_id`, `withdrawal_id`, `posted_after` / `posted_before`, `exclude_internal_movements`, `include_resource: false` for a faster response.
- Some line types, such as `onchain_deposit`, only appear when you request them in `line_types`.
- `financialReports.retrieve` returns balance activity, an income statement or a balance summary over a date range.
- Reconcile a payout to its settled row with `payout_request_id` (`cofr_`, from `payouts.create`) against `GET /payouts`.

## Stats

Account revenue queries need the `stats:read` permission. List the metrics with `stats.timeSeries.list()`, then retrieve one:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const series = await whop.stats.timeSeries.retrieve({
  metric: "gross_revenue",
  account_id: "biz_xxxxxxxxxxxxx",
  from: "2026-08-01",
  to: "2026-08-31",
  interval: "day",
  convert_to: "usd",
});

for (const point of series.data.points) {
  console.log(point.timestamp, point.value);
}
```

- `timestamp` is Unix seconds. Read `value` in the metric's unit: `count`, `currency` (a decimal amount) or `percent` (already in percentage points, `1.6` is 1.6%).
- Use `data.totals` for whole-range figures when present; averaging daily rates or summing daily unique counts gives the wrong answer.
- Filter by passing a listed property (`payment_method: "card"`) and split with `breakdown_by`. Filtering or breaking down by `currency` reports original amounts without conversion.
- An unsupported property is a `400`; an unknown metric is a `404`.

## Preferred settlement currency

Settle every new sale into one of `usd`, `eur`, `gbp`, `cad`, `aud` instead of one balance per variant currency:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const preferences = await whop.accounts.preferences.update({
  account_id: "biz_xxxxxxxxxxxxx",
  preferred_settlement_currency: "usd",
});

console.log(preferences.preferred_settlement_currency_changeable_at);
```

- Send `null` to turn it off. It can change at most once a day (`preferred_settlement_currency_changeable_at`) and needs the `payout:account:update` scope.
- It only affects new sales; money already in a balance stays in its currency.
- Each converted sale costs 0.5%. Sales already in the chosen currency, App Store purchases, and sales that settle outside the Whop balance never convert. No 0.5% applies when the buyer paid in a currency other than the variant's (adaptive pricing already charged for it).
- Refunds use the rate stored on the payment; disputes use the rate on the day the dispute opens.
- On a platform, the setting applies only to the account that sets it. Application fees follow the platform's setting; the subaccount's share follows the subaccount's.
- On a payment, `total`, `subtotal`, `tax_amount`, `refunded_amount` and `amount_after_fees` are in the settlement currency (use them for balances and payouts). `presentment_total` and the other `presentment_*` fields are what the buyer paid; match orders on `presentment_total`.

## Swaps and cards

The API also converts balances (swaps: `swaps.createQuote`, then `swaps.create`, then `swaps.retrieve` until it completes) and issues virtual cards that spend from a balance (`cards.create`, `cards.list`). The Wallet element's `ConvertElement` and card surfaces cover the common UI. Fetch the API reference pages below before building on either; this skill doesn't cover them further.

## Sources

- https://docs.whop.com/developer/payouts/overview.md
- https://docs.whop.com/developer/payouts/preferred-settlement-currency.md
- https://docs.whop.com/developer/guides/stats.md
- https://docs.whop.com/api-reference/beta/ledgers/ledger-activity.md
- https://docs.whop.com/api-reference/ledger-accounts/ledger-account.md
- https://docs.whop.com/api-reference/beta/stats/stats.md
- https://docs.whop.com/api-reference/beta/swaps/swap.md
- https://docs.whop.com/api-reference/beta/cards/card.md
