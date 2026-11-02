---
type: regex
target: { source: file, path: scripts/create-checkout.ts }
pattern: 'plan_type|plans\.create|2900'
match: not_contains
---
