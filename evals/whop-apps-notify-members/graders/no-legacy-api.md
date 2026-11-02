---
type: regex
target: { source: file, path: lib/notify.ts }
pattern: 'sendPushNotification|@whop/api'
match: not_contains
---
