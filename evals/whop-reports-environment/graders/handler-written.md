---
type: regex
target: { source: file, path: app/api/webhooks/whop/route.ts }
pattern: 'unwrapWebhook[\s\S]*payment\.succeeded|payment\.succeeded[\s\S]*unwrapWebhook'
---
