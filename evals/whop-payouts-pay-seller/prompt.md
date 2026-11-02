---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-payouts]
---

I run a marketplace on Whop. A seller just finished an order and I owe them $50. Write a Node script at `scripts/pay-seller.ts` that sends $50 USD from my platform's Whop balance (`biz_platformxxxxx`) to the seller's connected account (`biz_sellerxxxxxxx`), tagging it with the order ID `order_981`. It will run from a cron job that sometimes retries, so make sure a retry can't pay the seller twice. My API key is in `WHOP_API_KEY`.
