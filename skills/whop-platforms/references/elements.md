# Verifications and Dashboard elements

Embed onboarding and a seller dashboard in your own app. Install `@whop/elements` and `@whop/elements-react` (React), or load `https://cdn.whop.com/elements/amber/elements.js` and call `window.WhopElements()` (plain JavaScript). Both handles below take `accountId`: the connected account's `biz_` ID.

## Credentials

Elements never see your API key. Mint an access token on your server for the one account the signed-in user owns, with only the scopes the mounted elements need:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function mintDashboardToken(accountId: string) {
  const { token, expires_at } = await whop.accessTokens.create({
    account_id: accountId,
    scoped_actions: ["payout:account:read", "identity:write", "payment:basic:read"],
  });
  return { token, expires_at };
}
```

Tokens last 1 hour by default (3 hours at most). Leaving out `scoped_actions` gives the token every permission of your key, so always send it.

| Element | Scopes |
|---|---|
| Verifications handle (all its elements) | `identity:read`, `identity:write` |
| `RequiredActionsElement` | `payout:account:read`, plus `identity:write` to start verification |
| `VerificationElement` | `payout:account:read` |
| `PaymentsTableElement`, `PaymentDetailElement` | `payment:basic:read`; add `member:email:read` for buyer emails, `member:basic:read` for the customer journey, `access_pass:basic:read` and `plan:basic:read` for product and plan names |

## Verifications

`<Verifications accountId kind getToken>` (`kind` is `"individual"` for KYC, `"business"` for KYB; defaults to `"individual"`). `getToken` runs before the elements mount and must return a fresh token string.

- **`KycElement`**: the whole flow. It collects details, opens or resumes the provider session, answers follow-up requests, polls, and shows the result. Events: `onStatusChanged({ verificationId, status })`, `onCompleted({ verificationId })` (fires once on `approved`), `onActionRequired({ verificationId, requestedInformation })` (the element renders those forms itself), `onLoadFailed`.
- **`RfiElement`**: everything the account still owes, with the forms to answer it. Shows an all-clear when nothing is outstanding, so it can live on a settings page. Events: `onSubmitted`, `onCompleted`, `onLoadFailed`. `hideUnderReview` hides rows already with a reviewer.
- **`CapabilitiesElement`**: read-only standing (individual and business verification, plus what they unlock). Its verify button fires `onVerificationRequested` and does nothing else; mount `KycElement` in response. Sections hide with `hideStatus`, `hideCapabilities`, `hidePayouts`, `hideBankDeposits`, `hideCards`, `hideAds`.

Treat `onCompleted` as a UI hint. Your backend still confirms status with `verifications.list({ account_id })` or the `identity_profile.updated` webhook before enabling payouts.

## Dashboard

`<Dashboard accountId accessToken>`. One token serves every element under the handle; set a new one with `update({ accessToken })` before it expires.

```tsx
import { WhopElements, Dashboard, RequiredActionsElement, PaymentsTableElement } from "@whop/elements-react";
import { loadWhop } from "@whop/elements";

export function SellerHome({ accountId, accessToken }: { accountId: string; accessToken: string }) {
  return (
    <WhopElements elements={loadWhop()}>
      <Dashboard accountId={accountId} accessToken={accessToken}>
        <RequiredActionsElement onDepositRequested={() => console.log("open a deposit flow")} />
        <PaymentsTableElement onRefundRequested={(e) => console.log("confirm refund", e)} />
      </Dashboard>
    </WhopElements>
  );
}
```

- **`RequiredActionsElement`**: the outstanding-action banners from Whop's balance dashboard (verification, deposits, tax and more). Renders nothing when nothing is outstanding or a read fails. Verify starts a hosted session; Add money fires `onDepositRequested` for you to mount a deposit flow (the Wallet `DepositElement`, see `whop-payouts`). Also `onActionRequested`, `onIdentityVerificationRequested`.
- **`VerificationElement`**: an identity-only banner, shown while verification is outstanding. Its button fires `onVerificationRequested`; mount `KycElement` in response.
- **`PaymentsTableElement`**: the payments table with filters, search, export and pagination, for accounts with modest histories. Hands decisions back through `onPaymentSelected`, `onUserSelected`, `onRefundRequested`, `onInvoiceRequested`, `onSettingsRequested`.
- **`PaymentDetailElement`** (`paymentId: "pay_..."`): one payment with breakdown, activity and customer. It never refunds, retries or voids itself: `onRefundRequested`, `onRetryRequested` and `onVoidRequested` are your cue to confirm with the user and call the API from your server.

## Sources

- https://docs.whop.com/elements/latest/verifications/overview.md
- https://docs.whop.com/elements/latest/verifications/kyc.md
- https://docs.whop.com/elements/latest/verifications/rfi.md
- https://docs.whop.com/elements/latest/verifications/capabilities.md
- https://docs.whop.com/elements/latest/dashboard/overview.md
- https://docs.whop.com/elements/latest/dashboard/required-actions.md
- https://docs.whop.com/elements/latest/dashboard/verification.md
- https://docs.whop.com/elements/latest/dashboard/paymentsTable.md
- https://docs.whop.com/elements/latest/dashboard/paymentDetail.md
- https://docs.whop.com/developer/guides/auth-scoping.md
