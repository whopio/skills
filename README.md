# Whop Skills

Agent skills that teach AI coding agents to build on [Whop](https://whop.com) correctly: taking payments, verifying webhooks, managing memberships, paying people out, running a marketplace, building Whop apps, embedding chat, and migrating from Stripe.

Each skill follows the [Agent Skills specification](https://agentskills.io/specification), so it works in Claude Code, Cursor, OpenCode, Codex, and any other agent that reads `SKILL.md` files. The plugin also connects the official [Whop MCP server](https://docs.whop.com/developer/guides/ai_and_mcp.md).

## Skills

| Skill | Use it to |
|---|---|
| [`whop-api`](skills/whop-api) | Set up credentials and the SDK, use sandbox, and handle IDs, money units, pagination, errors and versioning |
| [`whop-checkout`](skills/whop-checkout) | Take a payment: checkout links, the Checkout element, Express Checkout, products and variants |
| [`whop-billing`](skills/whop-billing) | Manage what happens after the sale: memberships, access checks, cancellations, invoices, refunds, disputes |
| [`whop-webhooks`](skills/whop-webhooks) | Receive and verify webhook events and fulfill orders exactly once |
| [`whop-payouts`](skills/whop-payouts) | Move money out: transfers, payouts, the payout portal, ledgers |
| [`whop-platforms`](skills/whop-platforms) | Run a marketplace with connected accounts, onboarding and verification |
| [`whop-apps`](skills/whop-apps) | Build apps that run inside Whop: app views, user auth, permissions, OAuth |
| [`whop-communities`](skills/whop-communities) | Embed chat and DMs, sync users, and work with channels, forums and courses |
| [`whop-migrate`](skills/whop-migrate) | Move to Whop from Stripe and others, or from older Whop API names |

You don't call skills by name. Describe what you want ("add a Whop webhook that fulfills the order when a payment succeeds") and the agent loads the matching skill.

## Commands, agents and checks

The plugin adds these on top of the skills.

| Command | Does |
|---|---|
| `/whop-developer:setup` | Installs the SDK, adds the env var names, writes a server-only client and proves it works with a real sandbox call |
| `/whop-developer:test-webhook` | Sends signed test events to your running webhook handler: valid signature, tampered signature, duplicate delivery and the 5-second deadline |
| `/whop-developer:audit` | Reviews the integration for leaked keys, unverified webhooks, missing idempotency keys, cents-vs-dollars bugs, client-side access checks and stale API names |

| Subagent | Does |
|---|---|
| `whop-integration-reviewer` | Read-only review with `file:line` findings by severity (used by `/whop-developer:audit`) |
| `whop-migrator` | Rewrites old Whop code (`@whop/api`, API v2, plans, companies, withdrawals, cents) or a Stripe integration to the current API, and type-checks the result |

Claude Code also runs two hooks:

- **After every file edit**, it checks the lines just written for names the current API replaced (`plans.create`, `new Whop(`, `company_id`, `membership.went_valid`...) and for unsafe code: a Whop key under `NEXT_PUBLIC_` or in a `"use client"` file, a hard-coded `ws_` secret, a parsed webhook body. It tells the agent the fix and the skill to load. Each finding is reported once per session.
- **At session start**, in a project that already uses Whop, it tells the agent which Whop packages are installed, flags deprecated ones, and explains that the MCP server works on the live account and confirms consequential actions in two steps. Other projects get nothing.

Both hooks need Node 18+ and do nothing if it's missing. They read local files only and never send data anywhere. The webhook test script ships inside the `whop-webhooks` skill, so agents that install only the skills get it too.

## Install

**Claude Code**

```text
/plugin marketplace add whopio/skills
/plugin install whop-developer@whop-skills
```

**Cursor, Claude Code, Codex, and other plugin-aware tools** (skills plus the MCP server):

```bash
npx plugins add whopio/skills
```

**Skills only, into any agent** (OpenCode, Claude Code, Cursor, Codex, and [more](https://github.com/vercel-labs/skills)):

```bash
npx skills add whopio/skills
```

Add `-a <agent>` to pick the agent, or `--skill whop-checkout` to install one skill.

### Whop MCP server

The plugin installs it for you. To add it by hand:

- Claude Code: `claude mcp add --transport http whop https://mcp.whop.com/mcp`
- OpenCode: add this to `opencode.json`, then run `opencode mcp auth whop`:

  ```json
  {
    "$schema": "https://opencode.ai/config.json",
    "mcp": {
      "whop": { "type": "remote", "url": "https://mcp.whop.com/mcp" }
    }
  }
  ```

The first call opens a browser window to sign in to Whop. See the [MCP guide](https://docs.whop.com/developer/guides/ai_and_mcp.md) for other clients.

## Operating a Whop business instead?

These skills are for writing code against Whop. To run a live store from your agent (refund a customer, launch a product, check revenue), use [`whopio/plugins`](https://github.com/whopio/plugins) or the `whop` CLI.

## Contributing

Read [`AGENTS.md`](AGENTS.md) for how skills are written and checked, and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the pull request flow.

## Privacy

The plugin connects to `mcp.whop.com` using your Whop login. Whop's [privacy policy](https://whop.com/privacy) and [terms](https://whop.com/tos) apply.

## License

[Apache-2.0](LICENSE)
