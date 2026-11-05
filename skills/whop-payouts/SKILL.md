---
name: whop-payouts
description: >-
  Move money out of Whop balances: transfers between balances, payouts to bank
  or PayPal, payout methods, the payout portal (Wallet element or hosted link),
  deposits, settlement currency, ledgers, balances and stats. Use when: "pay my
  sellers", "send money to a subaccount", "send money to a connected account",
  "create a payout", "withdraw to bank", "PayPal payouts", "embed a payout
  portal", "let users manage their payouts", "top up my balance", "show balance
  and activity", "reconcile payouts". NOT for: onboarding or KYC
  (whop-platforms), charging buyers (whop-checkout), refunds (whop-billing),
  moving from Stripe Connect (whop-migrate).
license: Apache-2.0
metadata:
  author: whop
  version: "0.4.0"
---

# Whop Payouts

Money leaves a Whop balance two ways: a **transfer** moves it to another Whop balance (a user or subaccount), and a **payout** sends it from a balance to an external destination such as a bank account or PayPal.

## Before you start

1. **Inspect the project first.** Note the installed `@whop/sdk` version (`node_modules/@whop/sdk/package.json`; `whop-sdk` in Python, `whop_sdk` in Ruby), the framework, and whether the client targets sandbox or production. On `@whop/api` or `@whop/sdk` below 2.0, upgrade first (`whop-migrate`). If a name here doesn't compile, search the installed `node_modules/@whop/sdk/reference.md` for it and trust that over this skill.
2. Fetch `https://docs.whop.com/developer/platforms/manual-payouts.md` and `https://docs.whop.com/developer/payouts/overview.md`. If they disagree with this skill, follow the docs and tell the user (see [references/skill-feedback.md](references/skill-feedback.md)). Read the changelog (`https://docs.whop.com/developer/api/versioning.md`) only when you pin or upgrade a version, or a response doesn't match this skill or the docs.
3. Set up the client with `whop-api`. Without that skill: install `@whop/sdk` and create `new WhopClient({ token: process.env.WHOP_API_KEY, environment: WhopEnvironment.Sandbox })` in server-only code, dropping `environment` for production (`https://docs.whop.com/developer/quickstart.md`). Money calls use an **Account API key**, which is a secret: keep it on your server. Browsers get a short-lived access token instead (see [references/payout-portal.md](references/payout-portal.md)).
4. Build and test against sandbox first: `https://sandbox-api.whop.com/api/v1`, or `environment: WhopEnvironment.Sandbox` on the client.
5. Know who you are paying. A recipient needs a Whop account (a subaccount or a user) before a transfer, and a completed verification plus a payout method before a payout. Creating and verifying subaccounts is `whop-platforms`.
6. Other `whop-*` skills named here are optional. When one isn't installed, use the matching guide linked from `https://docs.whop.com/developer/start.md` instead.

## Rules

1. **Amounts are major currency units.** `amount: 50` is $50.00, not 50 cents, on `transfers.create`, `payouts.create`, `payouts.createQuote` and `deposits.create`. Responses return payout amounts as decimal strings (`"125.5"`).
2. **Confirm before moving money.** Before running code that creates a transfer, payout or deposit with a live key, show the person the amount, currency, origin and destination and get an explicit yes. A duplicated payout or transfer sends real money twice.
3. **Send an idempotency key on every money `POST`.** Pass `{ idempotencyKey }` as the second argument; the SDK sends it as `Idempotency-Key`. Generate it once per operation, store it with your order, and reuse it only to retry that same request. The SDK itself retries `408`, `429` and `5xx` twice by default, so a request without a key can run twice.
4. **A key is bound to its request for 24 hours.** Same key and same body replays the original response (errors included, with `Idempotent-Replayed: true`). Same key with a different body is a `400` `idempotency_key_mismatch`. A retry while the first is still running is a `409` `idempotency_request_in_progress`.
5. **Transfers are asynchronous.** A balance transfer can come back `processing` and settle to `succeeded` or `failed` within seconds. Listen for `transfer.completed` and `transfer.failed` (or retrieve the transfer); don't treat the create response as final.
6. **Balances are per currency.** A payout draws only from the balance in its `currency`. Pass the currency the funds arrived in (`cad` for CAD funds); when omitted, Whop uses `usd` if it covers the payout, otherwise the only other funded currency.
7. **Payout fees come out of the amount.** `amount` is the gross; the recipient gets `net_amount`. Quote every payout first: it shows fees and arrival, and its `quote_token` is required to create the payout. Set `platform_covers_fees: true` to charge the fee to your platform instead; it only works for subaccounts of a platform whose fee policy covers that payout method, or a caller allowed to manage subaccount fees.
8. **Use current names:** `transfers` (not top-ups or withdrawals), `payouts.create`, `deposits.create`, `account_id` with a `biz_` ID. `payout_method_id` is a `potk_` ID; a supported method type is a `podst_` ID.

