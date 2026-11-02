---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-apps]
---

My Whop app lets creators publish posts inside their experience. When a new post is published, every member of that experience should get a push notification that opens the post at `/posts/<postId>` inside my app view. Export `notifyNewPost({ experienceId, postId, title })` from `lib/notify.ts` using the official Node SDK. My API key is in `WHOP_API_KEY`. Write it to `lib/notify.ts`.
