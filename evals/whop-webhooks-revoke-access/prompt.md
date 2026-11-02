---
max_turns: 10
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
tags: [whop-webhooks]
---

I'm wiring Whop webhooks into my SaaS. Which webhook event(s) should I subscribe to so I can remove a customer's access when their Whop subscription ends (cancelled, payment failed, etc.), and how do I tell from the payload that they lost access? Short answer please.
