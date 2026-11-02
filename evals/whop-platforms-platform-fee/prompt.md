---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-platforms]
---

My marketplace runs on Whop and each seller already has a connected account (I store its `biz_` ID). Sellers list one-time products priced in USD. I want to take 10% of every sale as my platform's cut, and the seller should deal with their own refunds and disputes. Write `server/create-checkout.ts` with a function `createCheckout(sellerAccountId: string, priceUsd: number)` that returns the URL to send the buyer to. My platform API key is in `WHOP_API_KEY`.
