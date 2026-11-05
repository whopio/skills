---
type: regex
target: { source: file, path: scripts/withdraw.ts }
# Order-independent: helpers may be defined before the quote call, or the request built first.
pattern: '^(?=[\s\S]*payouts\.createQuote\()(?=[\s\S]*payouts\.create\()(?=[\s\S]*quote_token)'
---
