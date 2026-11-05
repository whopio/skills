---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-payouts]
---

Write a Node script at `scripts/withdraw.ts` that pays out $200 USD from my Whop account's balance (`biz_xxxxxxxxxxxxx`) to the account's default bank payout method at standard speed. It runs from a cron job that sometimes retries, so a retry must never pay out twice. My API key is in `WHOP_API_KEY`.
