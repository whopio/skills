---
type: regex
target: { source: file, path: app/api/webhooks/whop/route.ts }
pattern: 'btoa\(|base64'
match: not_contains
---
