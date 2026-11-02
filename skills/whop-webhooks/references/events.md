# Webhook events

Each event's `data` is the full resource object in the shape of the webhook's `api_version_date` pin. Payload schemas are linked from the event table in the webhooks guide; fetch `https://docs.whop.com/developer/guides/webhooks.md` for the current list, since new events are added there first.

## Envelope

```json
{
  "id": "msg_...",
  "type": "payment.succeeded",
  "api_version": "v1",
  "api_version_date": "2026-08-14",
  "timestamp": "2026-08-10T17:03:24.291Z",
  "account_id": "biz_...",
  "data": { "id": "pay_...", "...": "the full payment object" }
}
```

`previous_attributes` appears on `.updated` events that capture changes (`account.updated`, `product.updated`, `plan.updated`, `shipment.updated`, and `membership.updated`): the old values of the `data` fields that changed.

## Documented events

| Resource | Events | `data` type in `@whop/sdk` |
|---|---|---|
| Payments | `payment.created`, `payment.succeeded`, `payment.failed`, `payment.pending`, `payment.authorized`, `payment.canceled`, `payment.requires_action` | `Whop.Payment` |
| Memberships | `membership.activated`, `membership.updated`, `membership.trial_ending_soon` | `Whop.Membership` |
| Members | `member.created`, `member.updated` | `Whop.Member` |
| Refunds | `refund.created`, `refund.updated` | `Whop.Refund` |
| Disputes | `dispute.created`, `dispute.updated` | `Whop.Dispute` |
| Dispute alerts | `dispute_alert.created` | `Whop.DisputeAlert` |
| Invoices (legacy invoice API only) | `invoice.created`, `invoice.paid`, `invoice.past_due`, `invoice.voided`, `invoice.marked_uncollectible` | `Whop.Invoice`. Native invoices send `payment.created` when issued and `payment.succeeded` when paid instead |
| Setup intents | `setup_intent.succeeded`, `setup_intent.requires_action`, `setup_intent.canceled` | `Whop.SetupIntent` |
| Products | `product.created`, `product.updated`, `product.deleted`, `product.published`, `product.unpublished` | `Whop.Product` |
| Variants | `plan.created`, `plan.updated`, `plan.deleted` | `Whop.Variant` (event names keep the `plan.` prefix) |
| Payouts | `payout.created`, `payout.updated`, `payout.reversed` | |
| Payout methods and accounts | `payout_method.created`, `payout_account.status_updated` | `Whop.PayoutMethod`, `Whop.PayoutAccount` |
| Transfers | `transfer.created`, `transfer.completed`, `transfer.failed` | |
| Deposits and swaps | `deposit.succeeded`, `swap.completed` | |
| Balances | `ledger_account.funds_available`, `financial_activity.funds_available` | |
| Accounts | `account.updated`, `account.financing_approved`, `account.financing_denied`, `account.financing_disabled` | |
| Verification | `verification.succeeded`, `identity_profile.updated` | |
| Cards | `card.created`, `card.updated`, `card.frozen`, `card.canceled`, `card_application.*`, `card_transaction.*` | |
| App installations | `app_installation.created`, `app_installation.deleted` | |
| Chat | `chat.message.created`, `chat.reaction.created` | |
| Courses | `course_lesson_interaction.completed` | |
| Waitlist entries | `entry.created`, `entry.approved`, `entry.denied`, `entry.deleted` | |
| Shipments | `shipment.created`, `shipment.updated` | |
| Resolution center | `resolution_center_case.created`, `resolution_center_case.updated`, `resolution_center_case.decided` | |
| Exports | `export.completed`, `export.failed` | |
| Domains | `domain.created`, `domain.updated`, `domain.deleted` | |
| Ads | `ad_campaign.updated`, `ad_campaign.payment_failed`, `ad_group.updated`, `ad.updated` | |

Blank type cells: check the payload schema linked from the guide rather than guessing a type name.

## Still delivered, no longer documented

`membership.deactivated` and `membership.cancel_at_period_end_changed` are superseded by `membership.updated`. Existing subscriptions keep working; new code should handle `membership.updated` and read `previous_attributes`. The `withdrawal.*` names were renamed to `payout.*` and can no longer be selected for new subscriptions.

## Sources

- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/developer/guides/memberships.md
- https://docs.whop.com/developer/guides/invoices.md
- https://docs.whop.com/api-reference/webhooks/webhook.md
