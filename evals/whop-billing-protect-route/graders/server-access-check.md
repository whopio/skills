---
type: regex
target: { source: file, path: app/api/premium/route.ts }
pattern: '^(?=[\s\S]*users\.checkAccess\()(?=[\s\S]*resource_id)(?=[\s\S]*has_access)(?=[\s\S]*403)'
---
