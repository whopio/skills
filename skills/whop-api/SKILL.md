---
name: whop-api
description: >-
  Set up the Whop API: credentials (API keys, user tokens, OAuth tokens),
  @whop/sdk in TypeScript, Python or Ruby, sandbox vs production, IDs, dollar
  amounts, versions, idempotency keys, pagination, errors, and the Whop MCP
  server. Use when: "set up the Whop SDK", "Whop API key", "Whop sandbox",
  "which Whop token do I need", "Whop 401", "Whop 403 forbidden",
  "Api-Version-Date", "idempotency key", "what is a biz_ ID", "find my Whop
  product ID", "Whop MCP". NOT for: taking payments (whop-checkout), webhooks
  (whop-webhooks), memberships (whop-billing), payouts (whop-payouts),
  marketplaces (whop-platforms), apps inside Whop or Sign in with Whop
  (whop-apps), chat (whop-communities), old Whop or Stripe code (whop-migrate).
license: Apache-2.0
metadata:
  author: whop
  version: "0.4.0"
---

# Whop API

The foundation for every Whop integration: which credential to use, how to set up the SDK against sandbox or production, and the request conventions (versions, idempotency, pagination, errors) every other Whop skill assumes.

## Before you start

1. **Inspect the project first.** Note the installed `@whop/sdk` version (`node_modules/@whop/sdk/package.json`; `whop-sdk` in Python, `whop_sdk` in Ruby), the framework, and whether the client targets sandbox or production. On `@whop/api` or `@whop/sdk` below 2.0, upgrade first (`whop-migrate`). If a name here doesn't compile, search the installed `node_modules/@whop/sdk/reference.md` for it and trust that over this skill.
2. Fetch `https://docs.whop.com/developer/quickstart.md`, `https://docs.whop.com/developer/guides/auth-scoping.md` and the changelog at `https://docs.whop.com/developer/api/versioning.md`. If they disagree with this skill, follow the docs and tell the user (see [references/skill-feedback.md](references/skill-feedback.md)).
3. Confirm what is being built. Building Whop into your own product starts with an API key. Building an app that runs inside Whop starts with the Whop CLI, not an API key; that is `whop-apps`.
4. Confirm the environment. Sandbox (`https://sandbox.whop.com`, API `https://sandbox-api.whop.com/api/v1`) and production (`https://whop.com`, API `https://api.whop.com/api/v1`) share nothing: separate dashboards, keys, webhooks and data.
5. Confirm the language. The docs show SDKs for TypeScript (`@whop/sdk`), Python (`whop-sdk`) and Ruby (`whop_sdk`).
6. Other `whop-*` skills named here are optional. When one isn't installed, use the matching guide linked from `https://docs.whop.com/developer/start.md` instead.

## Rules

1. **API keys stay on the server.** Never put an Account or App API key in browser code, a mobile app, an iframe page, or a public repo. Clients call your server; your server calls Whop.
2. **Sandbox and production keys look identical.** Nothing in the key string says which environment it belongs to. Store them under different names and check which one you hold before running anything that moves money.
3. **Switch environments with `environment`, not a URL.** SDK 2.x takes `environment: WhopEnvironment.Sandbox`. A `baseUrl` override sends every request to one host, and operations that must reach another host are refused. The Python 2.x client has no `base_url` at all.
4. **IDs are prefixed tags**, never numeric: `biz_` account, `user_` user, `prod_` product, `plan_` variant, `mem_` membership, `pay_` payment. Variants keep the `plan_` prefix. Full table in [references/concepts.md](references/concepts.md).
5. **Money is in dollars** (major currency units): `initial_price: 10.0` is $10.00, `transfers.create({ amount: 25 })` moves $25.00, `payouts.create({ amount })` is in the payout currency. Never send cents.
6. **Pin a version.** The TypeScript SDK 2.7.0 sends `Api-Version-Date: 2026-10-28` on every request. Raw HTTP calls must send the header themselves; without it (and without a pin on the API key) you get the original `2025-01-01` shapes.
7. **Send an `Idempotency-Key` on every `POST` that moves money or creates something you can't create twice.** The SDK retries `408`, `429` and `5xx` twice by default, and a retried `POST` without a key can run twice. Generate one key per operation and reuse it only to retry that operation.
8. **Don't retry `400`, `401`, `403`, `404` or `422` unchanged.** Fix the request first. With an idempotency key, a `4xx` is replayed for 24 hours; send a new key with the corrected request.
9. **Build on the Current API.** Use resources under `/api-reference/beta` and the SDK's current namespaces (`accounts`, `variants`, `payouts`, `deposits`). Use a Legacy endpoint only when [the stability page](https://docs.whop.com/api-reference/stability.md) lists no Current successor.
10. **Minted tokens always get an explicit `scoped_actions` list.** Omit it and the token inherits every permission of the key that minted it.
11. **The Whop MCP server is for the agent, the SDK is for the app.** MCP tools act on the signed-in user's live account and can't reach sandbox. Use them to look up IDs and inspect production state, and write SDK code for anything the app does. Consequential MCP tools prepare first and execute only after the user approves. See [references/mcp.md](references/mcp.md).

