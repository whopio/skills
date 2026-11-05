---
type: regex
target: { source: file, path: scripts/create-checkout.ts }
pattern: '^(?=[\s\S]*(variants|checkoutConfigurations)\.create)(?=[\s\S]*renewal_price["'']?\s*:\s*29(\.0+)?\b)(?![\s\S]*2900)'
---
