---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-checkout]
---

My React app sells a course through Whop (variant `plan_xxxxxxxxxxxxx`). Instead of sending buyers to a Whop link, I want the Whop checkout embedded right on my pricing page, and buyers should come back to `https://example.com/thanks` after any bank verification step. Write the component to `src/components/WhopCheckout.tsx`.
