---
name: whop-migrate
description: >-
  Move a payment integration to Whop, or upgrade old Whop code. Scans for
  Stripe or other processor code and maps products, prices, checkout,
  customers, subscriptions and webhooks to Whop; rewrites old Whop names
  (plans, companies, withdrawals, top-ups, API v2, GraphQL, @whop/api, cents)
  to current ones. Use when: "migrate from Stripe to Whop", "switch payment
  processor to Whop", "replace Stripe Checkout with Whop", "move subscribers to
  Whop", "update old Whop code", "@whop/api is shut down", "plans renamed to
  variants", "company_id vs account_id". NOT for: a new integration with no
  payment code (whop-checkout), payouts (whop-payouts), subaccounts
  (whop-platforms), app auth (whop-apps).
license: Apache-2.0
metadata:
  author: whop
  version: "0.5.0"
---

# Whop Migrate

Two jobs: moving an existing integration from Stripe or another processor onto Whop, and upgrading code written against older Whop APIs to the current names.

## Before you start

1. Fetch `https://docs.whop.com/developer/api/migrate-from-previous-versions.md` and `https://docs.whop.com/api-reference/stability.md`. If they disagree with this skill, follow the docs and tell the user (see [references/skill-feedback.md](references/skill-feedback.md)). Read the changelog (`https://docs.whop.com/developer/api/versioning.md`) only when you pin or upgrade a version, or a response doesn't match this skill or the docs.
2. Find out which job this is: payment code from another processor, old Whop code, or both. Look before asking: the scans below answer it.
3. Set up a sandbox client first (`whop-api`). Without that skill: install `@whop/sdk` and create `new WhopClient({ token: process.env.WHOP_API_KEY, environment: WhopEnvironment.Sandbox })` in server-only code, dropping `environment` for production (`https://docs.whop.com/developer/quickstart.md`). Migrate and test against `https://sandbox-api.whop.com/api/v1` before touching production.
4. Check the installed `@whop/sdk` version. Every name in this skill was checked against 2.7.0; on another version, confirm a name in the package's `reference.md` before using it.
5. Other `whop-*` skills named here are optional. When one isn't installed, use the matching guide linked from `https://docs.whop.com/developer/start.md` instead.

## Rules

1. **Every new name must exist in the installed SDK.** Look it up in [references/legacy-map.md](references/legacy-map.md), then confirm it in `node_modules/@whop/sdk/reference.md` or the request types. Never keep an old name because a doc example still shows it.
2. **Amounts are dollars.** Prices, refunds, transfers, payouts and deposits take major units (`29.0` is $29.00). Convert every stored or computed cents value (`/ 100`) at the boundary, and say the unit in code.
3. **IDs survive the renames.** Variants keep the `plan_` prefix, payouts keep `wdrl_`, external accounts keep `sacc_`. Don't rewrite stored IDs; only the field and method names change (`plan_id` → `variant_id`, `company_id` → `account_id`).
4. **Same API keys.** The Current API takes the keys v2 used. A `403` means the key lacks that endpoint's permission; add it rather than making a new key.
5. **Deadlines.** API v2 (`api.whop.com/api/v2` and `/v2`) stops working on November 13, 2026. The public GraphQL API and the `@whop/api` client it backs stopped on October 26, 2026.
6. **Fulfill from the `payment.succeeded` webhook**, never from the browser redirect. A redirect handler ported from another processor is the most common bug.
7. **Old webhooks keep their old format.** A webhook created through v2 keeps sending v2 payloads. Create a new webhook (it is always `v1`) with an `api_version_date`, move the handler, then delete the old one.
8. **Don't charge existing subscribers again to move them.** Stripe subscriptions move with the dashboard migration (**Settings → Payments → Migrations → Stripe**), which hands renewals to Whop and sets the Stripe subscriptions to cancel at period end.
9. **Upgrading a version pin means reading every changelog entry in between**, not only the target month. From before `2026-07-23` you cross the members and memberships rewrite; from before `2026-10-27-1` you cross the plans-to-variants renames.
10. **Keep API keys on the server.** v2's `validate_license` becomes a server-side flow: your server retrieves the membership by license key, checks `status`, and writes the hardware ID to `metadata`. Never ship an API key in desktop, mobile or browser code to do it.

## Pick a path

