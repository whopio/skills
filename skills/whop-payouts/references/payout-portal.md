# Payout portal: embedded or hosted

Let a subaccount verify its identity, add payout methods and withdraw on its own. Embed Whop Elements in your app, or redirect to a Whop-hosted portal.

| | Embedded (Wallet elements) | Hosted (account link) |
|---|---|---|
| Where it runs | Your page | A Whop page, then back to `return_url` |
| Server work | Mint an access token per account | Create an account link per visit |
| Covers | Balance, withdraw, activity, deposit, send, convert, cards; KYC through the Verifications elements | Payouts, payout methods, KYC and identity verification |

## Embedded

### 1. Mint an access token on your server

Authenticate your own user first, check they may manage `accountId`, then mint a token for that account with only the scopes the mounted elements need:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function mintWalletToken(accountId: string) {
  const { token } = await whop.accessTokens.create({
    account_id: accountId,
    scoped_actions: [
      "company:balance:read",
      "payout:withdraw_funds",
      "payout:destination:read",
      "payout:create_destination",
    ],
  });
  return token;
}
```

- A token minted without `scoped_actions` inherits every permission of your API key. Always pass the list.
- Tokens expire after one hour by default, three hours at most (`expires_at`). Mint on demand rather than caching.
- In SDK 2.7.0 the parameter is `account_id`. Older guides show `company_id`.

Scopes each element reads:

| Element | Scopes |
|---|---|
| `Balances` / `BalanceElement`, `ActivityElement` | `company:balance:read` |
| `WithdrawElement` | `payout:withdraw_funds`, `payout:destination:read`, `payout:create_destination` (to add a bank) |
| `SendElement` | `payout:transfer_funds` for direct transfers, `payout:withdraw_funds` for recipient lists; account recipient search adds `company:authorized_user:read` and `member:basic:read`; account claim links need `airdrop_link:manage` |
| `ConvertElement` | `company:balance:read` plus `crypto_wallet:swap` or `crypto_wallet:manage` |
| `KycElement` (Verifications) | `identity:read`, `identity:write` |

### 2. Mount the Wallet handle

```bash
npm install @whop/elements-react @whop/elements
```

```tsx
"use client";

import { useEffect, useState } from "react";
import { ActivityElement, BalanceElement, Balances, Wallet, WhopElements, WithdrawElement } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function PayoutPortal({ accountId }: { accountId: string }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/token?accountId=${accountId}`)
      .then((res) => res.json())
      .then((data) => setAccessToken(data.token));
  }, [accountId]);

  if (!accessToken) return null;

  return (
    <WhopElements elements={loadWhop()}>
      <Wallet accountId={accountId} accessToken={accessToken}>
        <Balances>
          <BalanceElement />
        </Balances>
        <WithdrawElement />
        <ActivityElement />
      </Wallet>
    </WhopElements>
  );
}
```

Without a bundler, load `https://cdn.whop.com/elements/amber/elements.js` with a `data-whop-elements` attribute and call `window.WhopElements().wallet.create({ accountId, accessToken })`, then `wallet.create("withdraw").mount("#withdraw")`.

- `Wallet` options: `accountId` (required, `biz_` or the viewer's own `user_`), `accessToken` (required on your own domain; without it the elements use the viewer's whop.com session, which only works on whop.com), `currency` (defaults to `usd`), `appearance`, `locale`.
- Refresh the token before it expires: `wallet.update({ accessToken })`, or pass the new value as the `accessToken` prop in React. `accessToken` is a value, not a callback.
- `WithdrawElement` creates the payout itself when your page doesn't drive it. If your server already talks to the payouts API, supply the methods and limits yourself and handle `onWithdrawalRequested` to create the payout (with an idempotency key).
- A deposit that needs identity verification fires `onIdentityVerificationRequested` on the Wallet handle. Wallet doesn't navigate; open your verification flow.
- On iOS the wallet SDK ships `BalanceElement`, `ListElement` and `ActivityElement`.

The other Wallet surfaces: `ActionsElement` (deposit, send, withdraw, convert buttons), `DepositElement`, `SendElement`, `ConvertElement`, `ActivityDetailElement`, `Reports`, and card surfaces (`Cards`, `CardDetailsElement`). Each page lists its props, events and scopes.

### 3. Identity verification

A subaccount must verify its identity before it can withdraw. Mount `KycElement` under a `Verifications` handle, which takes a `getToken` callback (called before the element mounts) instead of an `accessToken` value. The full verification flow is in `whop-platforms`.

## Hosted

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const link = await whop.accountLinks.create({
  account_id: "biz_xxxxxxxxxxxxx",
  use_case: "payouts_portal",
  return_url: "https://yourapp.com/payouts/complete",
  refresh_url: "https://yourapp.com/payouts/refresh",
});

console.log(link.url, link.expires_at);
```

| `use_case` | Opens |
|---|---|
| `account_onboarding` | KYC and identity verification |
| `payouts_portal` | Payouts, payout methods, KYC and identity verification |

`return_url` is where Whop sends the user when they want to come back; `refresh_url` is where it sends them when the link expires, so create a fresh link there. Both must be `https`. Create links on demand; don't store them.

## Sources

- https://docs.whop.com/developer/platforms/render-payout-portal.md
- https://docs.whop.com/developer/platforms/quickstart.md
- https://docs.whop.com/developer/guides/auth-scoping.md
- https://docs.whop.com/elements/latest/wallet/overview.md
- https://docs.whop.com/elements/latest/wallet/withdraw.md
- https://docs.whop.com/elements/latest/wallet/send.md
- https://docs.whop.com/api-reference/account-links/create-account-link.md
