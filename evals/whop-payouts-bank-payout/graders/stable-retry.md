---
type: llm
focus: { source: file, path: scripts/withdraw.ts }
---

PASS if a retried run of the script can't create a second payout: the `Idempotency-Key` (`idempotencyKey`) is stable across retries (derived from something fixed for this payout, or stored before the call and reused), and a retry reuses the same `quote_token` with it or otherwise recovers the existing payout.

FAIL if the idempotency key is new on every run (for example `randomUUID()` with nothing stored), or if there is no idempotency key.
