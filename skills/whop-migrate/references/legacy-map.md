# Old Whop names → current names

Every "new" entry below exists in `@whop/sdk` 2.7.0 (`reference.md` and its request types) or in the current docs. If your installed SDK is newer and a name isn't there, check the changelog at `https://docs.whop.com/developer/api/versioning.md` before guessing.

## Find old Whop code

Run from the repo root and fix every hit (the list doubles as the "old" column below):

```bash
rg -n -g '!node_modules' -g '!*.lock' \
  -e '@whop/api' -e 'WhopServerSdk' -e 'makeWhopServerSdk' -e 'withUser\(' -e 'withCompany\(' \
  -e 'import Whop from "@whop/sdk"' -e 'new Whop\(' -e 'apiKey:' -e 'appID' -e 'webhookKey' -e 'btoa\(' -e 'webhooks\.unwrap' \
  -e 'api\.whop\.com/(api/)?v2' -e 'public-graphql' -e 'mcp\.whop\.com/sse' \
  -e '\.plans\.' -e '\.companies\.' -e '\.withdrawals\.' -e '\.topups\.' -e 'ledgerAccounts' -e 'feeMarkups' -e 'payoutMethods' \
  -e 'company_id' -e 'parent_company_id' -e 'plan_type' -e 'plan_id' -e 'plan_ids' -e 'default_plan' \
  -e 'went_valid' -e 'went_invalid' -e 'membership\.deactivated' -e 'withdrawal\.(created|updated|reversed)' -e 'payout\.completed' \
  -e 'hosted_kyc' -e 'hosted_payouts' -e 'chargeUser' -e 'checkout_sessions' -e 'access_pass' -e 'add_free_days' \
  -e '@whop/checkout' -e 'WhopCheckoutEmbed' -e '@whop/embedded-components'
```

For raw HTTP integrations, also log every response that carries a `Deprecation` header: v2 and public GraphQL responses carry `Deprecation`, `Sunset` and a `Link` whose `successor-version` URL is the Current API request that replaces the call.

## Packages and client setup

| Old | New | Notes |
|---|---|---|
| `@whop/api` (`WhopServerSdk`, `makeWhopServerSdk`) | `@whop/sdk` (`WhopClient`) | The public GraphQL API behind `@whop/api` stopped on October 26, 2026. `verifyUserToken` from `@whop/api` checks the header locally and keeps working |
| `withUser(...)`, `withCompany(...)` | Pass the user or account ID on each request | No equivalent helper |
| `import Whop from "@whop/sdk"` | `import { WhopClient } from "@whop/sdk"` | 2.x has no default export; types are `import type { Whop } from "@whop/sdk"` |
| `new Whop({ apiKey })` | `new WhopClient({ token })` | |
| `appID` option | none | Pass the App API key as `token` |
| `baseURL` / `baseUrl` pointed at the sandbox | `environment: WhopEnvironment.Sandbox` | Python `WhopEnvironment.SANDBOX`, Ruby `Whop_sdk::Environment::SANDBOX` |
| `webhookKey: btoa(secret)` and `client.webhooks.unwrap(...)` | `unwrapWebhook(body, { headers, key })` from `@whop/sdk/helpers` | Pass the `ws_...` secret unchanged; never base64 it |
| `https://api.whop.com/api/v2/...`, `https://api.whop.com/v2/...` | `https://api.whop.com/api/v1/...` | v2 stops working on November 13, 2026. Same API keys |
| `https://api.whop.com/public-graphql` | `https://api.whop.com/api/v1/...` | Stopped October 26, 2026 |
| `https://mcp.whop.com/sse` | `https://mcp.whop.com/mcp` | Streamable HTTP, browser sign-in |
| `@whop/checkout`, `WhopCheckoutEmbed` | `Checkout` + `CheckoutElement` from `@whop/elements-react`, `loadWhop` from `@whop/elements` | See `whop-checkout` |
| `@whop/embedded-components-*` for payouts or KYC | `@whop/elements-react` / `@whop/elements` (for example `Verifications` + `KycElement`) | Chat still uses the `@whop/embedded-components-*` packages (`whop-communities`) |

## SDK namespaces and methods