| You have | Do |
|---|---|
| Stripe or another processor's SDK, checkout, or webhooks | [Move from another processor](#move-from-another-processor) |
| Calls to `api.whop.com/api/v2`, `/v2`, or `public-graphql` | [Upgrade old Whop code](#upgrade-old-whop-code), route table in [references/legacy-map.md](references/legacy-map.md) |
| `@whop/api`, a default-imported or `apiKey`-configured Whop client, or old namespaces (plans, companies, withdrawals, top-ups) | [Upgrade old Whop code](#upgrade-old-whop-code) |
| Current SDK, but responses changed shape | Upgrade the pin: [references/legacy-map.md](references/legacy-map.md) and the changelog |
| Existing subscribers on Stripe | Step 7 of the processor path |

## Move from another processor

1. **Scan.** Run the searches in [references/processor-mapping.md](references/processor-mapping.md): processor SDKs in dependency files, files that import them, webhook routes and signature checks, stored processor IDs, and cents math. Write the hits down as a checklist.
2. **Map.** For each hit, find the Whop object that plays the same role in the mapping table there: product → product, price → variant, hosted checkout → checkout configuration, customer → member, subscription → membership, charge → payment.
3. **Set up Whop.** Install `@whop/sdk`, create sandbox keys, and build the client with `whop-api`. Keep the old processor running.
4. **Replace checkout.** Create a checkout configuration and send the buyer to `purchase_url`. Prices are dollars; `billing_period` is days; `metadata` is copied to the payment and membership so you can find your order again.

   ```ts
   import { WhopClient } from "@whop/sdk";

   const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

   const checkout = await whop.checkoutConfigurations.create({
     variant: {
       title: "Pro",
       billing_type: "renewal",
       initial_price: 29.0,
       renewal_price: 29.0,
       billing_period: 30,
       currency: "usd",
     },
     metadata: { order_id: "order_123" },
     redirect_url: "https://example.com/checkout/complete",
   });

   console.log(checkout.purchase_url);
   ```

   For an embedded checkout or your own card form instead of a redirect, use `whop-checkout`.

5. **Replace the webhook handler.** Verify with `unwrapWebhook` on the raw body and branch on `type`:

   ```ts
   import { unwrapWebhook } from "@whop/sdk/helpers";
   import type { Whop } from "@whop/sdk";

   type WhopEvent =
     | { id: string; type: "payment.succeeded"; data: Whop.Payment }
     | { id: string; type: "membership.activated" | "membership.updated"; data: Whop.Membership };

   export async function POST(request: Request): Promise<Response> {
     const event = unwrapWebhook<WhopEvent>(await request.text(), {
       headers: Object.fromEntries(request.headers),
       key: process.env.WHOP_WEBHOOK_SECRET!,
     });

     if (event.type === "payment.succeeded") {
       console.log("fulfill order", event.data.metadata?.order_id, event.data.id);
     }

     return new Response("OK");
   }
   ```

   Deduplicating on `event.id`, retries and the full event list are in `whop-webhooks`.

6. **Replace lookups.** Customer lookups become `members.list({ query })`; "is this subscription active" becomes `users.checkAccess({ id, resource_id })` or the membership's `status`; cancel becomes `memberships.cancel`; the billing portal link is the membership's `manage_url`; refunds are `payments.refund({ id, partial_amount })` in dollars. Details in `whop-billing`.
7. **Move subscribers.** Use the dashboard Stripe migration (Rule 8). Review the preview, the eligibility rules and the exceptions report in [references/processor-mapping.md](references/processor-mapping.md#4-move-existing-subscribers).
8. **Cut over.** Point production at production keys (`WhopEnvironment.Production` is the default), create the production webhook, and remove the old processor's code once the migration report is reconciled.

## Upgrade old Whop code

1. **Find every old call.** Run the search in [references/legacy-map.md](references/legacy-map.md#find-old-whop-code). For raw HTTP, also log responses carrying a `Deprecation` header; their `Link` header's `successor-version` URL is the replacement request.
2. **Replace the client.** `@whop/api` and the old default-imported client become `import { WhopClient } from "@whop/sdk"` with `new WhopClient({ token })`. Sandbox uses `environment: WhopEnvironment.Sandbox`. Webhook verification becomes `unwrapWebhook` from `@whop/sdk/helpers` with the `ws_` secret unchanged. `@whop/api`'s `verifyUserToken` becomes `jwtVerify` from `jose` against `https://api.whop.com/.well-known/jwks.json` with your app ID as `audience` (helper in `whop-apps`).
3. **Rename** namespaces, methods, parameters, response fields and webhook events with the tables in [references/legacy-map.md](references/legacy-map.md). Convert cents to dollars while you're there.
4. **Replace v2 routes and GraphQL operations** with the Current API equivalents in the same file. Updates move from `POST /resource/{id}` to `PATCH /resource/{id}`, which changes only the fields you send. Pagination moves from `page`/`per` to cursors.
5. **Recreate legacy-format webhooks** with `api_version_date` (Rule 7) and port the handler to dotted `v1` event names.
6. **Type-check and test.** Run your type checker against the installed SDK; an unknown property or method is an old name you missed. Then run the flow in sandbox.

What the upgraded code looks like:

```ts
import { WhopClient, WhopEnvironment } from "@whop/sdk";

const whop = new WhopClient({
  token: process.env.WHOP_API_KEY!,
  environment: WhopEnvironment.Sandbox,
});

const variant = await whop.variants.create({
  account_id: "biz_xxxxxxxxxxxxx",
  product_id: "prod_xxxxxxxxxxxxx",
  billing_type: "renewal",
  initial_price: 9.99,
  renewal_price: 9.99,
  billing_period: 30,
});

for await (const membership of await whop.memberships.list({ variant_id: variant.id, status: "active" })) {
  console.log(membership.id, membership.user_id);
}
```

## With the Whop MCP server

The `whop` MCP tools act on the signed-in user's **live** account and can't reach sandbox (`whop-api` covers connecting, `intent`/`intent_id`, and prepare-and-confirm). Its `docs_search` and `docs_query` read the docs pages this skill links. Use the tools to fill in and debug the code, not to replace it:

- Find old webhooks before moving the handler: `webhooks_list` shows each webhook's `api_version` (`v2` and `v5` are legacy) and `api_version_date`. Results include `webhook_secret`: never print it.
- Check the new code against real data: `products_list`, `variants_list`, `memberships_list`, `payments_list`.
- Moving existing Stripe subscribers is a dashboard migration (Rule 8), not an MCP or API call.

## Verify

1. Re-run the old-name search from [references/legacy-map.md](references/legacy-map.md#find-old-whop-code); it should find nothing outside comments and migrations.
2. Type-check against the installed `@whop/sdk`.
3. In sandbox, buy with test card `4242 4242 4242 4242` through the new checkout and confirm `payment.succeeded` reached the new handler once, with your `metadata`.
4. Check a migrated or test membership with `users.checkAccess` and confirm cancellation and refund paths against sandbox data.
5. Grep request logs for responses with a `Deprecation` header; there should be none.

When you're done, tell the user what changed, which environment it targets (sandbox or production; if that isn't decided yet, say so and recommend sandbox first), which of these checks you ran, and what is still unverified.

## Errors

If the same call fails twice, stop retrying it. Read the whole error (status, body and request ID), check the docs page and the installed SDK types, then change the request or the approach.

| Symptom | Cause | Fix |
|---|---|---|
| `Property 'x' does not exist` after upgrading | Old namespace or parameter name | Look it up in the legacy map; use the current name |
| Prices 100× too high | Cents sent where dollars are expected | Divide by 100; Whop amounts are major units |
| `403` on a call that worked on v2 | Key lacks the permission for the Current endpoint | Add the permission in the dashboard's Developer page |
| `404` on `GET /members/{id}` | Passed a user or Discord ID | It takes only `mber_`; search with `members.list({ user_ids })` or `memberships.list({ external_account })` |
| `410 Gone` | Endpoint retired at your version (withdrawals, ad reports) | Use the successor in the changelog |
| `400` on `POST /transfers` | Missing `type` | Send `type: "balance"` |
| Webhook payload has `company_id` | Webhook unpinned or pinned before `2026-08-14` | Recreate it with a current `api_version_date` |
| Handler never sees the old event names | Legacy v2 events don't exist on `v1` webhooks | Subscribe to the `v1` names in the legacy map |
| `400` creating a webhook with `api_version` | New webhooks are always `v1` | Drop `api_version`; pin the shape with `api_version_date` |

## References

- [references/legacy-map.md](references/legacy-map.md): read when upgrading old Whop code. Search command, every old → new name, v2 routes and GraphQL operations.
- [references/processor-mapping.md](references/processor-mapping.md): read when moving from Stripe or another processor. Codebase scans, the concept map, and moving subscribers.
- [references/skill-feedback.md](references/skill-feedback.md): read when the user says this skill gave wrong, outdated or missing guidance, or the docs contradicted it during the task.
