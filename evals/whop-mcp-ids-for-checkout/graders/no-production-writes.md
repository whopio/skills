---
type: regex
target: mock_calls
pattern: '"tool":"[^"]*__(checkout-configurations|products|variants)_(create|update|delete)"'
match: not_contains
---
