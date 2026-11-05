---
name: whop-platforms
description: >-
  Run a marketplace or platform on Whop: create subaccounts (formerly connected
  accounts) for sellers, onboard them with account links, verify identity
  (KYC/KYB) through the hosted flow, the API or the Verifications element,
  answer RFIs, and collect payments for subaccounts with an application fee.
  Use when: "build a marketplace", "onboard a seller", "create a subaccount",
  "create a connected account", "sub-merchant", "KYC", "KYB", "verify my
  sellers", "verification needs more information", "take a platform fee",
  "split payments with sellers". NOT for: transfers and payouts (whop-payouts),
  a single store (whop-checkout), moving from Stripe Connect (whop-migrate),
  apps inside Whop (whop-apps).
license: Apache-2.0
metadata:
  author: whop
  version: "0.5.0"
---

# Whop Platforms

A platform is a Whop account with subaccounts under it: one per seller, creator or merchant. You create each subaccount, send its owner through identity verification, then take payments for it (keeping an application fee) and pay it out.

Whop called subaccounts *connected accounts* until API version `2026-11-03-1`, so older docs, code and dashboards use that name. Nothing about creating or paying them changed, but on that version and later `include_connected_accounts` on payment and dispute lists is `include_subaccounts`; `@whop/sdk` 2.7.0 (which sends `2026-10-28`) still takes `include_connected_accounts`.

## Before you start

1. **Inspect the project first.** Note the installed `@whop/sdk` version (`node_modules/@whop/sdk/package.json`; `whop-sdk` in Python, `whop_sdk` in Ruby), the framework, and whether the client targets sandbox or production. On `@whop/api` or `@whop/sdk` below 2.0, upgrade first (`whop-migrate`). If a name here doesn't compile, search the installed `node_modules/@whop/sdk/reference.md` for it and trust that over this skill.
2. Fetch `https://docs.whop.com/developer/platforms/enroll-subaccounts.md`, `https://docs.whop.com/developer/platforms/collect-payments-for-subaccounts.md` and `https://docs.whop.com/developer/verification/overview.md`. If they disagree with this skill, follow the docs and tell the user (see [references/skill-feedback.md](references/skill-feedback.md)). Read the changelog (`https://docs.whop.com/developer/api/versioning.md`) only when you pin or upgrade a version, or a response doesn't match this skill or the docs.
3. Set up the client with `whop-api`, using the **platform's Account API key**. That key decides which platform owns every subaccount you create. It is a secret: keep it on your server. Without that skill: install `@whop/sdk` and create `new WhopClient({ token: process.env.WHOP_API_KEY, environment: WhopEnvironment.Sandbox })` in server-only code, dropping `environment` for production (`https://docs.whop.com/developer/quickstart.md`).
4. Build against sandbox first (`https://sandbox-api.whop.com/api/v1`).
5. Decide where onboarding happens: a Whop-hosted page (account link), your own page (Verifications element), or fully through the API.
6. Other `whop-*` skills named here are optional. When one isn't installed, use the matching guide linked from `https://docs.whop.com/developer/start.md` instead.

## Rules

1. **The API key makes it a subaccount.** `accounts.create` with the platform's Account API key creates a subaccount under that platform; there is no parent field to send. `email` is required for a subaccount and belongs to the seller, who gets setup and payment notifications.
2. **Set `metadata.external_id` to your own seller ID.** Create is idempotent on email plus `external_id`: the same pair returns the existing account, a new `external_id` creates a new account even for a used email. That makes retries safe.
3. **Use `account_id` (`biz_`) everywhere.** `accountLinks.create`, `accessTokens.create`, `checkoutConfigurations.create` and `verifications.list` all take `account_id` in `@whop/sdk` 2.7.0. Some guides still show `company_id`; it is the old name.
4. **Account links have two use cases only**: `account_onboarding` (identity verification) and `payouts_portal` (payouts, payout methods and verification). `return_url` and `refresh_url` must be `https`. Links expire (`expires_at`), so create one per visit.
5. **Don't trust the verification webhook's payload for state.** `identity_profile.updated` fires on every change and tells you which profile changed, not its new state. Re-read with `verifications.list({ account_id })`.
6. **A seller must be verified before money leaves.** Verification is required to pay out; accepting payments doesn't need it until the account reaches $5,000 in payments.
7. **Fees are fixed amounts in major units.** `application_fee_amount: 1.23` is $1.23 per unit, in the variant's currency. It must be positive and less than the price. For a percentage fee, compute the amount from the price yourself.
8. **Pick who owns the payment.** A direct charge on the subaccount makes the seller pay Whop fees and handle refunds and disputes. Collecting on the platform and transferring later makes the platform the merchant of record for all of that.
9. **Subaccount webhooks are opt-in.** A webhook on the platform with `child_resource_events: true` receives events from its subaccounts only (see `whop-webhooks`).
10. **Browsers get scoped access tokens, never the API key.** Mint them on your server with an explicit `scoped_actions` list; without one the token inherits the key's full reach.

