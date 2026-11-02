# Payout methods

A payout method (`potk_`) is a saved destination for one account or user: a bank account, PayPal, a wallet. Each one is an instance of a supported payout method (`podst_`), which defines the fields it needs for a country and currency.

The easiest way to collect one is to let the account holder do it in the Withdraw element or the hosted payouts portal (see `references/payout-portal.md`). Use the API below when you build your own form.

## List saved methods

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

for await (const method of await whop.payouts.methods.list({ account_id: "biz_xxxxxxxxxxxxx" })) {
  console.log(method.id, method.is_default, method.status);
}
```

- Pass `account_id` (`biz_`) or `user_id` (`user_`), not both.
- `status` is `created` (saved, never used), `active` (a payout through it succeeded) or `broken` (the last payout failed; the holder must fix it). A later successful payout returns it to `active`.
- Pass `amount` (major units, `250.00`) and `currency` to get a fee and arrival quote on each method. `include_limits: true` adds the per-speed payout limits and needs the `payout:withdrawal:read` scope.
- The manual payouts guide uses `payoutMethods.listPayoutMethod({ account_id })`, which lists the same methods from the older endpoint. In SDK 2.7.0 its parameter is `account_id`, not `company_id`.

## Save a method through the API

1. List the supported methods for the holder's country and read the `required_fields` of the one they pick:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const page = await whop.payouts.supportedMethods.list({
  account_id: "biz_xxxxxxxxxxxxx",
  supported_payout_method_id: "podst_xxxxxxxxxxxxx",
  destination_currency: "usd",
});

for (const field of page.data[0]?.required_fields ?? []) {
  console.log(field.id);
}
```

2. Create the method with the values keyed by field ID:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const method = await whop.payouts.methods.create({
  account_id: "biz_xxxxxxxxxxxxx",
  supported_payout_method_id: "podst_xxxxxxxxxxxxx",
  destination_currency: "usd",
  fields: { fld_xxxxxxxxxxxxx: "value from your form" },
  nickname: "Operating account",
  is_default: true,
});

console.log(method.id);
```

- Field IDs are stable `fld_` identifiers; you may hardcode them.
- A Basis Theory token ID may be passed in place of a raw value.
- A US routing number must pass the ABA checksum. A validation failure returns the method's full `required_fields` schema with the error.
- `nickname` must be unique per destination.
- Whop sends `payout_method.created` when a method is saved.

## PayPal with Log in with PayPal

The holder logs in to PayPal instead of typing an email, and Whop saves PayPal's email once its name matches the holder's payout setup.

Before you start:

- An API key with `payout:destination:read` and `payout:create_destination`.
- PayPal login enabled on the account by Whop. Until then `supports_paypal_login` is `false` and the session call returns `403`.
- A completed payout setup (verification), because Whop matches its name to the PayPal account.
- An `https` return page on a domain added to the account or its platform (`POST /domains` with `verification: {}`; it doesn't need to finish verifying). `https://localhost` works for testing.
- `@whop/sdk` 2.5.0 or later.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

let paypalMethodId: string | undefined;
for await (const method of await whop.payouts.supportedMethods.list({
  account_id: "biz_xxxxxxxxxxxxx",
  destination_currency: "usd",
})) {
  if (method.supports_paypal_login) {
    paypalMethodId = method.id;
    break;
  }
}
if (!paypalMethodId) throw new Error("PayPal login is not enabled for this account");

const session = await whop.payouts.paypalLinkSessions.create({
  account_id: "biz_xxxxxxxxxxxxx",
  supported_payout_method_id: paypalMethodId,
  destination_currency: "usd",
  return_url: "https://yourapp.example/settings/payouts",
});

console.log(session.authorize_url);
```

Redirect the holder's browser to `authorize_url`. The session expires in 15 minutes. Whop sends the browser back to `return_url` with one of:

| Query string | Meaning | Next |
|---|---|---|
| `?paypal_link_token=…` | The holder logged in | Save the method within 15 minutes |
| `?error=paypal_login_canceled` | The holder backed out | Offer to start again |
| `?error=paypal_login_failed` | PayPal refused, the link was reused, or the exchange failed | Start a new session |

On your server, save the method with the token in place of `fields`, using the same `account_id`, `supported_payout_method_id` and `destination_currency` as the session:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function savePaypal(paypalLinkToken: string, paypalMethodId: string) {
  const method = await whop.payouts.methods.create({
    account_id: "biz_xxxxxxxxxxxxx",
    supported_payout_method_id: paypalMethodId,
    destination_currency: "usd",
    paypal_link_token: paypalLinkToken,
  });
  return method.id;
}
```

- A refusal is a `400` with a `message` for the holder (for example a name mismatch). Show it as is.
- The token survives a refusal, so retry a temporary error with the same token. If the message says to connect PayPal again, start a new session.
- An unverified PayPal account or unconfirmed email still saves.
- Every redirect stays in the tab that opened PayPal. In a pop-up, your return page must notify its opener and close.

## Sources

- https://docs.whop.com/developer/platforms/manual-payouts.md
- https://docs.whop.com/developer/guides/connect-paypal-payout-method.md
- https://docs.whop.com/api-reference/beta/payouts/payout.md
- https://docs.whop.com/api-reference/beta/payouts/create-saved-payout-method.md
- https://docs.whop.com/api-reference/beta/payouts/list-supported-payout-methods.md
