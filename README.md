# Whop Skills

Agent skills that teach AI coding agents to build on [Whop](https://whop.com) correctly: taking payments, verifying webhooks, managing memberships, paying people out, running a marketplace, building Whop apps, embedding chat, and migrating from Stripe.

Each skill follows the [Agent Skills specification](https://agentskills.io/specification), so it works in Claude Code, Cursor, OpenCode, Codex, and any other agent that reads `SKILL.md` files. The plugin also connects the official [Whop MCP server](https://docs.whop.com/developer/guides/ai_and_mcp.md).

## Skills

| Skill | Use it to |
|---|---|
| [`whop`](skills/whop) | Start here: it inspects your project and picks the skill for your goal, even when you don't say "Whop" |
| [`whop-api`](skills/whop-api) | Set up credentials and the SDK, use sandbox, and handle IDs, money units, pagination, errors and versioning |
| [`whop-checkout`](skills/whop-checkout) | Take a payment: checkout links, the Checkout element, Express Checkout, products and variants |
| [`whop-billing`](skills/whop-billing) | Manage what happens after the sale: memberships, access checks, cancellations, invoices, refunds, disputes |
| [`whop-webhooks`](skills/whop-webhooks) | Receive and verify webhook events and fulfill orders exactly once |
| [`whop-payouts`](skills/whop-payouts) | Move money out: transfers, payouts, the payout portal, ledgers |
| [`whop-platforms`](skills/whop-platforms) | Run a marketplace with subaccounts, onboarding and verification |
| [`whop-apps`](skills/whop-apps) | Build apps that run inside Whop: app views, user auth, permissions, OAuth |
| [`whop-communities`](skills/whop-communities) | Embed chat and DMs, sync users, and work with channels, forums and courses |
| [`whop-migrate`](skills/whop-migrate) | Move to Whop from Stripe and others, or from older Whop API names |

You don't call skills by name. Describe what you want ("add a Whop webhook that fulfills the order when a payment succeeds") and the agent loads the matching skill. Each skill works when installed alone; it falls back to the Whop docs where it would hand off to a skill you don't have.

If a skill gives wrong or outdated guidance, tell your agent. It drafts a [skill-feedback issue](https://github.com/whopio/skills/issues/new?template=skill-feedback.md) with keys, IDs and customer data removed, and posts it only after you approve the text.

## Commands, agents and checks

The plugin adds these on top of the skills.

| Command | Does |
|---|---|
| `/whop-developer:connect` | Checks the Whop MCP sign-in (user, businesses, live account) and how it differs from the project's own API key and environment |
| `/whop-developer:setup` | Installs the SDK, adds the env var names, writes a server-only client and proves it works with a real sandbox call |
| `/whop-developer:test-webhook` | Sends signed test events to your running webhook handler: valid signature, tampered signature, duplicate delivery and the 5-second deadline |
| `/whop-developer:audit` | Reviews the integration for leaked keys, unverified webhooks, missing idempotency keys, cents-vs-dollars bugs, client-side access checks and stale API names |

| Subagent | Does |
|---|---|
| `whop-integration-reviewer` | Read-only review with `file:line` findings by severity (used by `/whop-developer:audit`) |
| `whop-migrator` | Rewrites old Whop code (`@whop/api`, API v2, plans, companies, withdrawals, cents) or a Stripe integration to the current API, and type-checks the result |

Claude Code also runs three hooks:

- **Before a prepared Whop operation executes** (a Whop MCP call carrying `mcp_confirmation_token`: a refund, a cancellation, a deletion, a new webhook), it makes Claude Code ask you, even if you always allow the Whop tools. The model can't treat your original request as the approval. Previews and reads aren't affected.

- **After every file edit**, it checks the lines just written for names the current API replaced (`plans.create`, `new Whop(`, `company_id`, `membership.went_valid`...) and for unsafe code: a Whop key under `NEXT_PUBLIC_` or in a `"use client"` file, a hard-coded `ws_` secret, a parsed webhook body. It tells the agent the fix and the skill to load. Each finding is reported once per session.
- **At session start**, in a project that already uses Whop, it tells the agent which Whop packages are installed, flags deprecated ones, and explains that the MCP server works on the live account and confirms consequential actions in two steps. Other projects get nothing.

All three need Node 18+ and do nothing if it's missing. They read local files only and never send data anywhere. The webhook test script ships inside the `whop-webhooks` skill, so agents that install only the skills get it too.

## Install

**Claude Code**

```text
/plugin marketplace add whopio/skills
/plugin install whop-developer@whop-skills
```

**GitHub Copilot CLI**

```bash
copilot plugin marketplace add whopio/skills
copilot plugin install whop-developer@whop-skills
```

**Codex**

```bash
codex plugin marketplace add whopio/skills
codex plugin add whop-developer@whop-skills
```

Start a new Codex session after installing.

**VS Code (GitHub Copilot)**: turn on the `chat.plugins.enabled` setting, run **Chat: Install Plugin from Source** from the Command Palette, and enter `https://github.com/whopio/skills`.

**Antigravity**

```bash
agy plugin install https://github.com/whopio/skills
```

**Gemini CLI**

```bash
gemini extensions install https://github.com/whopio/skills
```

**Kimi Code**: run `/plugins install https://github.com/whopio/skills`, then `/reload`. Sign in to the Whop MCP server with `/mcp-config login` when Kimi asks.

**Cursor, and other plugin-aware tools** (skills plus the MCP server):

```bash
npx plugins add whopio/skills
```

### What each tool gets

| Tool | Skills | MCP server | Commands | Subagents | Hooks | Rules | Manifest |
|---|---|---|---|---|---|---|---|
| Claude Code | ✓ | ✓ | ✓ | ✓ | ✓ | | `.claude-plugin/plugin.json` |
| Cursor | ✓ | ✓ | ✓ | ✓ | | ✓ | `.cursor-plugin/plugin.json` |
| Kimi Code | ✓ | ✓ | ✓ | ✓ | | | `.kimi-plugin/plugin.json` |
| Gemini CLI | ✓ | ✓ | ✓ | | | | `gemini-extension.json` |
| Antigravity | ✓ | ✓ | | | | ✓ | `.antigravity-plugin/plugin.json` + `mcp_config.json` |
| Codex | ✓ | ✓ | | | | | `.codex-plugin/plugin.json`, listed in `.agents/plugins/marketplace.json` |
| GitHub Copilot (CLI and VS Code) and other [Agent Plugins](https://agent-plugins.org) hosts | ✓ | ✓ | | | | | `plugin.json` + `mcp.json` |
| Grok Build | ✓ | ✓ | | | | | `.grok-plugin/plugin.json` |

Where a tool has no subagents, `/whop-developer:audit` follows the reviewer's checklist itself. Cursor and Antigravity don't run the plugin's hooks, so they get the same checks as a rule ([`rules/whop.mdc`](rules/whop.mdc), [`rules/whop.md`](rules/whop.md)) that the agent applies when it works on Whop code.

**Skills only, into any agent** (OpenCode, Claude Code, Cursor, Codex, and [more](https://github.com/vercel-labs/skills)):

```bash
npx skills add whopio/skills
```

Add `-a <agent>` to pick the agent, or `--skill whop-checkout` to install one skill.

**Copy the skills by hand.** Each skill is a folder with a `SKILL.md`. Codex, Cursor, OpenCode and Gemini CLI all read `~/.agents/skills/`:

```bash
git clone --depth 1 https://github.com/whopio/skills.git /tmp/whop-skills
mkdir -p ~/.agents/skills && cp -R /tmp/whop-skills/skills/* ~/.agents/skills/
```

Or copy them into the folder your agent reads:

| Agent | All projects | One project | Docs |
|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | [Skills](https://code.claude.com/docs/en/skills) |
| Codex | `~/.agents/skills/` | `.agents/skills/` | [Skills](https://developers.openai.com/codex/skills) |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` | [Skills](https://cursor.com/docs/skills) |
| OpenCode | `~/.config/opencode/skills/` or `~/.agents/skills/` | `.opencode/skills/` | [Skills](https://opencode.ai/docs/skills/) |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` | [Skills](https://geminicli.com/docs/cli/skills/) |

A hand copy doesn't include the MCP server, commands, subagents or hooks; add the MCP server as below.

### Whop MCP server

One connection covers the API (acting on your live account) and the Whop docs (`docs_search`, `docs_query`), so there's no separate docs server. The plugin installs it for you. To add it by hand:

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
