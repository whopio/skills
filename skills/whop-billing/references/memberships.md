# Memberships, members and license keys

A **membership** (`mem_...`) is one user's relationship with one product: access, billing status and renewal schedule. Checkout creates it; you don't. A **member** (`mber_...`) is one record per customer of an account, across all their memberships. Grant or revoke access through memberships, not members.

## Statuses

| `status` | Grants access | Meaning |
|---|---|---|
| `trialing` | Yes | In a free trial |
| `active` | Yes | Paid and renewing |
| `completed` | Yes | One-time purchase, kept for good |
| `past_due` | Your call | Grace period after a failed renewal payment while Whop retries |
| `canceled` | No | Ended |
| `expired` | No | Ended |
| `unresolved` | | Listed in the API's status options; read the docs before relying on it |

`cancel_at_period_end: true` on an `active` membership means it's still active but won't renew. The SDK's status type also lists `drafted` (an invoice's membership before it's paid has no access) and `canceling`; the `memberships.list` `status` filter accepts derived buckets such as `canceling`, `paused` and `expiring`.

Prefer `users.checkAccess` for gating: it already applies these rules and follows renewals, cancellations and refunds.

## Retrieve and list

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const membership = await whop.memberships.retrieve({ id: "mem_xxxxxxxxxxxxx" });
console.log(membership.status, membership.cancel_at_period_end, membership.current_period_end);

const page = await whop.memberships.list({
  account_id: "biz_xxxxxxxxxxxxx",
  user_id: "user_xxxxxxxxxxxxx",
  statuses: ["active", "trialing"],
});

for await (const item of page) {
  console.log(item.id, item.product_id, item.variant_id);
}
```

Other `list` filters include `member_id`, `product_id` and `variant_id`. Useful fields: `user_id`, `member_id`, `variant_id`, `product_id`, `metadata` (copied from checkout metadata), `renewal_price` and `initial_price` (money objects), `license_key`, `manage_url`.

## Lifecycle calls

| Goal | Call |
|---|---|
| Cancel at period end | `memberships.cancel({ id, cancel_at_period_end: true, reason? })` |
| Cancel now | `memberships.cancel({ id })` |
| Undo a pending cancel | `memberships.update({ id, cancel_at_period_end: false })` |
| Pause renewals | `memberships.pause({ id, until? })` (`until` must be in the future; Whop-billed memberships only) |
| Resume | `memberships.resume({ id })` |
| Add free days | `memberships.extend({ id, days })`, 1 to 1095 |
| Move the billing day | `memberships.update({ id, current_period_end })`; 30/60/…/360/365-day memberships keep renewing on that day of the month |
| Store your own data | `memberships.update({ id, metadata })`; merges, `{}` clears |

Events: `membership.activated` when it becomes valid (purchase or renewal); `membership.updated` for every other change, including losing access, with `previous_attributes` holding the old values. Pause, resume and extend fire no status event.

## Members

`members.list({ account_id, membership_status?, product_ids?, variant_ids?, access_level?, query? })` lists customers; `members.retrieve({ id })` reads one. A member carries `email`, `access_level`, `status`, `usd_total_spent` and `user`. Use it for CRM views and support tools; use memberships for access.

## License keys

For software customers download, each purchase carries a license key once the product includes Whop's Software app. Validate keys from **your server**, never from the shipped software, because the API key can change every membership.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const VALID_STATUSES = ["active", "trialing", "completed"];

export async function validateLicense(licenseKey: string, hwid: string) {
  const membership = await whop.memberships.retrieve({ id: licenseKey });
  if (!VALID_STATUSES.includes(membership.status)) return { valid: false, reason: "membership_inactive" };

  const boundHwid = membership.metadata?.hwid;
  if (!boundHwid) {
    await whop.memberships.update({ id: membership.id, metadata: { hwid } });
    return { valid: true };
  }
  return boundHwid === hwid ? { valid: true } : { valid: false, reason: "bound_to_another_machine" };
}
```

`retrieve` accepts the license key in place of the membership ID; an unknown key is a 404. Add `past_due` to the valid list if customers keep access while Whop retries. Reset a key with `metadata: {}`.

## Sources

- https://docs.whop.com/developer/guides/memberships.md
- https://docs.whop.com/api-reference/beta/memberships/membership.md
- https://docs.whop.com/api-reference/beta/members/member.md
- https://docs.whop.com/supported-business-models/saas.md
- https://docs.whop.com/developer/guides/invoices.md
- https://docs.whop.com/developer/guides/authentication.md
