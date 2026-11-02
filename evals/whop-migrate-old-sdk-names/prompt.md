---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-migrate]
---

This file was written against an older version of the Whop SDK and no longer type-checks after we upgraded `@whop/sdk`. Update it to the current API with the same behavior ($9.99 every 30 days), and write the updated version to `src/create-plan.ts`.

```ts
import Whop from "@whop/sdk";

const client = new Whop({
  apiKey: process.env.WHOP_API_KEY,
  appID: process.env.WHOP_APP_ID,
});

export async function createMonthlyPlan(productId: string) {
  return client.plans.create({
    company_id: "biz_xxxxxxxxxxxxx",
    product_id: productId,
    plan_type: "renewal",
    initial_price: 999,
    renewal_price: 999,
    billing_period: 30,
  });
}
```
