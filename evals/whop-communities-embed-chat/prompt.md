---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-communities]
---

My React app (Next.js App Router) has its own login; `getSession()` from `@/lib/session` returns `{ whopUserId }` for the signed-in user. I want them to chat in my Whop community channel `chat_feed_XXXXXXXXXXXXXX`, embedded in my app. My account is `biz_xxxxxxxxxxxxx` and my API key is in `WHOP_API_KEY`. Write the chat component to `components/Chat.tsx` and the server route that authenticates the user for chat to `app/api/chat/token/route.ts`.
