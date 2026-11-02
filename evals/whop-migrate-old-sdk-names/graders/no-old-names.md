---
type: regex
target: { source: file, path: src/create-plan.ts }
pattern: 'plans\.create|plan_type|company_id|new Whop\(|apiKey\s*:|\b999\b'
match: not_contains
---
