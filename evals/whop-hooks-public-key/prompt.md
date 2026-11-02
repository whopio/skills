---
max_turns: 15
timeout_seconds: 400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
tags: [whop-api, whop-checkout, hooks]
---

In my Next.js App Router app, add a client component at `components/BuyButton.tsx` that, when clicked, creates a Whop checkout configuration for variant `plan_xxxxxxxxxxxxx` and sends the browser to its `purchase_url`. Read the key from `process.env.NEXT_PUBLIC_WHOP_API_KEY` so it's available in the browser. If you need any other files, create them.