| Old | New | Notes |
|---|---|---|
| `client.plans.list/retrieve/create/update/delete` | `client.variants.list/retrieve/create/update/delete` | `/plans` still answers with `Deprecation` headers. Variant IDs keep `plan_` |
| `client.plans.calculateTax` | `client.paymentQuotes.create` | Tax previews are payment quotes |
| `client.companies.retrieve` | `client.accounts.retrieve` | Companies are accounts, same object |
| `client.companies.list` | `client.accounts.list({ parent_account_id })` | |
| `client.companies.create({ parent_company_id, ... })` | `client.accounts.create({ email, title, metadata })` | Called with the platform's Account API key, the new account is created under that platform; there is no parent field |
| `client.companies.update` | `client.accounts.update` | |
| `GET /company` | `client.accounts.me()` (`GET /accounts/me`) | |
| `client.withdrawals.create({ company_id, amount })` | `client.payouts.createQuote(...)`, then `client.payouts.create({ account_id, amount, payout_method_id, quote_token })` | `/withdrawals` list and create return `410` from `2026-08-25-1`; payout IDs keep `wdrl_`. Pass `Idempotency-Key` as a header. `quote_token` is required from `2026-11-03` |
| `client.topups.create` | `client.deposits.create({ destination, amount })` | `destination` is a `biz_` or `user_` ID |
| `client.ledgerAccounts.retrieve` | `client.accounts.retrieve` (read `balances`) | Ledger accounts' Current successor is account balances |
| `client.feeMarkups.list` | `client.accounts.fees.retrieve` / `client.accounts.fees.update` | |
| `client.payoutMethods.list` | `client.payouts.methods.list` | Saved payout methods |
| `client.authorizedUsers.*` | `client.teamMembers.*` | |
| `client.socialAccounts.*` | `client.externalAccounts.*` | IDs keep `sacc_` |
| `client.paymentMethodDomains.*` | `client.domains.*` with `apple_pay` | |
| `client.users.checkAccess(companyId, { id })` | `client.users.checkAccess({ id, resource_id })` | `resource_id` is a `biz_`, `prod_` or `exp_` ID |
| `chargeUser` | `client.payments.create({ member_id, payment_method_id, ... })` | |
| `payUser` | `client.transfers.create({ type: "balance", amount, currency, origin_id, destination_id })` | `type` is required from `2026-10-09-1` |
| `createCheckoutSession` | `client.checkoutConfigurations.create` | Returns `purchase_url` |
| `accountLinks.create({ use_case: "hosted_kyc" })` | `accountLinks.create({ use_case: "account_onboarding" })` | |
| `accountLinks.create({ use_case: "hosted_payouts" })` | `accountLinks.create({ use_case: "payouts_portal" })` | |

## Parameters and fields

| Old | New | Notes |
|---|---|---|
| `company_id` (requests, filters, responses) | `account_id` | Some Legacy-only resources still take `company_id`; follow the SDK type for that method |
| `company` on products, variants, reviews | `account` | |
| `parent_account_id` on accounts | `parent_account` (`id`, `title`, `route`, `logo_url`) | From `2026-07-31` |
| `plan_type` | `billing_type` (`one_time` or `renewal`) | On variants, inline variants and embedded variants |
| `plan_types` filter | `billing_types` | |
| `plan_id`, `plan_ids` | `variant_id`, `variant_ids` | Memberships, members, waitlist entries, payments, disputes, invoices, checkout configurations, promo codes |
| `plan` (inline on checkout configurations, payments, invoice items) | `variant` | The Elements `plan` property keeps its name for compatibility |
| `plan_title` on line items | `variant_title` | |
| `default_plan` on products | `default_variant` | |
| `related.plan` on events | `related.variant` | |
| `access_pass`, `access_passes` | `product`, `products` | Product IDs are `prod_` |
| `checkout_sessions` | `checkout_configurations` | |
| `add_free_days` | `memberships.extend({ id, days })` | |
| v2 `terminate` | `memberships.cancel({ id })` | Omitting `cancel_at_period_end` revokes access now; pass `true` to keep access until renewal |
| `discord_id=<id>` | `external_account=discord_<id>` on `memberships.list` | |
| `last_payment_attempt`, `next_payment_attempt` | `last_payment_attempt_at`, `next_payment_attempt_at` | |
| `pdf_url` on payments | `payments.generatePdf({ id })` | |
| `idempotency_key` body field on payouts | `Idempotency-Key` header | |
| webhook `api_version` input (`v2`, `v5`) | `api_version_date` | New webhooks are always `v1` |
| v2 `page` / `per`, `pagination.current_page` | `first` / `after`, `page_info.end_cursor` / `has_next_page` | |
| Amounts in cents (`initial_price: 5000`, `amount: 4500`) | Dollars (`initial_price: 50.0`, `amount: 45.0`) | Prices, transfers, payouts, deposits and refunds are in major units |

## Webhook events

| Old | New | Notes |
|---|---|---|
| `membership.went_valid` | `membership.activated` | Legacy `v2`/`v5` webhooks only. Activations also arrive as `membership.updated` |
| `membership.went_invalid`, `membership.deactivated` | `membership.updated` | Read `previous_attributes.status` for the status it left |
| `membership.cancel_at_period_end_changed` | `membership.updated` | Still delivered, no longer documented |
| `withdrawal.created`, `withdrawal.updated`, `withdrawal.reversed` | `payout.created`, `payout.updated`, `payout.reversed` | Old names can't be selected on new webhooks |
| `payout.completed` | `payout.updated` with `status: "completed"` | Not a Whop event |
| `company_id` in the envelope | `account_id` | Webhooks pinned `2026-08-14` or later |
| Underscored names (`payment_succeeded`) | Dotted names (`payment.succeeded`) in `type` | |

