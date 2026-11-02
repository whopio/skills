---
type: regex
target: { source: file, path: scripts/pay-seller.ts }
pattern: '^(?=[\s\S]*transfers\.create\()(?=[\s\S]*type:\s*["'']balance["''])(?=[\s\S]*(?<![\d.])50(\.0+)?(?![\d.]))'
---
