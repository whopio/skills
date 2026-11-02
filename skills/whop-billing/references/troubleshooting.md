# Billing troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Customer lost access right after cancelling | `memberships.cancel` without `cancel_at_period_end`, which defaults to immediate | Always pass `cancel_at_period_end: true` for period-end cancels |
| Pending cancellation needs undoing | Customer changed their mind | `memberships.update({ id, cancel_at_period_end: false })` |
| `has_access` false for a paying user | Wrong `resource_id`, mixed sandbox and production IDs, or the user ID was never linked | Use the `prod_` you sell; link `user_id` from `membership.activated` via checkout `metadata` |
| Access check passes in the browser but data leaks | Gate runs client-side | Call `users.checkAccess` in the server route and return `403` |
| Your access table drifts from Whop | Mirroring status from events that arrive out of order | Call `checkAccess`, or re-read the membership on `membership.updated` |
| No event after pause, resume or extend | Status didn't change | Retrieve the membership to confirm |
| `pause` with `until` refused | `until` not in the future, or membership not billed by Whop | Pass a future ISO 8601 time; omit `until` otherwise |
| License key always invalid | Product lacks Whop's Software app, so `license_key` is empty, or status not in your allowed list | Add the app; allow `active`, `trialing`, `completed` (and `past_due` if you choose) |
| Refund refused: "This payment has been disputed" | The payment has a dispute | Respond to or accept the dispute |
| No `refund.created` after a lost dispute | Lost disputes create no refund record | Track the dispute's status instead |
| Evidence update refused | Already submitted, or `evidence_editable` is `false` | Check `evidence_editable` before updating |
| `disputes.accept` refused | `acceptable` is `false` (inquiry, past deadline, or processor doesn't support it) | Submit evidence instead |
| Invoice issue refused for tax | Tax applies and there's no billing address | Add `billing_address` or `mailing_address_id` |
| Invoice behaves like the legacy API, or items rejected | Older `Api-Version-Date`, or old item field names | Use the current SDK; items take `variant_id` / `variant` |
| `429 invoice_send_limit_reached` | Fourth email in 24 hours | Wait, or deliver the checkout link yourself |
| Invoice saved-method charge never completes | Bank asked for 3D Secure on an off-session charge | Customer pays through `checkout_link` |
| No `invoice.paid` event for a native invoice | Native invoices only send `payment.*` events | Fulfill on `payment.succeeded` for the invoice's `pay_` ID |
| Rule change didn't take effect on the old ID | `replace` creates a new rule ID | Store the successor's ID |
| `review` rule never holds a payment | Wallet, bank, balance or off-session payment | Only on-session cards can be held |
| `400 idempotency_key_mismatch` / `409 idempotency_request_in_progress` | Key reused with a different body / first request still running | One key per distinct request; wait and retry with the same key |

## Sources

- https://docs.whop.com/developer/guides/memberships.md
- https://docs.whop.com/supported-business-models/saas.md
- https://docs.whop.com/developer/guides/authentication.md
- https://docs.whop.com/developer/guides/refunds-and-disputes.md
- https://docs.whop.com/api-reference/beta/disputes/dispute.md
- https://docs.whop.com/developer/guides/invoices.md
- https://docs.whop.com/developer/guides/manage-fraud.md
- https://docs.whop.com/developer/api/idempotency.md
