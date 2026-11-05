---
type: regex
target: { source: file, path: src/server.ts }
pattern: 'stripe|plans\.create|new Whop\(|company_id'
flags: i
match: not_contains
---
