---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-billing]
---

I run a Next.js App Router SaaS and customers subscribe through Whop. Each of my users has their Whop user ID saved; `getSessionUser()` from `lib/auth.ts` returns `{ whopUserId }` or `null`. Protect `GET /api/premium` so only people currently paying for my product `prod_xxxxxxxxxxxxx` get the data, and everyone else is turned away. My API key is in `WHOP_API_KEY`. Write it to `app/api/premium/route.ts`.
