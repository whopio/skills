---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-payouts]
---

My marketplace runs on Whop and every seller has their own connected account. Sellers keep emailing me to change their bank details or withdraw early. I want them to manage their own payouts (see their balance, add a bank account, withdraw) from a "Payouts" page inside my app instead of contacting me. My backend is Node with the Whop API key in `WHOP_API_KEY`. Write the server-side part to `server/payouts.ts`: whatever my page needs from Whop for the seller whose connected account ID is passed in. Then tell me briefly what the page does with it.