## Pick a credential

| Credential | Acts as | Lives | Use when |
|---|---|---|---|
| Account API key | Your account (`biz_`) | Your server | Your backend works on your own business and its connected accounts. Most integrations need only this |
| App API key | Your app | Your server | Your app reaches every account that installed it (`whop-apps`) |
| Account-scoped user token | One user inside one account | Minted on your server, used in your client | Your product has its own users who reach Whop without a Whop sign-in |
| Account access token | Your account, narrowed | Minted on your server, used in your client | A client needs short-lived account access with no user attached, such as an embedded component |
| iframe user token | The user viewing your app | Sent by Whop in `x-whop-user-token`, verified by you | Your app renders inside Whop (`whop-apps`) |
| OAuth token | A user who signed in to Whop | Your server, after the OAuth flow | "Sign in with Whop", acting for a user (`whop-apps`) |

Create an Account API key in the dashboard's Developer page under **Account API Keys** (sandbox: `sandbox.whop.com/dashboard/developer`). Start on the Admin role for a first call, then switch to a custom permission set. Details for every credential: [references/credentials.md](references/credentials.md).

## Set up the client

```bash
pnpm add @whop/sdk        # Python: pip install whop-sdk   Ruby: gem install whop_sdk
```

```ts
import { WhopClient, WhopEnvironment } from "@whop/sdk";

const whop = new WhopClient({
  token: process.env.WHOP_API_KEY!,
  environment:
    process.env.WHOP_ENVIRONMENT === "sandbox" ? WhopEnvironment.Sandbox : WhopEnvironment.Production,
});

const account = await whop.accounts.me();
console.log(account.id);
```

`accounts.me()` returns the account the key belongs to; its ID starts with `biz_`. Production is the default environment.

```python
import os
from whop_sdk import Whop, WhopEnvironment

client = Whop(token=os.environ["WHOP_API_KEY"], environment=WhopEnvironment.SANDBOX)
print(client.accounts.me().id)
```

```ruby
require "whop_sdk"

client = Whop_sdk::Client.new(token: ENV.fetch("WHOP_API_KEY"), environment: Whop_sdk::Environment::SANDBOX)
puts client.accounts.me.id
```

Leave out `environment` (or use production keys with the production environment) to go live.

## Mint a scoped token for a client

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const { token, expires_at } = await whop.accessTokens.create({
  account_id: "biz_xxxxxxxxxxxxx",
  user_id: "user_xxxxxxxxxxxxx",
  scoped_actions: ["chat:read", "chat:message:create"],
});
```

Pass `account_id` and `user_id` for an account-scoped user token, or `account_id` alone for an account access token. Tokens last one hour by default and at most three (`expires_at`). Mint on demand; don't cache.

## Make requests safely

Money-moving `POST` with an idempotency key (here a $25.00 transfer):

```ts
import { randomUUID } from "node:crypto";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const transfer = await whop.transfers.create(
  {
    type: "balance",
    amount: 25.0,
    currency: "usd",
    origin_id: "biz_xxxxxxxxxxxxx",
    destination_id: "user_xxxxxxxxxxxxx",
  },
  { idempotencyKey: randomUUID() },
);
```

Store the key with your own record before calling, so a retry after a crash reuses it. Keys are any unique string up to 255 bytes and last 24 hours.

List endpoints are cursor-paginated (`data` plus `page_info`; pass `first` and `after`). The SDK pages for you:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

for await (const membership of await whop.memberships.list({ product_id: "prod_xxxxxxxxxxxxx" })) {
  console.log(membership.id, membership.status);
}
```

Errors throw a subclass of `WhopError` carrying the status, the parsed body, and the request ID:

```ts
import { WhopClient, WhopError } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

try {
  await whop.accounts.me();
} catch (error) {
  if (error instanceof WhopError) {
    console.error(error.statusCode, error.body, error.requestId);
  }
  throw error;
}
```

Versions, pins and upgrades: [references/versioning.md](references/versioning.md). Idempotency, pagination, error bodies and rate limits: [references/requests.md](references/requests.md).

