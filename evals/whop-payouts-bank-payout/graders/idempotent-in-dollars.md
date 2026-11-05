---
type: regex
target: { source: file, path: scripts/withdraw.ts }
# The amount can be inline (amount: 200) or a constant (const AMOUNT = 200); never 20000 cents.
pattern: '^(?=[\s\S]*idempotencyKey)(?=[\s\S]*[:=]\s*200(\.0+)?\b)(?![\s\S]*\b20000\b)'
---
