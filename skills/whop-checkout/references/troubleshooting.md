# Checkout troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| First charge is double the subscription price | Recurring variant with `initial_price` equal to `renewal_price`; checkout charges both | `initial_price: 0` unless you want a setup fee |
| Price 100× too high, or a $0.29 charge | Minor and major units mixed up | API price fields (`initial_price`, `renewal_price`, `partial_amount`) are major units; Elements `amount` and payment request `amount` are minor units |
| Order fulfilled but never paid | Fulfilling from `onComplete` or the return page | Fulfill from the `payment.succeeded` webhook only |
| Thank-you page shown after a failed 3DS or declined financing | Return page ignores `status` | Branch on `status`: `succeeded`, `failed`, `canceled`, else pending |
| `returnUrl` refused | Not `https` (or a custom app scheme) | Use an `https` URL; `http` only on localhost |
| Checkout ignores a new variant or quantity | Element options are fixed at mount | Remount the `Checkout` handle |
| Payment elements spin forever | No `BrandingElement`; `createConfirmationToken` refuses without it | Mount `BrandingElement` inside `Payments` |
| No Apple Pay or Google Pay button | Domain not ready, wrong device, sandbox, or a Framer Embed | Register the domain until `apple_pay.state` is `ready`; test in production in Safari on a real device; load the script in the site header |
| Apple Pay sheet refuses to open from a custom button | `show()` called after an `await` | Call `canMakePayment()` earlier and `show()` first in the press handler |
| `payment_request_cancelled` | Buyer dismissed the sheet | Not an error; leave the button as it was |
| `requires_action` after a saved-card charge | Buyer treated as present (a `return_url` without `off_session`) | Pass `off_session: true` for charges without the buyer |
| Setup intent refuses the token | Token came from a payment-mode form | Mount `Payments` with `mode="setup"` |
| Setup intent stays `processing` | It saves in the background | Wait for `setup_intent.succeeded` |
| `409 idempotency_request_in_progress` | Retried while the first request with that key is still running | Wait and retry with the same key |
| `400 idempotency_key_mismatch` | Same key reused for a different request | One key per distinct request |
| CSP violation in the console | Missing source | Add `frame-src https://cdn.whop.com`, `connect-src https://api.whop.com`, or use `contentSecurityPolicy()`; wallet providers need their own sources |
| Old plan-era field names ignored on a current API version | Renamed in `2026-10-27` | `billing_type`, `variant_id`, `variant` |
| `400` naming `setup_future_usage` on `payments.direct.create` | Renewal variant without consent to save | Pass `setup_future_usage: "off_session"` |

## Sources

- https://docs.whop.com/developer/guides/accept-payments.md
- https://docs.whop.com/developer/guides/embed-checkout.md
- https://docs.whop.com/developer/guides/payment-request.md
- https://docs.whop.com/developer/guides/save-payment-methods.md
- https://docs.whop.com/developer/guides/card-details.md
- https://docs.whop.com/developer/api/idempotency.md
- https://docs.whop.com/developer/api/versioning.md
- https://docs.whop.com/payments/apple-pay.md
- https://docs.whop.com/elements/latest/getting-started.md
- https://docs.whop.com/api-reference/beta/variants/variant.md