## Look things up live

Facts change faster than this skill. Before writing a call you haven't verified:

- With the Whop MCP server connected, search first: `docs_search` finds the page, and `docs_query` reads it (`head -200 /<path>.mdx`). Same pages, no web fetch.
- Any docs page as Markdown: append `.md` to its URL, e.g. `https://docs.whop.com/developer/guides/webhooks.md`.
- The index of every page: `https://docs.whop.com/llms.txt`.
- The API contract: `https://api.whop.com/api/v1/openapi.json`.
- Which resources are Current vs Legacy: `https://docs.whop.com/api-reference/stability.md`.
- The SDK itself: the installed `@whop/sdk` package's `reference.md` and request types are what compiles. If docs and types disagree on a parameter name, trust the types for your installed version and check the changelog.

## Use the Whop MCP server

When the `whop` MCP tools are available, use them to fill in what the code needs, instead of asking the user to copy IDs out of the dashboard:

1. `connection_status` shows who is signed in. Get the business from `accounts_list` and pass `account_id` explicitly.
2. Look things up: `products_list` and `variants_list` for the IDs a checkout needs, `webhooks_list` for existing endpoints, `api-keys_permissions` for what a key can do.
3. Every operation tool takes `intent` (the user's request) and `intent_id` (one UUID per user message).
4. Anything that creates, changes or deletes data is a real production change. Do it only when the user asks, show the prepared preview, and confirm with the token and a stable `idempotency_key`.

Tool naming, prepare-and-confirm, what the plugin's connection excludes, and error codes: [references/mcp.md](references/mcp.md).

## Route to the right skill

| Goal | Skill |
|---|---|
| Sell something: checkout links, Checkout element, card fields, products and variants | `whop-checkout` |
| Memberships, access checks, cancellations, refunds, disputes, invoices | `whop-billing` |
| Receive and verify webhooks | `whop-webhooks` |
| Payouts, transfers, deposits, balances | `whop-payouts` |
| Marketplace with connected accounts | `whop-platforms` |
| App inside Whop, OAuth, iframe user tokens | `whop-apps` |
| Chat, DMs, forums, courses | `whop-communities` |
| Coming from Stripe or older Whop API names | `whop-migrate` |

## Verify

1. Create a sandbox key at `sandbox.whop.com/dashboard/developer` and run the setup snippet with `WHOP_ENVIRONMENT=sandbox`. It should print a `biz_` ID.
2. Check what the key can do before you hit a `403`: `whop.permissions.list({ resource_id: "biz_xxxxxxxxxxxxx", actions: "payment:basic:read" })` returns each action with `granted`.
3. Re-send a money-moving `POST` with the same idempotency key and confirm the response carries `Idempotent-Replayed: true` and nothing ran twice.

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `401` | Key missing, wrong, or from the other environment | Load the key on the server; match sandbox keys to `WhopEnvironment.Sandbox` |
| `403` | Key valid but lacks the permission, or the resource belongs to another account | Add the permission to the key (or the app's permissions); check the `account_id` you pass is yours or a connected account |
| `404` | Wrong ID prefix, numeric ID, wrong environment, or a Legacy-only route | Use the tag (`biz_`, `plan_`, `mem_`...); check the environment and the stability page |
| `400` naming the version | Unknown `Api-Version-Date` | Use a date from the changelog |
| `400` `idempotency_key_mismatch` | Same key, different request | New key for a new request |
| `409` `idempotency_request_in_progress` | Retried while the first is running | Wait, then retry with the same key |
| `429` | Over 600 requests per minute for that operation and credential | Wait the time in `error.message`, back off |
| Response shape differs from the docs | Unpinned raw HTTP call getting `2025-01-01` shapes | Send `Api-Version-Date` or use the SDK |

## References

- [references/credentials.md](references/credentials.md): read when choosing or minting a credential, scoping a key, or handling iframe and OAuth tokens.
- [references/versioning.md](references/versioning.md): read when pinning a version, upgrading a pin, or a response changed shape.
- [references/requests.md](references/requests.md): read for idempotency details, pagination in each language, error bodies, retries and rate limits.
- [references/concepts.md](references/concepts.md): read when you meet an unfamiliar object or ID prefix.
- [references/mcp.md](references/mcp.md): read before calling Whop MCP tools: when to use them instead of SDK code, connecting, prepare-and-confirm, idempotency, and errors.
- [references/skill-feedback.md](references/skill-feedback.md): read when the user says this skill gave wrong, outdated or missing guidance, or the docs contradicted it during the task.
