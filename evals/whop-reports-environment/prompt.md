---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-webhooks, behavior]
---

Add a Whop webhook endpoint to my Next.js App Router app at `app/api/webhooks/whop/route.ts`. When someone pays, call `grantAccess(userId)` from `@/lib/access`. The webhook secret is in `WHOP_WEBHOOK_SECRET`.
