---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-apps]
---

My Next.js app is shown to members inside Whop as an experience view at `/experiences/[experienceId]`. Add a GET route that figures out which Whop user is making the request and whether they have access to the experience, and returns `{ userId, accessLevel }` (401 if the user can't be identified, 403 if they have no access). The experience ID arrives as an `experienceId` query parameter. My API key is in `WHOP_API_KEY` and my app ID is in `WHOP_APP_ID`. Keep everything in one file, `app/api/me/route.ts`.
