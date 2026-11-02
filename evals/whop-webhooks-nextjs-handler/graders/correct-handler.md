---
type: llm
focus: { source: file, path: app/api/webhooks/whop/route.ts }
---

PASS if all of these hold in the file:
- It checks the event's `type` for exactly `"payment.succeeded"` (dotted name) before fulfilling.
- It guards against handling the same delivery twice (deduplicates on the event `id` / `webhook-id`, or clearly marks where that check goes).
- It returns a 2xx response without awaiting the fulfillment work inline, or explicitly defers it (for example `waitUntil`, a queue, or a background task).

FAIL if any of these is missing, if it uses an event name like `payment_succeeded` or `payment.paid`, or if it reads the JSON body before verifying the signature.