## Pick a path

| Goal | Do this |
|---|---|
| Pay a seller or user from your platform balance (stays on Whop) | [Transfer between balances](#transfer-between-balances) |
| Send an account's balance to its bank or PayPal | [Create a payout](#create-a-payout) |
| Let sellers add payout methods and withdraw on their own | [Let accounts manage their own payouts](#let-accounts-manage-their-own-payouts) |
| Add a payout method through the API, or PayPal login | [references/payout-methods.md](references/payout-methods.md) |
| Fund your platform balance before paying out | [Add funds](#add-funds) |
| A link anyone can redeem for money | `transfers.create` with `type: "claim_link"` |
| Show balances, activity, revenue; reconcile; settle in one currency | [references/balances-and-reporting.md](references/balances-and-reporting.md) |
| Create subaccounts, onboarding, KYC | `whop-platforms` |

## Transfer between balances

A transfer debits `origin_id` and credits `destination_id`. Both accept a user (`user_`), account (`biz_`) or ledger account (`ldgr_`) ID. The origin must be verified and hold enough balance; the destination must already exist.

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const idempotencyKey = randomUUID();

const transfer = await whop.transfers.create(
  {
    type: "balance",
    origin_id: "biz_yyyyyyyyyyyyy",
    destination_id: "biz_xxxxxxxxxxxxx",
    amount: 50.0,
    currency: "usd",
    metadata: { order_id: "order_12345" },
  },
  { idempotencyKey },
);

if (transfer.object === "transfer") {
  console.log(transfer.id, transfer.status);
}
```

`amount: 50.0` is $50.00. `type`, `origin_id`, `destination_id`, `amount` and `currency` are all required. The API key needs `payout:transfer_funds`. Store `idempotencyKey` before the call so a crash-and-retry reuses it. A transfer that fails because the origin is unverified, short on balance, or the destination can't receive yet must be fixed before retrying; don't loop on it.

## Create a payout

Find the account's default payout method, quote the payout so the person sees the fee and arrival, then create it with the quote and an idempotency key:

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const methods = await whop.payouts.methods.list({ account_id: "biz_xxxxxxxxxxxxx" });
const method = methods.data.find((m) => m.is_default);
if (!method) throw new Error("The account has no default payout method");

const quote = await whop.payouts.createQuote({
  account_id: "biz_xxxxxxxxxxxxx",
  payout_method_id: method.id,
  amount: 100.0,
  currency: "usd",
});
console.log(quote.fee, quote.net_amount);

const payout = await whop.payouts.create(
  {
    account_id: "biz_xxxxxxxxxxxxx",
    payout_method_id: method.id,
    amount: 100.0,
    currency: "usd",
    quote_token: quote.quote_token,
  },
  { idempotencyKey: randomUUID() },
);
console.log(payout.id, payout.status);
```

- `amount: 100.0` is $100.00 gross; the fee comes out of it unless the platform covers it.
- No payout method yet? Let the account add one in the Withdraw element or the hosted portal, or create one through the API ([references/payout-methods.md](references/payout-methods.md)).
- Always send `quote_token`, created with the same owner, method, amount, currency and speed. From API version `2026-11-03` it is required on every payout; before that (including `@whop/sdk` 2.7.0, which sends `2026-10-28`) only accounts with quote enforcement require it, so sending it always works on both. A missing, mismatched or expired quote returns `400` `invalid_payout_quote`. To retry an uncertain payout, resend the original `quote_token` and `Idempotency-Key`: the existing payout is recovered even after the quote expires.
- Add `speed: "instant"` only when the method supports it; an ineligible instant payout is rejected.
- Track it with the `payout.created`, `payout.updated` and `payout.reversed` webhooks (`whop-webhooks`) or `payouts.retrieve`. `status` is one of `requested`, `in_review`, `processing`, `completed`, `reversed`, `canceled`, `failed`, `denied`; `failure` explains the last four.
- To cancel, check `cancelable` on the payout, then call `payouts.cancel({ id, account_id })`. `id` takes the `wdrl_` payout ID or the `cofr_` request ID that `payouts.create` returned.

## Let accounts manage their own payouts

Two options, both covered in [references/payout-portal.md](references/payout-portal.md):

- **Embedded**: mount the Wallet elements (`BalanceElement`, `WithdrawElement`, `ActivityElement`) in your app with an access token your server mints for the subaccount. `WithdrawElement` lists payout methods, collects a new one, and creates the payout when the user confirms.
- **Hosted**: create an account link with `use_case: "payouts_portal"` and redirect. It covers payouts, payout methods and identity verification.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const link = await whop.accountLinks.create({
  account_id: "biz_xxxxxxxxxxxxx",
  use_case: "payouts_portal",
  return_url: "https://yourapp.com/payouts/complete",
  refresh_url: "https://yourapp.com/payouts/refresh",
});

console.log(link.url);
```

`account_id` is the subaccount (or your own account) the user manages. Both URLs must start with `https://`. The only use cases are `payouts_portal` and `account_onboarding` (identity verification only, see `whop-platforms`).

## Add funds

Charge a saved payment method of your account into your balance. Save one first with a dashboard top up or a setup intent whose `owner_id` is your account.

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const deposit = await whop.deposits.create(
  {
    destination: "biz_xxxxxxxxxxxxx",
    amount: 1000.0,
    payment_method_id: "payt_xxxxxxxxxxxxx",
  },
  { idempotencyKey: randomUUID() },
);

console.log(deposit.methods.card?.payment_id);
```

`amount: 1000.0` is $1,000.00 USD. This needs the `payment:charge` scope and a `biz_` destination; a declined charge fails with `400`. Confirm the result with the `payment.succeeded` / `payment.failed` webhooks for that `payment_id`. Without `payment_method_id`, `deposits.create` charges nothing and returns the ways to fund the account instead: a hosted deposit page, bank transfer details and crypto addresses (crypto has a $10 minimum).

## With the Whop MCP server

The `whop` MCP tools act on the signed-in user's **live** account and can't reach sandbox (`whop-api` covers connecting, `intent`/`intent_id`, and prepare-and-confirm). Its `docs_search` and `docs_query` read the docs pages this skill links. Use the tools to fill in and debug the code, not to replace it:

- Read-only through MCP: `payouts_list`, `payouts_get`, `transfers_list`, `transfers_get`, `ledger-accounts_get`, `payout-methods_list`, `accounts_fees_get`.
- Creating payouts, transfers and deposits isn't available on the plugin's MCP connection. Write that code with the SDK and run it with the user's API key, after confirming the amount, currency and destination (Rule 2). Don't look for a workaround.

## Verify

1. Run every flow against sandbox with a sandbox API key.
2. Create a transfer, then confirm `transfer.completed` arrives (or `transfers.retrieve` shows `succeeded`) and the destination's balance moved in `financialActivity.list`.
3. Re-run the same transfer with the same `idempotencyKey` and confirm the response carries `Idempotent-Replayed: true` and no second transfer appears.
4. Quote and create a payout to a sandbox payout method; watch `status` move with `payout.updated`.
5. Mount the payout portal with a scoped token and check balance, withdraw and activity all load.

When you're done, tell the user what changed, which environment it targets (sandbox or production; if that isn't decided yet, say so and recommend sandbox first), which of these checks you ran, and what is still unverified.

## Errors

If the same call fails twice, stop retrying it. Read the whole error (status, body and request ID), check the docs page and the installed SDK types, then change the request or the approach.

| Symptom | Cause | Fix |
|---|---|---|
| `400` `idempotency_key_mismatch` | Reused a key with a different body | New operation, new key |
| `409` `idempotency_request_in_progress` | Retried while the first request runs | Wait, retry with the same key |
| Payout refused for amount | More than the available balance in that currency | Check the balance for that `currency` before paying out |
| `invalid_payout_quote` | No quote, a quote for different payout details, or an expired quote | Call `payouts.createQuote` with the same details and pass its `quote_token` |
| `platform_covers_fees` rejected | Not a subaccount, or the fee policy doesn't cover the method | Omit it, or update the platform's covered payout fees |
| Transfer `failed` | Origin unverified or short on balance, or destination can't receive | Fix the cause first; read `failure_reason` |
| Transfer `403` | API key lacks `payout:transfer_funds` | Add the scope to the key |
| Amount 100x too large | Sent cents | Send dollars: `50.0` is $50.00 |
| Wallet elements blank or `403` | Token missing scopes, or expired (1 hour default) | Mint with the scopes in [references/payout-portal.md](references/payout-portal.md); refresh before expiry |

More cases in [references/payout-methods.md](references/payout-methods.md) and [references/balances-and-reporting.md](references/balances-and-reporting.md).

## References

- [references/payout-methods.md](references/payout-methods.md): read when an account has no payout method, you need required bank fields, or you want PayPal login.
- [references/payout-portal.md](references/payout-portal.md): read when embedding the Wallet elements or redirecting to the hosted payouts portal.
- [references/balances-and-reporting.md](references/balances-and-reporting.md): read when showing balances, building a statement, reconciling, charting revenue, setting a settlement currency, or touching swaps and cards.
- [references/skill-feedback.md](references/skill-feedback.md): read when the user says this skill gave wrong, outdated or missing guidance, or the docs contradicted it during the task.