## v2 routes

| v2 route | Current API |
|---|---|
| `GET /memberships`, `GET /licenses` | `GET /memberships` (`license_key` on each membership) |
| `POST /memberships/{id}` | `PATCH /memberships/{id}` (send `metadata` to merge keys) |
| `POST /memberships/{id}/cancel` | `POST /memberships/{id}/cancel` |
| `POST /memberships/{id}/terminate` | `POST /memberships/{id}/cancel` without `cancel_at_period_end` |
| `POST /memberships/{id}/add_free_days` | `POST /memberships/{id}/extend` |
| `POST /memberships/{id}/validate_license` | `GET /memberships/{id}` (accepts the license key) and `PATCH /memberships/{id}` to bind a machine in `metadata`, from your server |
| `GET /customers`, `GET /members/{search}` | `GET /members` with `user_ids` or `query`. `GET /members/{id}` takes only `mber_` |
| `GET /payment_fees?payment_id=` | `GET /payments/{id}/fees` |
| `POST /checkout_requests` | `POST /payments` with `member_id` and `payment_method_id` |
| `GET /checkout_requests/{id}` | `GET /payments/{id}` |
| `GET/POST/DELETE /checkout_sessions[/{id}]` | `/checkout_configurations[/{id}]` |
| `GET /access_passes[/{id}]`, `POST /access_passes/{id}` | `GET /products[/{id}]`, `PATCH /products/{id}` |
| `GET/POST /plans`, `POST /plans/{id}` | `GET/POST /variants`, `PATCH /variants/{id}` |
| `POST /plans/{id}/create_quick_link` | `POST /variants` with `visibility: "quick_link"`, `stock` and the price fields (the Current API doesn't copy an existing variant) |
| `POST /promo_codes/{id}` (status) | `POST /promo_codes/{id}/activate`, `POST /promo_codes/{id}/deactivate` |
| `POST /experiences/{id}`, `POST /webhooks/{id}` | `PATCH /experiences/{id}`, `PATCH /webhooks/{id}` |

Any v2 `POST /resource/{id}` update becomes `PATCH /resource/{id}`, which changes only the fields you send.

## Public GraphQL operations

| GraphQL operation | Current API |
|---|---|
| `checkIfUserHasAccessToExperience` / `...ToAccessPass` / `...ToCompany` | `users.checkAccess({ id, resource_id })` with an `exp_`, `prod_` or `biz_` ID. Response `has_access`, `access_level` |
| `getCurrentUser` | `users.me()` (with an app key: read the user ID from the iframe token, then `users.retrieve`) |
| `getUser` | `users.retrieve` |
| `listUsersForExperience` | `members.list({ product_ids })` |
| `getCompany` | `accounts.me()` |
| `listAccessPasses`, `getAccessPass`, `createAccessPass`, `updateAccessPass`, `deleteAccessPass` | `products.list/retrieve/create/update/delete` |
| `listPlans` | `variants.list` |
| `listMemberships`, `listMembers`, `getMember` | `memberships.list`, `members.list`, `members.retrieve` |
| `listReceiptsForCompany` | `payments.list` |
| `listMessagesFromChat`, `sendMessageToChat` | `messages.list`, `messages.create` with `channel_id`. Subscribe to `chat.message.created` instead of polling |
| `sendDirectMessageToUser` | `dmChannels.create({ with_user_ids })`, then `messages.create` |
| `uploadMedia`, `processAttachment`, `getAttachment` | `files.create`, `files.complete`, `files.retrieve` |
| `sendPushNotification` | `notifications.create` |
| `listWebhooks`, `createWebhook`, `updateWebhook`, `deleteWebhook`, `testWebhook` | `webhooks.list/create/update/delete/test` |

GraphQL `camelCase` fields (`hasAccess`) are `snake_case` (`has_access`). Stored IDs keep their prefixes and still work. Anything not listed: search the API reference for the resource.

## Sources

- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
- https://docs.whop.com/developer/api/versioning.md
- https://docs.whop.com/api-reference/stability.md
- https://docs.whop.com/developer/guides/sandbox.md
- https://docs.whop.com/developer/guides/memberships.md
- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/developer/guides/embed-checkout.md
- https://docs.whop.com/developer/platforms/enroll-subaccounts.md
- https://docs.whop.com/developer/platforms/render-payout-portal.md
- https://docs.whop.com/developer/guides/ai_and_mcp.md
