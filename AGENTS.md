# AGENTS.md — Whop Skills

Instructions for any agent or person changing this repo. `CLAUDE.md` imports this file (`@AGENTS.md`), so every agent reads the same rules. Keep it a regular file: `npx plugins` rewrites symlinks to absolute paths, which breaks reinstalls.

## What this is

Agent skills for **developers building on Whop**: taking payments, verifying webhooks, managing memberships, paying people out, running a marketplace with connected accounts, building Whop apps, embedding chat, and migrating to Whop. Each skill is a folder under `skills/` that follows the [Agent Skills specification](https://agentskills.io/specification.md).

Operating a live Whop business by hand ("refund this customer", "launch my store", "run ads") is **not** this repo's job. That lives in [`whopio/plugins`](https://github.com/whopio/plugins) and the `whop` CLI's own skill (`whop skills add`). Skills here hand off to those instead of duplicating them.

```
whop-api          foundation: credentials, SDK setup, sandbox, concepts and IDs, money units, versioning, idempotency, pagination, errors
whop-checkout     take a payment: checkout links, Checkout element, Express Checkout, card fields, wallets, saved methods, products and variants, iOS, React Native
whop-billing      after the sale: memberships, access checks, cancellations, invoices, refunds, disputes, fraud
whop-webhooks     receive and verify events, fulfill idempotently, retries, local testing
whop-payouts      money out: payouts, payout portal, adding funds, transfers, ledgers, stats, Wallet element
whop-platforms    marketplaces: connected accounts, onboarding, collecting for connected accounts, verification and RFIs, Dashboard element
whop-apps         apps that run inside Whop: CLI, app views, user auth, permissions, installs, scheduled runs, notifications, OAuth, uploads
whop-communities  chat and community: Chat and DMs elements, chat auth and user sync, channels, support chats, forums, courses
whop-migrate      move to Whop from Stripe and others, or from older Whop API names
```

Every other skill assumes `whop-api`'s setup. A skill that needs an API client says "set up the client with `whop-api`" rather than repeating it.

## Source of truth

Whop changes its API often. A skill that copies facts goes stale; that is what happened to the previous payments skill (prices in cents instead of dollars, `btoa()` on webhook secrets, removed endpoints).

1. **Every fact comes from the current docs or the published SDK.** The docs source lives in the Whop monorepo at `public-docs/` and is served at `https://docs.whop.com/<path>.md` (the `.mdx` path with `.md` appended). The API contract is `https://api.whop.com/api/v1/openapi.json`. The TypeScript SDK is `@whop/sdk` on npm (version pinned in `package.json`).
2. **Teach decisions, link details.** A skill tells the agent which path to take and what will go wrong. Full parameter tables stay in the docs: link the `.md` page and tell the agent to fetch it. Fetching `https://docs.whop.com/<path>.md` works in every agent with web access, so skills never depend on an MCP server for docs.
3. **Every reference file ends with a `## Sources` list** of the docs pages it was written from. `scripts/check-links.py` fetches each one.
4. **Never invent.** If the docs don't say it, the skill doesn't say it. If you believe something but can't find it, leave it out.

## Writing a skill

### Frontmatter

```yaml
---
name: whop-<name>            # must equal the folder name
description: >-
  <What it does, in one or two sentences.>
  Use when: "<trigger phrase>", "<trigger phrase>", ...
  Chain with: <skill> for <reason>.
  NOT for: <case> (use <skill>), <case> (use <skill>).
license: Apache-2.0
metadata:
  author: whop
  version: "0.1.0"           # must equal VERSION
---
```

Only spec fields are allowed at the top level (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). The description is at most 1024 characters and must contain `Use when` and `NOT for`. Agents pick skills from the description alone, so put the words users actually type in the triggers.

### Body

Aim for under 300 lines; 500 is the hard limit. The test for what stays in `SKILL.md`: if removing a section would stop the agent from deciding what to do next, it stays. Everything else moves to `references/`.

Sections, in this order:

1. `# Title` and one sentence on what the skill does.
2. `## Before you start` — what must be true first (client set up via `whop-api`, sandbox keys, which credential type).
3. `## Rules` — the numbered gotchas that cause real bugs. These are the most valuable lines in the skill.
4. `## Pick a path` — a decision table or tree from the user's goal to a workflow.
5. One `##` section per workflow: numbered steps with a minimal, correct snippet.
6. `## Verify` — how to prove it works in sandbox before going live.
7. `## Errors` — symptom → cause → fix.
8. `## References` — every file in `references/` with one line on when to read it.

### Code

- TypeScript first, using `@whop/sdk`: `import { WhopClient } from "@whop/sdk"` and `new WhopClient({ token: process.env.WHOP_API_KEY })`. Python (`whop-sdk`) where the docs show it.
- **TypeScript snippets that import only `@whop/sdk` / `@whop/sdk/helpers` (and Node built-ins) must compile on their own.** `npm run check:snippets` type-checks them against the pinned SDK with `strict`. Use literal placeholder IDs (`"biz_xxxxxxxxxxxxx"`) instead of undefined variables. Snippets that import a framework (Next.js, React) are skipped by the checker, so keep their Whop calls identical to a checked snippet.
- Money is in **major currency units** (dollars, `10.00` = $10.00) for prices, fees, transfers and payouts. Say so wherever an amount appears.
- Use current names: `variants` (not plans), `accounts` and `account_id` (not companies / `company_id`), `payouts` (not withdrawals), `deposits` (not top-ups), `unwrapWebhook` from `@whop/sdk/helpers`, `event.type`.
- Never put an API key in client-side code.

### Banned patterns

`scripts/validate.py` fails on these outside `skills/whop-migrate/references/legacy-map.md` (where they appear as the "old" column) and outside `skills/whop-communities/` for the chat embed packages, which chat still uses:

`btoa(`, `webhookKey`, `hosted_kyc`, `hosted_payouts`, `plans.create`, `companies.create`, `companies.list`, `companies.update`, `parent_company_id`, `withdrawals.create`, `topups.`, `chargeUser`, `mcp.whop.com/sse`, `new Whop(`, `plan_type`, `@whop/embedded-components`, `@whop/checkout`, `WhopCheckoutEmbed`, `membership.went_valid`, `from "@whop/api"`.

When the API renames something, add the old name here and to the list in `scripts/validate.py`.

### Self-contained

Each skill installs on its own (`npx skills add <repo> --skill whop-checkout`). No `../` paths. Every file in `references/` is linked from that skill's `SKILL.md`. If two skills need the same fact, each states it; small duplication beats a broken link.

## Versioning

`VERSION` is the single version. It must match `metadata.version` in every `SKILL.md`, the `version` in every plugin manifest, and the `X-Whop-Plugin: skills/<version>` header in the MCP configs. `scripts/bump-version.py <new>` updates all of them.

| File | Read by |
|---|---|
| `plugin.json` + `mcp.json` | The [Agent Plugins](https://agent-plugins.org) standard: Cursor, Codex (OpenAI metadata under `extensions.com.openai`) |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` + `.mcp.json` | Claude Code, `npx plugins` |
| `.codex-plugin/plugin.json` + `.mcp.json` | Older Codex builds and `npx plugins -t codex`, which otherwise generate a manifest with no branding. Current Codex reads `plugin.json` first. `interface` must equal `plugin.json`'s `extensions.com.openai.interface` |
| `.cursor-plugin/plugin.json` | Cursor Marketplace |
| `.grok-plugin/plugin.json` + `.mcp.json` | Grok Build |
| `gemini-extension.json` | Gemini CLI (MCP inline, as `httpUrl`) |

`.mcp.json` and `mcp.json` must be identical and define one server, `whop`: the official Whop MCP server. It is `https://mcp.whop.com/claude/mcp`, the route without money-out tools, until the hosted server offers a non-admin default on `/mcp`.

## Checks

```bash
python3 scripts/validate.py      # structure, frontmatter, versions, references, banned patterns
npm run check:snippets           # type-check TypeScript snippets against the pinned @whop/sdk
python3 scripts/check-links.py   # every docs.whop.com link in the skills returns 200
```

CI runs all three on every PR. Dependabot bumps `@whop/sdk` weekly, so an SDK change that breaks a snippet fails CI instead of reaching users.

## Evals

Each `evals/<case>/` folder holds a `prompt.md` and `graders/*.md`. Claude Code's eval runner runs each case with and without the plugin and reports the difference:

```bash
claude plugin eval . --runs 3          # all cases
claude plugin eval . --case 'whop-webhooks-*'
```

Run the affected cases after any change to a `SKILL.md`, and compare scores before and after when rewording a description. When a bug is found by hand, add a case for it.
