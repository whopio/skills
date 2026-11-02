---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-webhooks]
---

I sell a course through Whop checkout. Add a Next.js App Router route that receives Whop's webhook when a payment succeeds and fulfills the order (just call a `fulfillOrder(paymentId)` function I already have in `lib/fulfill.ts`). My signing secret is in `WHOP_WEBHOOK_SECRET`. Write it to `app/api/webhooks/whop/route.ts`.
