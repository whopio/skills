---
max_turns: 16
timeout_seconds: 400
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-api, whop-checkout, mcp]
---

My Whop store has a "Pro Membership" product with a monthly plan. Write `lib/checkout.ts`: a server-side function `createProCheckout()` that creates a Whop checkout for that monthly plan and returns the URL to send the buyer to. Use the Whop tools you have to look up the real IDs; don't leave placeholders.
