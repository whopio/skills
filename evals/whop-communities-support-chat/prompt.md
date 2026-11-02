---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-communities]
---

When a customer clicks "Contact support" in my app, my backend should open a private support conversation between them and my Whop business (`biz_xxxxxxxxxxxxx`) and post a greeting into it from my business. Export `openSupportChat(whopUserId: string, greeting: string)` that returns the conversation ID, using the official Node SDK. My API key is in `WHOP_API_KEY`. Write it to `lib/support.ts`.
