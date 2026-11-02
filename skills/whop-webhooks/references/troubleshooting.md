# Webhook troubleshooting

## Nothing arrives

- The URL must be public `https`. Whop rejects `localhost` and private-network addresses; use a tunnel (ngrok, Cloudflare Tunnel) locally.
- The webhook must belong to the right account and the right environment. Sandbox webhooks only receive sandbox events.
- Check the webhook is `enabled`. After 24 hours of failed deliveries Whop emails a warning; after 72 hours with 10 or more failures it disables the webhook and emails again. Re-enable it in the dashboard or with `PATCH /api/v1/webhooks/{id}` and `"enabled": true`, which resets the failure history. Events from while it was off are not resent; read them from the API.
- Look at the delivery log: each delivery's request, response code, body and timing are kept for 30 days in the dashboard and at `GET /api/v1/webhooks/{id}/deliveries`.

## Signatures fail

- The body was parsed (or re-serialized) before verification. Pass the exact raw string or bytes.
- The secret was changed. Pass the `ws_...` value exactly as returned; no base64, no prefix stripping.
- The secret is from the other environment, or from a different webhook.
- The server clock is off by more than 5 minutes; the timestamp check rejects the request.

## Duplicates or retries

- Whop delivers at least once. Every retry carries the same `webhook-id` header, which also appears as the envelope's `id`. Dedupe on it.
- A response slower than 5 seconds, an error status, or a redirect counts as failure and is retried: 12 retries at 30s, 2m, 8m, 30m, 1h, 3h, 6h, then every 12h, about 71 hours in total.

## Events out of order

- Delivery order isn't guaranteed. For state that matters (access, balances), re-read the resource from the API when the event arrives.

## Payload shape changed

- Set `api_version_date` on the webhook. Unpinned webhooks keep the shape they were created with; pinned ones follow the pin. Pins from `2026-08-14` carry `account_id` in the envelope, older ones `company_id`. Resources that exist only on the current API (cards, variants, transfers, swaps, deposits, exports) always send the latest `data` shape.

## Sources

- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/developer/troubleshooting.md
