---
name: whop-webhooks
description: >-
  Receive and verify Whop webhooks: create an endpoint, verify signatures with
  unwrapWebhook from @whop/sdk/helpers, handle payment, membership, refund,
  dispute, invoice, payout and app-install events, deduplicate retries, and test
  locally. Use when: "Whop webhook", "listen for payments", "fulfill after
  checkout", "grant access when someone pays", "revoke access when a
  subscription ends", "webhook signature failed", "Whop events aren't arriving".
  Chain with: whop-checkout for what creates the payment, whop-billing for
  acting on memberships, whop-api for client setup. NOT for: running a live
  store by hand (use the Whop CLI or whop plugin), ad conversion tracking.
license: Apache-2.0
metadata:
  author: whop
  version: "0.4.0"
---

# Whop Webhooks

Whop sends a signed `POST` to your server when something happens: a payment succeeds, a membership changes, a dispute opens. Your server verifies the signature, queues the work, and returns `200` within 5 seconds.

## Before you start

1. Fetch `https://docs.whop.com/developer/guides/webhooks.md` and the changelog at `https://docs.whop.com/developer/api/versioning.md`. If they disagree with this skill, follow the docs.
2. Confirm the environment. Sandbox (`https://sandbox-api.whop.com/api/v1`, dashboard at `sandbox.whop.com`) and production have separate webhooks and secrets.
3. Confirm the server framework before writing a handler. Framework handlers are in [references/frameworks.md](references/frameworks.md).
4. Creating a webhook through the API needs an API key and a client. Set that up with `whop-api`.

## Rules

