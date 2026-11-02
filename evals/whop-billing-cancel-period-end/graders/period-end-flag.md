---
type: regex
target: { source: file, path: lib/cancel-subscription.ts }
pattern: 'memberships\.(cancel|update)\(\s*\{[\s\S]*?cancel_at_period_end\s*:\s*true'
---