## Pick a path

| Goal | Do this |
|---|---|
| Add a seller and send them to Whop's onboarding | [Onboard a seller](#onboard-a-seller) |
| Onboarding inside your own app | [Embed verification](#embed-verification) |
| Verify through the API with your own form or documents | [references/verification.md](references/verification.md) |
| Whop asked for more information (`action_required`) | [Answer RFIs](#answer-rfis) |
| Take a platform fee on each sale | [Collect payments for a seller](#collect-payments-for-a-seller) |
| Pay a seller from your balance, or embed their payout portal | `whop-payouts` |
| Show a seller their payments and outstanding actions | Dashboard element, [references/elements.md](references/elements.md) |

## Onboard a seller

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const account = await whop.accounts.create({
  email: "merchant@example.com",
  title: "Acme Merchant Store",
  metadata: { external_id: "seller_12345" },
});

const link = await whop.accountLinks.create({
  account_id: account.id,
  use_case: "account_onboarding",
  return_url: "https://yourapp.com/onboarding/complete",
  refresh_url: "https://yourapp.com/onboarding/refresh",
});

console.log(account.id, link.url);
```

1. Store `account.id` (`biz_`) against your seller.
2. Redirect the seller to `link.url`. Whop sends them to `return_url` when they finish and to `refresh_url` if the link expires; mint a fresh link there.
3. Don't treat the return as success. Read the status with `verifications.list({ account_id })` or wait for `identity_profile.updated`.

Statuses: `not_started`, `pending` (send the user to `session_url`), `processing`, `action_required` (answer RFIs), `manual_review` (nothing to submit; usually within 3 business days), `approved`, `rejected` (call `verifications.create` again for a new session). An account has at most one individual (KYC) and one business (KYB) verification.

## Embed verification

Mount `KycElement` for the full KYC or KYB flow on your page. The `Verifications` handle calls `getToken` before it mounts; return a token minted on your server for that account with `identity:read` and `identity:write`.

```tsx
import { WhopElements, Verifications, KycElement } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function VerifyIdentity({ accountId }: { accountId: string }) {
  return (
    <WhopElements elements={loadWhop()}>
      <Verifications
        accountId={accountId}
        kind="individual"
        getToken={() =>
          fetch(`/api/token?accountId=${accountId}`)
            .then((res) => res.json())
            .then((data) => data.token)
        }
      >
        <KycElement onCompleted={() => console.log("Verified")} />
      </Verifications>
    </WhopElements>
  );
}
```

The token endpoint:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function mintVerificationToken(accountId: string) {
  const { token } = await whop.accessTokens.create({
    account_id: accountId,
    scoped_actions: ["identity:read", "identity:write"],
  });
  return token;
}
```

Authenticate your user and check they own `accountId` before minting. `RfiElement`, `CapabilitiesElement` and the Dashboard elements are in [references/elements.md](references/elements.md).

## Answer RFIs

When Whop needs more (a document, a tax ID, a business detail), the verification goes to `action_required` and lists open items in `requested_information`. Each item has an `id` (`inrqi_`), a `requirement`, an input `type` and a `label` to show the user. Answer with one `PATCH`:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.verifications.update({
  id: "idpf_xxxxxxxxxxxxx",
  body: {
    requested_information: [
      { id: "inrqi_xxxxxxxxxxxxx", value: "1990-01-15" },
      { id: "inrqi_zzzzzzzzzzzzz", files: ["file_xxxxxxxxxxxxx"] },
    ],
  },
});
```

Answered items leave the array; the verification moves to `processing`, then `approved` or `manual_review`. A rejected answer comes back with `errors` (`code` and `reason`): show `reason` and resubmit with the same item `id`. Answer payloads per `type`, and the rejection codes, are in [references/verification.md](references/verification.md). `RfiElement` renders the same forms for you.

## Collect payments for a seller

**Direct charge with an application fee.** Create the checkout on the subaccount; Whop charges the buyer there and sends your fee to the platform.

```ts
import { WhopClient } from "@whop/sdk";
import type { Whop } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const price = 49.0;
const variant: Whop.CreateCheckoutConfigurationsRequest.Variant & { application_fee_amount: number } = {
  currency: "usd",
  billing_type: "one_time",
  initial_price: price,
  application_fee_amount: Math.round(price * 0.1 * 100) / 100,
};

const checkout = await whop.checkoutConfigurations.create({
  account_id: "biz_xxxxxxxxxxxxx",
  variant,
});

console.log(checkout.purchase_url);
```

`initial_price: 49.0` is $49.00 and the fee is $4.90, so the seller receives $44.10 before Whop's fees. `@whop/sdk` 2.7.0 doesn't type `application_fee_amount` on `variant` yet, hence the widened type; the API accepts it. Send the buyer to `purchase_url`, or embed it (`whop-checkout`).

**Collect on the platform, then transfer.** Take the payment on your own account and move each seller's share with `transfers.create` (`type: "balance"`, amounts in dollars, an idempotency key). That flow lives in `whop-payouts`. More on choosing in [references/collect-payments.md](references/collect-payments.md).

## With the Whop MCP server

The `whop` MCP tools act on the signed-in user's **live** account and can't reach sandbox (`whop-api` covers connecting, `intent`/`intent_id`, and prepare-and-confirm). Its `docs_search` and `docs_query` read the docs pages this skill links. Use the tools to fill in and debug the code, not to replace it:

- Inspect subaccounts: `accounts_get`, `accounts_list`, `verifications_list`, `identity-profiles_get`.
- `accounts_create` and `account-links_create` exist but create real seller accounts and live onboarding links. Your platform does that per seller with the SDK and its Account API key; through MCP, only when the user asks for a specific account.

## Verify

1. In sandbox, create a subaccount with a test email and `external_id`, and repeat the call: the same `id` must come back.
2. Open the onboarding link, finish it, and confirm `verifications.list({ account_id })` shows the status you expect and `identity_profile.updated` reached your webhook (created with `child_resource_events: true`).
3. Buy through the checkout with a sandbox test card and check the platform's balance received the fee and the seller's the rest (`financialActivity.list`, see `whop-payouts`).

When you're done, tell the user what changed, which environment it targets (sandbox or production; if that isn't decided yet, say so and recommend sandbox first), which of these checks you ran, and what is still unverified.

## Errors

If the same call fails twice, stop retrying it. Read the whole error (status, body and request ID), check the docs page and the installed SDK types, then change the request or the approach.

| Symptom | Cause | Fix |
|---|---|---|
| `400` `email is required` on `accounts.create` | Subaccounts need the owner's email | Pass `email` |
| `400` `Unsupported fields: parent_account_id` | Tried to name the parent | Drop it; the API key sets the parent |
| `A connected account cannot create its own connected accounts` | Called with a subaccount's key | Use the platform's key |
| Duplicate seller accounts | No `external_id`, or a new one per retry | Use your stable seller ID as `metadata.external_id` |
| Account link `URL must start with 'https://'` | `http` or `localhost` return URLs | Use `https` URLs (a tunnel locally) |
| Verification `400` `address_country_sanctioned` | Address in a sanctioned country or region | Whop can't support the user |
| `400` `Cannot update an approved verification.` | Identity data is locked after approval | Start a new verification instead |
| Verification `403` | Key or token lacks `identity:read` / `identity:write` | Add the scopes |
| `application_fee_amount` rejected | Not positive, not below the price, or the account has no parent | Fix the amount; create the checkout on a subaccount |
| No subaccount events | Webhook lacks `child_resource_events: true` | Create it on the platform with that flag |

## References

- [references/verification.md](references/verification.md): read when verifying through the API (prefill, documents, KYB, business structures), answering RFIs, or handling rejections.
- [references/collect-payments.md](references/collect-payments.md): read when choosing between direct charges and transfers, or working out fees, refunds and disputes.
- [references/elements.md](references/elements.md): read when embedding the Verifications or Dashboard elements.
- [references/skill-feedback.md](references/skill-feedback.md): read when the user says this skill gave wrong, outdated or missing guidance, or the docs contradicted it during the task.
