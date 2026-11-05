---
max_turns: 16
timeout_seconds: 400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
tags: [whop, routing]
---

I want readers to pay $29 a month for my newsletter, and the `/premium` route in `src/server.ts` should only work for people who are currently paying. The product is `prod_xxxxxxxxxxxxx` in account `biz_xxxxxxxxxxxxx`. Write a script at `scripts/create-checkout.ts` that creates the monthly price and prints a link readers can use to subscribe, then update `src/server.ts` so `/premium` is only for paying readers. Use what this project already has.
