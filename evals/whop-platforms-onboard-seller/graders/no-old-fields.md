---
type: regex
target: { source: file, path: scripts/onboard-seller.ts }
pattern: 'company_id|parent_account_id'
match: not_contains
---