1. **Verify before you read anything.** Call `unwrapWebhook` from `@whop/sdk/helpers` (Python: `whop_sdk.lib.verify_webhook.unwrap`, Ruby: `WhopSDK::Helpers::VerifyWebhook.unwrap`). If the signature is wrong it throws, and your handler never sees the payload.
2. **Pass the raw body.** `await request.text()`, `await request.body()`, `request.raw_post`. Parsing JSON first changes the bytes and every signature check fails.
3. **Pass the secret exactly as Whop gave it**, a `ws_...` string. Don't strip the prefix and don't base64-encode it. The helper derives the key.
4. **Respond `2xx` in under 5 seconds.** Verify, queue the work, return. A timeout, error status, or redirect is a failed attempt, and Whop doesn't follow redirects.
5. **Deduplicate on `webhook-id`.** Whop delivers at least once, and every retry of a delivery carries the same `webhook-id` header (it equals the envelope's `id`). Store it and skip ones you've handled.
6. **Don't rely on order.** A newer event can arrive before an older one. When order matters, read the current state from the API instead of trusting the event.
7. **Event names are dotted `resource.action`** and the envelope field is `type`: `payment.succeeded`, `membership.activated`, `membership.updated`.
8. **Losing access arrives as `membership.updated`**, with `previous_attributes.status` holding the status it left. `membership.deactivated` and `membership.cancel_at_period_end_changed` still deliver but are no longer documented; don't build new handlers on them.
9. **Set `api_version_date` when you create a webhook** so payloads don't change shape when the API changes. Pins from `2026-08-14` carry `account_id` in the envelope; older or unpinned webhooks carry `company_id`.
10. **Use `api_version: "v1"`.** The legacy `v2` and `v5` formats don't use Standard Webhooks signatures.

## Pick the events

| Goal | Subscribe to | Then |
|---|---|---|
| Fulfill an order | `payment.succeeded` | Use `data` (a payment) to fulfill |
| Grant or revoke access | `membership.activated`, `membership.updated` | On `membership.updated`, re-read access from the API (`whop-billing`) |
| Recover a failed renewal | `payment.failed`, `payment.requires_action` | Send the buyer `data.recovery_url` when present |
| Track refunds and disputes | `refund.created`, `refund.updated`, `dispute.created`, `dispute.updated` | Update your records |
| Fulfill a paid invoice | `payment.succeeded` | `data.id` is the invoice's `pay_` ID. Native invoices don't send `invoice.*` events (`whop-billing`) |
| Track payouts | `payout.created`, `payout.updated`, `payout.reversed` | See `whop-payouts` |
| App installed or removed | `app_installation.created`, `app_installation.deleted` | See `whop-apps` |

Every event and its payload type is in [references/events.md](references/events.md).

## Create the webhook

Through the API (or the dashboard's Developer tab, which shows the secret in the **Secret** column):

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const webhook = await whop.webhooks.create({
  url: "https://example.com/webhooks/whop",
  events: ["payment.succeeded", "membership.activated", "membership.updated"],
  api_version_date: "2026-08-14",
});

console.log(webhook.webhook_secret);
```

`webhook_secret` is returned only once. Store it as `WHOP_WEBHOOK_SECRET` immediately. To receive events for an app's installs, or for connected accounts, see `resource_id` and `child_resource_events` in the [Webhooks API reference](https://docs.whop.com/api-reference/webhooks/webhook.md).

## With the Whop MCP server

The `whop` MCP tools act on the signed-in user's **live** account and can't reach sandbox (`whop-api` covers connecting, `intent`/`intent_id`, and prepare-and-confirm). Its `docs_search` and `docs_query` read the docs pages this skill links. Use the tools to fill in and debug the code, not to replace it:

- See what's registered: `webhooks_list` / `webhooks_get` (URL, events, `enabled`, `api_version`, `api_version_date`, failure counts). Results include `webhook_secret`: never print it or write it to a tracked file.
- Debug production deliveries: `webhooks_deliveries` lists recent attempts and their status. `webhooks_deliveries-replay` resends one and `webhooks_test` sends a test event; both are prepare-and-confirm and hit the live endpoint.
- `webhooks_create` makes a real production endpoint. Use it only when the user asks, and put the returned secret straight into the gitignored env file the handler reads.
- Test the handler code locally with `scripts/send-test-event.mjs` (Verify, step 1) and a sandbox webhook, not through MCP.

## Verify and handle events

```ts
import { unwrapWebhook } from "@whop/sdk/helpers";
import type { Whop } from "@whop/sdk";

type WhopEvent =
  | { id: string; type: "payment.succeeded"; data: Whop.Payment }
  | { id: string; type: "membership.activated" | "membership.updated"; data: Whop.Membership };

const handled = new Set<string>();

export async function POST(request: Request): Promise<Response> {
  const event = unwrapWebhook<WhopEvent>(await request.text(), {
    headers: Object.fromEntries(request.headers),
    key: process.env.WHOP_WEBHOOK_SECRET!,
  });

  if (handled.has(event.id)) return new Response("OK");
  handled.add(event.id);

  if (event.type === "payment.succeeded") {
    queueMicrotask(() => fulfill(event.data));
  }

  return new Response("OK");
}

function fulfill(payment: Whop.Payment) {
  console.log("fulfill", payment.id);
}
```

The `Set` stands in for durable storage. In production, record `event.id` in your database inside the same transaction as the work, and do slow work in a job queue or your platform's background function (`waitUntil` on Vercel and Cloudflare). `unwrapWebhook` returns the parsed body as a plain object; branch on `type`.

## Verify

1. Test the handler locally first, with no tunnel or Whop account. [scripts/send-test-event.mjs](scripts/send-test-event.mjs) (Node 18+, no dependencies) sends Whop's published example payload for an event, signed with your secret the way Whop signs deliveries:

   ```bash
   node scripts/send-test-event.mjs --url http://localhost:3000/api/webhooks/whop --repeat 2
   node scripts/send-test-event.mjs --url http://localhost:3000/api/webhooks/whop --tamper
   ```

   It reads the secret from `WHOP_WEBHOOK_SECRET` (or `--secret`), so use the same value the server has. `--type` picks the event (`--list-types` lists them). The first command passes when every attempt gets a `2xx` within 5 seconds, and your logs should show the work ran once for the two identical deliveries. The second passes when the handler rejects the bad signature.
2. Expose your local server with [ngrok](https://ngrok.com) or Cloudflare Tunnel; Whop rejects `localhost` and private addresses. Register the tunnel URL.
3. Send a test event from the webhook's menu in the dashboard, or call `POST /api/v1/webhooks/{id}/test`. Whop returns your server's status and body.
4. Make a real sandbox purchase with a test card (see `whop-checkout`) and confirm the handler ran once.
5. Inspect deliveries (kept 30 days) in the dashboard or with `GET /api/v1/webhooks/{id}/deliveries`.

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| Every signature check fails | Body parsed before verifying, or secret altered | Pass the raw body; pass the `ws_` secret unchanged |
| Signature fails only in production | Using the sandbox secret, or vice versa | Each environment's webhook has its own secret |
| Same event handled twice | No dedupe | Store `webhook-id` / `event.id` |
| Retries pile up | Handler slower than 5 seconds | Return `200` first, work in the background |
| No events at all | URL not public, wrong environment, or webhook disabled | Check the URL, environment, and `enabled` |
| Events stopped after an outage | 72 hours of failures (10+ failed deliveries) disables the webhook | Re-enable in the dashboard or `PATCH /webhooks/{id}` with `"enabled": true`; read missed data from the API, it isn't resent |

Retries: 12 after the first attempt, at 30s, 2m, 8m, 30m, 1h, 3h, 6h, then every 12h, about 71 hours in total. More cases in [references/troubleshooting.md](references/troubleshooting.md).

## References

- [references/frameworks.md](references/frameworks.md): read when writing the handler for Next.js, FastAPI, or Rails.
- [references/events.md](references/events.md): read when choosing events or typing a payload.
- [references/verify-without-sdk.md](references/verify-without-sdk.md): read when there's no Whop SDK for the language (Go, Elixir, ...).
- [references/troubleshooting.md](references/troubleshooting.md): read when deliveries fail or signatures don't verify.
- [scripts/send-test-event.mjs](scripts/send-test-event.mjs): run to send signed test events to a local handler (see Verify).
