---
type: regex
target: { source: file, path: components/BuyButton.tsx }
pattern: 'NEXT_PUBLIC_WHOP_API_KEY|WHOP_API_KEY|new WhopClient'
match: not_contains
---
