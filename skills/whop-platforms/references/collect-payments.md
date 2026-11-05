# Collecting payments for subaccounts

Two models. Pick per product, not per platform.

|  | Direct charge | Collect then transfer |
|---|---|---|
| Where the charge lands | The subaccount | The platform |
| Whop fees | Subaccount | Platform |
| Refunds and disputes | Subaccount | Platform (merchant of record) |
| Your cut | `application_fee_amount`, fixed per unit | Whatever you don't transfer |
| Use when | The seller should own the sale | Your backend decides how much and when each seller is paid |

## Direct charge with an application fee

Create the checkout configuration with the subaccount's `account_id` and an inline `variant`. Whop charges the buyer on the subaccount and pays your platform the fee.

```ts
import { WhopClient } from "@whop/sdk";
import type { Whop } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const variant: Whop.CreateCheckoutConfigurationsRequest.Variant & { application_fee_amount: number } = {
  currency: "usd",
  billing_type: "one_time",
  initial_price: 10.0,
  application_fee_amount: 1.23,
};

const checkout = await whop.checkoutConfigurations.create({
  account_id: "biz_xxxxxxxxxxxxx",
  variant,
  metadata: { order_id: "order_12345" },
});

console.log(checkout.purchase_url);
```

`initial_price: 10.0` is $10.00; the platform collects $1.23 and the subaccount receives $8.77 before its Whop fees.

`application_fee_amount`:

- A fixed amount **per unit**, in the variant's currency, in major units (`5.00` is $5.00).
- Must be positive and below the initial price (one-time) or renewal price (recurring).
- Applies to later payments on recurring variants too.
- Collection is capped to what is left of the proceeds; it can't exceed the captured amount.
- Only valid on a subaccount that has a parent, so the checkout must be created on the seller's `biz_`, not your own.

A percentage fee is your arithmetic: for 10% of a $49.00 price send `4.90`. Round to the currency's minor unit.

`@whop/sdk` 2.7.0's `Variant` type doesn't list `application_fee_amount`, though the API accepts it on the inline variant. Widen the type as above rather than casting the whole request to `any`. Always send `currency`.

The payment's `application_fee` object (`amount`, `amount_captured`, `amount_refunded`, `currency`) shows what you collected. Application fees also appear as `application_fee` lines in `financialActivity.list`.

## Collect on the platform, then transfer

1. Sell on your own account with a normal checkout (`whop-checkout`).
2. After the order settles, move the seller's share with `transfers.create({ type: "balance", origin_id, destination_id, amount, currency }, { idempotencyKey })`. `amount` is in dollars in the transfer currency. Full workflow in `whop-payouts`.

Before transferring:

- The origin (your platform) must be KYC-verified and hold enough balance in that currency.
- The destination must already exist as a Whop account; onboard it first.
- Transfers fail when the origin isn't verified, the balance is too low, or the destination can't receive funds yet. Fix the cause before retrying.

## Platform-wide fee settings

`accounts.fees.update({ account_id, ... })` changes an account's fee schedule. `child_markups` sets default markups for subaccounts (available on accounts without a parent), `markups` sets them on one subaccount, and `covered_payout_fees` chooses which payout fees the platform covers for its subaccounts. Read the current schedule with `accounts.fees.retrieve` before changing it, and confirm the change with the user: it affects every future payment.

## Sources

- https://docs.whop.com/developer/platforms/collect-payments-for-subaccounts.md
- https://docs.whop.com/api-reference/checkout-configurations/create-checkout-configuration.md
- https://docs.whop.com/api-reference/beta/transfers/create-transfer.md
- https://docs.whop.com/developer/platforms/enroll-subaccounts.md
