# Verify a webhook without an SDK

Whop webhooks follow the [Standard Webhooks](https://github.com/standard-webhooks/standard-webhooks) specification. Use this when there is no Whop SDK for your language (Go, for example). Where an SDK exists, use its helper instead.

## What Whop signs

- Signed content: the string `{webhook-id}.{webhook-timestamp}.{raw body}`.
- Algorithm: HMAC-SHA256, keyed with your `ws_...` webhook secret.
- Header: `webhook-signature` holds `v1,<base64 signature>`.

## Steps

1. Read the raw request body as bytes. Don't parse it first.
2. Read the `webhook-id`, `webhook-timestamp`, and `webhook-signature` headers.
3. Reject the request if `webhook-timestamp` is more than 5 minutes from the current time. This stops replays. (The SDK helpers apply this limit for you.)
4. Compute HMAC-SHA256 over `{webhook-id}.{webhook-timestamp}.{raw body}` and base64-encode the result.
5. Compare it to the signature after `v1,` with a constant-time comparison. Reject on mismatch.
6. Only then parse the JSON and branch on `type`.

These four headers never change across API versions: `webhook-id`, `webhook-signature`, `webhook-timestamp`, and `content-type`. Verification works the same on every `api_version_date` pin.

## Sources

- https://docs.whop.com/developer/guides/webhooks.md
