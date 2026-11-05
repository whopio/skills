---
name: whop
description: >-
  Start here for building on Whop: inspect the project, then load the whop-*
  skill that fits the goal. Covers projects that already use Whop (@whop/sdk,
  whop-sdk, WHOP_API_KEY) even when the user doesn't say "Whop", and reporting
  a problem with a Whop skill. Use when: "build on Whop", "integrate Whop",
  "what can I build with Whop", "which Whop skill", "add payments", "sell a
  subscription", "add a paywall", "pay my users", "build a marketplace", "add
  chat to my app", "the Whop skill was wrong", "report a problem with a Whop
  skill". NOT for: a task one skill clearly covers (load it directly:
  whop-checkout, whop-webhooks, whop-billing...), a project on another
  processor with no plan to move (whop-migrate only when moving), running a
  live Whop store by hand (use the whop CLI).
license: Apache-2.0
metadata:
  author: whop
  version: "0.4.0"
---

# Whop

Pick the right Whop skill for the user's goal, after checking what the project already has. Every `whop-*` skill is optional: when one isn't installed, use the docs page in its row instead.

## Inspect the project first

Look before asking. These answers decide which skill applies and how its code must look.

1. **Language and Whop packages.** `package.json` and the lockfile (`@whop/sdk`, `@whop/elements-react`, `@whop/elements`), `requirements.txt` or `pyproject.toml` (`whop-sdk`), `Gemfile` (`whop_sdk`). Note the installed `@whop/sdk` version: `node_modules/@whop/sdk/package.json`.
2. **Old Whop code.** The `@whop/api` package, `@whop/sdk` below 2.0, a client built from a `Whop` class instead of `WhopClient`, calls on `plans` or `companies`, `company_id`, or `api/v2` URLs mean the code predates the current API. Fix that first with `whop-migrate`; don't add new code on top.
3. **Another processor.** `stripe`, `@stripe/`, `paddle`, `lemonsqueezy` and the like. Only move it to Whop if the user asks (`whop-migrate`).
4. **Framework and server boundary.** Where server code runs (API routes, server actions, a backend folder), so keys and webhook handlers go there.
5. **Environment.** Env var names (`WHOP_API_KEY`, `WHOP_WEBHOOK_SECRET`, `WHOP_ENVIRONMENT`) and whether the client targets sandbox (`WhopEnvironment.Sandbox`, `sandbox-api.whop.com`) or production. Read names, never print values.
6. **Existing Whop code.** Search for `WhopClient`, `unwrapWebhook`, `purchase_url`, `checkAccess` and `webhooks/whop` routes. Extend what's there rather than adding a second client or handler.

The installed SDK is the source of truth for names on that version: `node_modules/@whop/sdk/reference.md` documents every method. It is long, so search it for the method you need (`grep -n "checkAccess"`) instead of reading it whole. Your memory of the Whop API is likely out of date; prefer the docs and the installed types.

## Rules

1. **Money is in dollars** (major currency units) in the API: `renewal_price: 29` is $29.00. Only Elements amounts on the page are in cents.
2. **API keys stay on the server.** Never in browser code, a mobile app or a `NEXT_PUBLIC_` variable.
3. **Build and test in sandbox first.** Sandbox and production share nothing, and their keys look identical.
4. **Fulfill from the `payment.succeeded` webhook**, not from a return page or a client callback.
5. **Use current names:** `variants` (not plans), `accounts` and `account_id` (not companies), `payouts` (not withdrawals), `deposits` (not top-ups), `unwrapWebhook` from `@whop/sdk/helpers`.
6. **Don't loop.** If the same call fails twice, stop: read the error body, check the docs page and the installed types, then change the approach.

## Pick a skill

| The user wants to | Skill | Docs page if the skill isn't installed |
|---|---|---|
| Set up the SDK, API keys, sandbox, tokens; fix `401`/`403`; look up IDs | `whop-api` | `developer/quickstart` |
| Sell something: checkout link, embedded checkout, card form, Apple Pay, products and prices | `whop-checkout` | `developer/guides/accept-payments` |
| Run code when something happens: fulfill an order, grant or revoke access | `whop-webhooks` | `developer/guides/webhooks` |
| Check access, cancel or pause subscriptions, refunds, invoices, disputes, fraud rules | `whop-billing` | `developer/guides/memberships` |
| Pay people: transfers, payouts, payout portal, balances, deposits | `whop-payouts` | `developer/platforms/manual-payouts` |
| Run a marketplace: connected accounts, seller onboarding, KYC, platform fees | `whop-platforms` | `developer/platforms/quickstart` |
| Build an app that runs inside Whop: views, user tokens, permissions, OAuth | `whop-apps` | `developer/apps/overview` |
| Chat, DMs, support chats, forums, courses in your own product | `whop-communities` | `developer/guides/chat/quickstart` |
| Move from Stripe or another processor, or upgrade old Whop code | `whop-migrate` | `developer/api/migrate-from-previous-versions` |

Each docs page is at `https://docs.whop.com/<path>.md`. Load the skill for the user's first step, and load the next one when the work reaches it.

## Common combinations

| Goal | Skills, in order |
|---|---|
| Sell a subscription and gate content on it | `whop-checkout` → `whop-webhooks` → `whop-billing` |
| Sell a one-time product and deliver it | `whop-checkout` → `whop-webhooks` |
| Marketplace that takes a cut and pays sellers | `whop-platforms` → `whop-checkout` → `whop-payouts` → `whop-webhooks` |
| Pay creators or affiliates from your balance | `whop-payouts` (+ `whop-platforms` if they need accounts first) |
| App in the Whop App Store with paid features | `whop-apps` → `whop-checkout` → `whop-webhooks` |
| Community product with chat for paying members | `whop-communities` → `whop-billing` |
| Replace Stripe with Whop | `whop-migrate` → `whop-checkout` → `whop-webhooks` → `whop-billing` |

## Not covered by a skill

Fetch the guide and follow it: ads and conversion tracking (`developer/ads/overview`), revenue and member stats (`developer/guides/stats`), affiliates (`developer/guides/affiliates`), hosted websites (`developer/websites/overview`), bounties (`developer/bounties/overview`). Anything else: start at `https://docs.whop.com/developer/start.md`, or the index at `https://docs.whop.com/llms.txt` (follow its "For Developers" index down to the page).

## With the Whop MCP server

If the `whop` MCP tools are connected, use them to look things up for the code you write (`accounts_list`, `products_list`, `variants_list`, `webhooks_list`) and to search the docs (`docs_search`, then `docs_query`). They act on the signed-in user's live production account and can't reach sandbox, so test code with sandbox API keys, not MCP. Tools that change data return a preview first; run them only after the user approves that preview.

## Finish

Report what changed, which environment it targets (sandbox or production), what you ran to check it, and what is still unverified, such as a webhook never delivered by Whop or a flow only tested with sandbox cards.

## References

- [references/skill-feedback.md](references/skill-feedback.md): read when the user says a Whop skill gave wrong, outdated or missing guidance, or the docs contradicted a skill during the task.
