---
max_turns: 20
timeout_seconds: 500
allowed_tools: [Read, Glob, Grep, Skill, Write, Agent]
tags: [whop-webhooks, agents]
---

Review this Whop webhook handler for problems before we ship it. Don't change the code. Write your findings, most serious first, to `AUDIT.md`.

```ts
// app/api/webhooks/whop/route.ts
import { unwrapWebhook } from "@whop/sdk/helpers";
import { fulfillOrder } from "@/lib/fulfill";

export async function POST(request: Request) {
  const body = await request.json();
  const event = unwrapWebhook(JSON.stringify(body), {
    headers: Object.fromEntries(request.headers),
    key: btoa(process.env.WHOP_WEBHOOK_SECRET!),
  });

  if (event.type === "payment_succeeded") {
    await fulfillOrder(event.data.id);
  }
  return new Response("OK");
}
```
