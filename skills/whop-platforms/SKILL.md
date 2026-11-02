---
name: whop-platforms
description: >-
  Run a marketplace or platform on Whop: create connected accounts for your
  sellers, onboard them with account links, verify identity (KYC/KYB) through
  the hosted flow, the API or the Verifications element, answer RFIs, and
  collect payments for connected accounts with an application fee. Use when:
  "build a marketplace", "onboard a seller", "create a connected account",
  "sub-merchant", "send sellers to KYC", "verify my sellers", "KYB",
  "verification needs more information", "take a platform fee", "application
  fee", "split payments with sellers", "embed onboarding in my app". Chain
  with: whop-payouts to pay connected accounts and embed their payout portal,
  whop-webhooks for connected-account events, whop-checkout for the checkout
  UI, whop-api for client setup. NOT for: transfers and payouts (use
  whop-payouts), a single store taking payments (use whop-checkout), moving
  from Stripe Connect (use whop-migrate), apps installed inside Whop (use
  whop-apps).
license: Apache-2.0
metadata:
  author: whop
  version: "0.3.0"
---

# Whop Platforms

A platform is a Whop account with connected accounts under it: one per seller, creator or merchant. You create each connected account, send its owner through identity verification, then take payments for it (keeping an application fee) and pay it out.

## Before you start

1. Fetch `https://docs.whop.com/developer/platforms/enroll-connected-accounts.md`, `https://docs.whop.com/developer/platforms/collect-payments-for-connected-accounts.md`, `https://docs.whop.com/developer/verification/overview.md` and the changelog at `https://docs.whop.com/developer/api/versioning.md`. If they disagree with this skill, follow the docs.
2. Set up the client with `whop-api`, using the **platform's Account API key**. That key decides which platform owns every connected account you create. It is a secret: keep it on your server.
3. Build against sandbox first (`https://sandbox-api.whop.com/api/v1`).
4. Decide where onboarding happens: a Whop-hosted page (account link), your own page (Verifications element), or fully through the API.

## Rules

1. **The API key makes it a connected account.** `accounts.create` with the platform's Account API key creates a connected account under that platform; there is no parent field to send. `email` is required for a connected account and belongs to the seller, who gets setup and payment notifications.
2. **Set `metadata.external_id` to your own seller ID.** Create is idempotent on email plus `external_id`: the same pair returns the existing account, a new `external_id` creates a new account even for a used email. That makes retries safe.
3. **Use `account_id` (`biz_`) everywhere.** `accountLinks.create`, `accessTokens.create`, `checkoutConfigurations.create` and `verifications.list` all take `account_id` in `@whop/sdk` 2.7.0. Some guides still show `company_id`; it is the old name.
4. **Account links have two use cases only**: `account_onboarding` (identity verification) and `payouts_portal` (payouts, payout methods and verification). `return_url` and `refresh_url` must be `https`. Links expire (`expires_at`), so create one per visit.
5. **Don't trust the verification webhook's payload for state.** `identity_profile.updated` fires on every change and tells you which profile changed, not its new state. Re-read with `verifications.list({ account_id })`.
6. **A seller must be verified before money leaves.** Verification is required to pay out; accepting payments doesn't need it until the account reaches $5,000 in payments.
7. **Fees are fixed amounts in major units.** `application_fee_amount: 1.23` is $1.23 per unit, in the variant's currency. It must be positive and less than the price. For a percentage fee, compute the amount from the price yourself.
8. **Pick who owns the payment.** A direct charge on the connected account makes the seller pay Whop fees and handle refunds and disputes. Collecting on the platform and transferring later makes the platform the merchant of record for all of that.
9. **Connected-account webhooks are opt-in.** A webhook on the platform with `child_resource_events: true` receives events from its connected accounts only (see `whop-webhooks`).
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

**Direct charge with an application fee.** Create the checkout on the connected account; Whop charges the buyer there and sends your fee to the platform.

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

## Verify

1. In sandbox, create a connected account with a test email and `external_id`, and repeat the call: the same `id` must come back.
2. Open the onboarding link, finish it, and confirm `verifications.list({ account_id })` shows the status you expect and `identity_profile.updated` reached your webhook (created with `child_resource_events: true`).
3. Buy through the checkout with a sandbox test card and check the platform's balance received the fee and the seller's the rest (`financialActivity.list`, see `whop-payouts`).

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `400` `email is required` on `accounts.create` | Connected accounts need the owner's email | Pass `email` |
| `400` `Unsupported fields: parent_account_id` | Tried to name the parent | Drop it; the API key sets the parent |
| `A connected account cannot create its own connected accounts` | Called with a connected account's key | Use the platform's key |
| Duplicate seller accounts | No `external_id`, or a new one per retry | Use your stable seller ID as `metadata.external_id` |
| Account link `URL must start with 'https://'` | `http` or `localhost` return URLs | Use `https` URLs (a tunnel locally) |
| Verification `400` `address_country_sanctioned` | Address in a sanctioned country or region | Whop can't support the user |
| `400` `Cannot update an approved verification.` | Identity data is locked after approval | Start a new verification instead |
| Verification `403` | Key or token lacks `identity:read` / `identity:write` | Add the scopes |
| `application_fee_amount` rejected | Not positive, not below the price, or the account has no parent | Fix the amount; create the checkout on a connected account |
| No connected-account events | Webhook lacks `child_resource_events: true` | Create it on the platform with that flag |

## References

- [references/verification.md](references/verification.md): read when verifying through the API (prefill, documents, KYB, business structures), answering RFIs, or handling rejections.
- [references/collect-payments.md](references/collect-payments.md): read when choosing between direct charges and transfers, or working out fees, refunds and disputes.
- [references/elements.md](references/elements.md): read when embedding the Verifications or Dashboard elements.
