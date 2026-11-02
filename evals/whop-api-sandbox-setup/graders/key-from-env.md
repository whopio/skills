---
type: regex
target: { source: file, path: src/whop.ts }
pattern: '^(?=[\s\S]*process\.env(\.\w*KEY\w*|\[))(?=[\s\S]*\btoken\s*:)(?![\s\S]*token\s*:\s*["''`])'
---
