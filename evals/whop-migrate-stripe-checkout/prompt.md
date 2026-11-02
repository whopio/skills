---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [whop-migrate]
---

Our SaaS takes payments with Stripe today: we create Stripe Checkout Sessions for a monthly subscription, and a webhook on `checkout.session.completed` and `customer.subscription.deleted` turns accounts on and off. We have a few hundred active subscribers. We want to move to Whop. What's the migration plan, and what replaces each of those pieces?
