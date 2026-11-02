---
type: regex
target: mock_calls
pattern: '"input":\{[^}]*"mcp_confirmation_token"[^\n]*"verdict":"ok"'
match: not_contains
---
