---
type: regex
target: { source: file, path: src/create-plan.ts }
# Code only: a trailing // comment such as "was 999 cents" is fine.
pattern: '^[^/\n]*(plans\.create|plan_type|company_id|new Whop\(|apiKey\s*:|\b999\b)'
flags: m
match: not_contains
---
