---
type: llm
focus: { source: file, path: AUDIT.md }
---

PASS if `AUDIT.md` identifies all of these problems:
- The signature is checked against a re-serialized body (`request.json()` then `JSON.stringify`) instead of the raw body (`await request.text()`).
- The secret is base64-encoded with `btoa`; it must be passed unchanged.
- The event name `payment_succeeded` is wrong; Whop sends the dotted `payment.succeeded` in `type`.
- There is no deduplication on the event `id` / `webhook-id`, so retries fulfill twice.
- Fulfillment is awaited inline, which risks the 5-second response deadline.

FAIL if any of the five is missing, or if it recommends something the Whop docs contradict (for example base64-encoding the secret, or parsing JSON before verifying).
