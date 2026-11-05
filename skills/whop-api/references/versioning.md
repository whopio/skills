# API versions

The Current API is versioned by date. Breaking changes ship only inside a new dated version you opt into. New endpoints and new optional fields reach every version.

## Which version a request gets

| You send | You get |
|---|---|
| `Api-Version-Date: 2026-07-23` | The API as it worked on that date |
| No header, the API key has a stored pin | The key's pinned version |
| No header, no pin | The original `2025-01-01` behavior |
| An unknown date | A `400` listing the supported versions |

- An explicit header always beats the key's pin, so you can test an upgrade per request before changing anything saved.
- Keys created before pins existed have no pin and get `2025-01-01`. Newly created keys are pinned to the latest released version.
- Version labels can carry a suffix (`2026-10-27-2`, `2026-10-29-8`) when several changes ship on one day. Send the full label.

## What the SDKs send

Official SDKs send the version they were generated against on every request, so the key's pin doesn't apply to SDK calls. `@whop/sdk` 2.7.0 sends `2026-10-28`. Override it for the whole client or one call:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({
  token: process.env.WHOP_API_KEY!,
  apiVersionDate: "2026-10-28",
});

const variants = await whop.variants.list(
  { account_id: "biz_xxxxxxxxxxxxx" },
  { apiVersionDate: "2026-10-28" },
);
```

Overriding the version changes the response shape but not the SDK's TypeScript types. To move to a newer version, upgrade the SDK so the types match.

Raw HTTP:

```bash
curl https://api.whop.com/api/v1/variants \
  -H "Authorization: Bearer $WHOP_API_KEY" \
  -H "Api-Version-Date: 2026-10-28"
```

## Upgrading a pin

1. Find your current version (the header you send, the key's pin, or the SDK version).
2. Read **every** changelog entry after it, up to your target. Not just the target month.
3. Test the target with the header on a few calls in sandbox, then upgrade the SDK or change the saved pin.

Entries that break the most integrations:

| Version | Change |
|---|---|
| `2026-07-23` | Members and memberships become native: `cancel_at_period_end` schedules a cancel, the `cancel` action ends access now, `extend` replaces `add_free_days` |
| `2026-08-14` | Webhook envelopes carry `account_id` instead of `company_id` |
| `2026-08-21` | Payout statuses rebuilt; payout money fields become decimal strings; idempotency only in the `Idempotency-Key` header |
| `2026-09-02-1` | Payments become native: `account_id`, money objects, singular list filters, `201 Created` on create |
| `2026-10-09-1` | `POST /transfers` requires `type` (`balance` or `claim_link`) |
| `2026-11-02-1` | A draft invoice's customer is fixed once set: an update with a different `member_id` (or `null`) returns `400`; void the draft and create a new invoice instead |
| `2026-11-03` | `POST /payouts` requires `quote_token` from `POST /payouts/quotes`; without one it returns `400` `invalid_payout_quote` |
| `2026-11-03-1` | Connected accounts are renamed subaccounts: `include_connected_accounts` becomes `include_subaccounts` on payment and dispute lists and summaries, and `covers_connected_account_negative_balances` becomes `covers_subaccount_negative_balances` in account preferences |

The last three are newer than the `2026-10-28` that `@whop/sdk` 2.7.0 sends, so SDK code still uses the old names until you upgrade the SDK or override `apiVersionDate`.
| `2026-10-27-1` | `/plans` becomes `/variants`; `billing_type` replaces the old billing field; `default_variant` on products |
| `2026-10-27-2` | Every other resource says `variant_id` / `variant` instead of the old plan names |

## Deprecated endpoints

Deprecated endpoints keep answering on every version and say so in headers: `Deprecation`, a `Link` with `rel="successor-version"` naming the replacement, and eventually a `Sunset` date. Log responses that carry `Deprecation` to find calls you still need to move. Retired endpoints answer `410 Gone` at the versions that retired them.

## Webhooks

Webhook payloads follow the webhook's own `api_version_date`, set when you create the webhook, not your request header. See `whop-webhooks`.

## Sources

- https://docs.whop.com/developer/api/versioning.md
- https://docs.whop.com/developer/quickstart.md
- https://docs.whop.com/api-reference/beta/overview.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
