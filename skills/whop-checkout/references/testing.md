# Testing checkout

## Sandbox

| | URL |
|---|---|
| Dashboard and checkout pages | `https://sandbox.whop.com` |
| API | `https://sandbox-api.whop.com/api/v1` |

Create sandbox API keys at `sandbox.whop.com/dashboard/developer`; they're separate from production keys, and so are webhooks and their secrets.

```ts
import { WhopClient, WhopEnvironment } from "@whop/sdk";

const whop = new WhopClient({
  token: process.env.WHOP_API_KEY!,
  environment: WhopEnvironment.Sandbox,
});
```

Use `environment` (SDK 2.0+), not a custom `baseUrl`: a base URL sends every request to one host, so operations that need another host (such as the card-details vault) are refused.

## Test cards

| Card | Result |
|---|---|
| `4242 4242 4242 4242` | Succeeds |
| `4000 0000 0000 0002` | Declined |
| `4000 0000 0000 0341` | Saving the card succeeds; later charges are declined (test renewal recovery) |
| `5385 3083 6013 5181` | Requires 3D Secure; enter `Checkout1!` on the 3DS screen |

Any future expiry (such as 12/34), any 3-digit CVC, any billing address.

## What the sandbox can't test

- **Elements.** The sandbox environment isn't available for Whop Elements yet (`environment="sandbox"` on `WhopElements` will work once it is). Test sandbox purchases through the hosted `purchase_url` instead.
- **Apple Pay, Google Pay and other alternative methods.** Cards only. Test wallets in production, in Safari on a real Apple device for Apple Pay.
- **Payouts**, apps and messaging.

## A test pass

1. Create a variant and checkout configuration in sandbox and open `purchase_url`.
2. Pay with `4242...`; confirm your `payment.succeeded` handler ran once and the membership appears.
3. Pay with `4000 0000 0000 0002`; confirm nothing was fulfilled.
4. Pay with `5385...`; confirm the 3DS step and that your return page reads `status`.
5. Save `4000 0000 0000 0341` with a setup intent, charge it with `off_session: true`, and confirm you handle `payment.failed`.

## Sources

- https://docs.whop.com/developer/guides/sandbox.md
- https://docs.whop.com/payments/apple-pay.md
- https://docs.whop.com/developer/guides/card-details.md
