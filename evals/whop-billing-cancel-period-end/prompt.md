---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-billing]
---

Customers on my site pay a monthly subscription through Whop. Add a server function `cancelSubscription(membershipId: string)` that cancels a customer's subscription when they click "Cancel", but lets them keep access until the end of the period they already paid for. My API key is in `WHOP_API_KEY`. Write it to `lib/cancel-subscription.ts`.
