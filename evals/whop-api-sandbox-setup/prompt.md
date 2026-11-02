---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-api]
---

I'm adding Whop to my Node.js backend (TypeScript). While I develop I want every request to go to Whop's sandbox, not production. Set up the Whop SDK client and export it so the rest of the app can import it. My API key is in an environment variable. Write it to `src/whop.ts`.
