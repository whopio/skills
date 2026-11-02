---
description: Review this project's Whop integration for security and correctness - leaked keys, webhook verification, idempotency, money units, access checks and stale API names
argument-hint: "[path or area to focus on]"
---

# Audit the Whop integration

Focus from the user: `$ARGUMENTS` (empty means the whole repository).

1. Run the `whop-integration-reviewer` subagent from this plugin on that scope. It reads code and reports; it doesn't edit anything.
2. Present its findings grouped by severity (`critical`, `high`, `medium`, `low`), each with `file:line`, the problem, the fix and the skill that covers it. If it found nothing, say what it checked.
3. Ask which findings to fix. Fix the ones the user picks, loading the skill each finding names. For stale API names across many files, offer the `whop-migrator` subagent instead.
4. After the fixes, re-run the checks that failed (type-check, tests, or `/whop-developer:test-webhook` for webhook findings) and report the result.
