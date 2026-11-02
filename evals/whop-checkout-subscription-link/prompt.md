---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-checkout]
---

I sell a newsletter on Whop. From my Node backend, create a $29/month subscription price for my product `prod_xxxxxxxxxxxxx` (account `biz_xxxxxxxxxxxxx`) and a checkout link customers can use to subscribe. My API key is in `WHOP_API_KEY`. Write it to `scripts/create-checkout.ts` and log the link.
