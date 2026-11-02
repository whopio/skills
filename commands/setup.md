---
description: Set up Whop in this project - install the SDK, add env vars, create a server-only client, and prove it works against sandbox
argument-hint: "[typescript|python|ruby]"
---

# Set up Whop

Get this project to a working, server-side Whop client on **sandbox**, verified by a real API call. Language hint from the user: `$ARGUMENTS` (detect it if empty).

Load the `whop-api` skill first and follow it. If anything below disagrees with the skill or the live docs it points to, the skill and docs win.

## 1. Look before asking

- Language, framework and package manager (lockfile: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lock`; `requirements.txt` / `pyproject.toml`; `Gemfile`).
- Existing Whop code: `@whop/sdk` and its version, `@whop/api`, `whop-sdk`, `whop_sdk`, and `WHOP_*` variable *names* in `.env*` files. Never print variable values.
- If you find `@whop/api`, `@whop/sdk` below 2.0, or old names (`plans.`, `companies.`, `withdrawals.`), say so and suggest `/whop-developer:audit` or the `whop-migrate` skill instead of layering new code on top.

Then ask only what you could not find out:

- **What are they building?** Whop inside their own product means an API key, so continue here. An app that runs inside Whop starts with the Whop CLI, not an API key: stop and switch to the `whop-apps` skill.

## 2. Install the SDK

Use the project's own package manager: `pnpm add @whop/sdk` (or the npm, yarn or bun equivalent), `pip install whop-sdk`, or `gem install whop_sdk` / add it to the `Gemfile`.

## 3. Environment variables

- Add the names to `.env.example` (create it if missing) with empty values: `WHOP_API_KEY=` and `WHOP_ENVIRONMENT=sandbox`. Add `WHOP_WEBHOOK_SECRET=` only if they will receive webhooks.
- Make sure the real env file (`.env.local`, `.env`) is gitignored before anything goes in it.
- **The user pastes the key into that file themselves.** Don't ask them to paste a key into the chat, and never write a key into a tracked file. Send them to `https://sandbox.whop.com/dashboard/developer` → **Account API Keys** for a sandbox key.
- Never prefix these with `NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_` or similar. Whop keys stay on the server.

## 4. Create the client

Write one server-only module (for example `lib/whop.ts`, or the framework's server folder) with the setup snippet from `whop-api`: `new WhopClient({ token: process.env.WHOP_API_KEY, environment })`, choosing `WhopEnvironment.Sandbox` when `WHOP_ENVIRONMENT=sandbox`. Python and Ruby use the matching snippets in the skill. Don't import it from client components.

## 5. Prove it works

Once the user says the key is in place, make one real sandbox call. For TypeScript or JavaScript on Node 20.6+:

```bash
node --env-file=.env.local --input-type=module -e '
import { WhopClient, WhopEnvironment } from "@whop/sdk";
const whop = new WhopClient({ token: process.env.WHOP_API_KEY, environment: WhopEnvironment.Sandbox });
console.log((await whop.accounts.me()).id);'
```

Use the env file the project actually has. It should print a `biz_` ID. On `401`, the key is missing or belongs to production (keys look identical, so check which dashboard it came from). For other errors, use the Errors table in `whop-api`. Run the equivalent one-liner for Python or Ruby.

## 6. The Whop MCP server (optional)

If the `whop` MCP tools are connected, call `connection_status` and tell the user which Whop user and account that connection uses. Explain that the MCP server works on their **live production** account, separately from the sandbox key you just set up. During setup, use it only for reads. Creating products, webhooks or payments through it creates real production objects, so do that only when the user asks, and only after they approve the prepared preview.

## 7. Wrap up

Report what changed (files, packages, variable names) and the verified `biz_` ID. Then point to the next step for what they're building: `whop-checkout` to take a payment, `whop-webhooks` to receive events (then `/whop-developer:test-webhook`), `whop-billing` for access checks, `whop-payouts` or `whop-platforms` for money out and marketplaces.
