---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-platforms]
---

I'm building a marketplace on top of Whop. When a new seller signs up on my site (I have their email and my internal seller ID), I need to create their Whop account under my platform and send them straight to identity verification, then bring them back to `https://market.example.com/sellers/welcome`. Write a Node function in `scripts/onboard-seller.ts` that takes `{ email, sellerId }` and returns the URL to redirect them to. It must be safe to call twice for the same seller. My platform API key is in `WHOP_API_KEY`.
