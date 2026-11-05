# AGENTS.md — Whop Skills

Instructions for any agent or person changing this repo. `CLAUDE.md` imports this file (`@AGENTS.md`), so every agent reads the same rules. Keep it a regular file: `npx plugins` rewrites symlinks to absolute paths, which breaks reinstalls.

## What this is

Agent skills for **developers building on Whop**: taking payments, verifying webhooks, managing memberships, paying people out, running a marketplace with subaccounts, building Whop apps, embedding chat, and migrating to Whop. Each skill is a folder under `skills/` that follows the [Agent Skills specification](https://agentskills.io/specification.md).

Operating a live Whop business by hand ("refund this customer", "launch my store", "run ads") is **not** this repo's job. That lives in [`whopio/plugins`](https://github.com/whopio/plugins) and the `whop` CLI's own skill (`whop skills add`). Skills here hand off to those instead of duplicating them.

```
whop              router: inspect the project, pick the skill for the goal, docs fallbacks when a skill isn't installed
whop-api          foundation: credentials, SDK setup, sandbox, concepts and IDs, money units, versioning, idempotency, pagination, errors
whop-checkout     take a payment: checkout links, Checkout element, Express Checkout, card fields, wallets, saved methods, products and variants, iOS, React Native
whop-billing      after the sale: memberships, access checks, cancellations, invoices, refunds, disputes, fraud
whop-webhooks     receive and verify events, fulfill idempotently, retries, local testing
whop-payouts      money out: payouts, payout portal, adding funds, transfers, ledgers, stats, Wallet element
whop-platforms    marketplaces: subaccounts, onboarding, collecting for subaccounts, verification and RFIs, Dashboard element
whop-apps         apps that run inside Whop: CLI, app views, user auth, permissions, installs, scheduled runs, notifications, OAuth, uploads
whop-communities  chat and community: Chat and DMs elements, chat auth and user sync, channels, support chats, forums, courses
whop-migrate      move to Whop from Stripe and others, or from older Whop API names
```

Every other skill assumes `whop-api`'s setup. A skill that needs an API client says "set up the client with `whop-api`", followed by a one-line fallback for when that skill isn't installed. `whop` is the entry point: it maps a goal ("sell a subscription", "pay my sellers") to skills and works even when the user never says "Whop".

## Source of truth

Whop changes its API often. A skill that copies facts goes stale; that is what happened to the previous payments skill (prices in cents instead of dollars, `btoa()` on webhook secrets, removed endpoints).

1. **Every fact comes from the current docs or the published SDK.** The docs source lives in the Whop monorepo at `public-docs/` and is served at `https://docs.whop.com/<path>.md` (the `.mdx` path with `.md` appended). The API contract is `https://api.whop.com/api/v1/openapi.json`. The TypeScript SDK is `@whop/sdk` on npm (version pinned in `package.json`). The MCP server's behavior and tool list come from its public source, [`whopio/whop-mcp-server`](https://github.com/whopio/whop-mcp-server), which is what `mcp.whop.com` runs.
2. **Teach decisions, link details.** A skill tells the agent which path to take and what will go wrong. Full parameter tables stay in the docs: link the `.md` page and tell the agent to fetch it. Fetching `https://docs.whop.com/<path>.md` works in every agent with web access, so skills never depend on an MCP server for docs; they mention the MCP `docs_search` tool as the faster path when it's connected.
3. **Every reference file ends with a `## Sources` list** of the docs pages it was written from. `scripts/check-links.py` fetches each one.
4. **Never invent.** If the docs don't say it, the skill doesn't say it. If you believe something but can't find it, leave it out.

## The Whop MCP server in skills

The plugin ships the Whop MCP server, and skills tell the agent when to use it. The split, which every skill follows:

- **MCP is for the agent's own work**: looking up IDs, checking live state, debugging production, and one-off changes the user asks for. It acts on the signed-in user's live account and can't reach sandbox.
- **The SDK is for the app's code**, tested in sandbox with an API key.
- **Consequential tools prepare first.** A skill that names one says the user must approve the preview.
- **`/claude/mcp` has no money-out writes** (payouts, transfers, deposits, cards, swaps). Skills never suggest a workaround.

`skills/whop-api/references/mcp.md` is the full contract: connecting, `intent`/`intent_id`, prepare-and-confirm, idempotency and error codes. Every other skill has a short `## With the Whop MCP server` section that links to it by skill name.

`scripts/mcp-tools.json` lists every tool on the plugin's route, with its safety flags. `validate.py` fails when a skill, command, subagent or eval mock names a tool that isn't in it.

**It refreshes itself.** The `Sync MCP tools` workflow (`.github/workflows/sync-mcp-tools.yml`) runs daily. `whopio/whop-mcp-server` is updated after every production deploy of `mcp.whop.com`, so the workflow follows production. On each run it:

1. Checks out that repo and generates its tool registry.
2. Runs `scripts/sync-mcp-tools.py`.
3. When tools were added, removed or re-flagged, or a mock's schema changed, opens or updates one PR on `bot/sync-mcp-tools`. The PR lists the changes and the results of `validate.py` and `npm test`. A server commit with the same tools changes nothing and opens no PR.
4. When `main` matches the server again, closes that PR.

When a sync PR arrives:

- **Its title says "Action needed".** A skill or eval names a removed tool. Fix the mention in that PR.
- **It adds tools.** Decide whether a skill should mention them.

Run it by hand from the Actions tab, with `mcp_ref` set to a branch, tag or commit to sync from somewhere else. Running the steps at the top of `scripts/sync-mcp-tools.py` locally does the same.

## Writing a skill

### Frontmatter

```yaml
---
name: whop-<name>            # must equal the folder name
description: >-
  <What it does, in one or two sentences.>
  Use when: "<trigger phrase>", "<trigger phrase>", ...
  NOT for: <case> (<skill>), <case> (<skill>).
license: Apache-2.0
metadata:
  author: whop
  version: "0.1.0"           # must equal VERSION
---
```

Only spec fields are allowed at the top level (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). The description is at most 1024 characters and must contain `Use when` and `NOT for`. Agents pick skills from the description alone, so put the words users actually type in the triggers. Keep it under about 750 characters: ten or so triggers users really type beat thirty that crowd out new ones, and the `whop` router and each skill's body handle chaining.

### Body

Aim for under 300 lines; 500 is the hard limit. The test for what stays in `SKILL.md`: if removing a section would stop the agent from deciding what to do next, it stays. Everything else moves to `references/`.

Sections, in this order:

1. `# Title` and one sentence on what the skill does.
2. `## Before you start` — what must be true first. Step 1 inspects the project (installed SDK version, framework, sandbox or production). Then the docs to fetch (only the guides the task needs; the versioning changelog is read on demand, when pinning or upgrading a version or when a response doesn't match), the client (via `whop-api`, with a fallback), sandbox keys and which credential type. The last step says sibling skills are optional.
3. `## Rules` — the numbered gotchas that cause real bugs. These are the most valuable lines in the skill.
4. `## Pick a path` — a decision table or tree from the user's goal to a workflow.
5. One `##` section per workflow: numbered steps with a minimal, correct snippet.
6. `## Verify` — how to prove it works in sandbox before going live. It ends by telling the agent to report what changed, which environment it targets, which checks ran, and what is still unverified.
7. `## Errors` — symptom → cause → fix. It opens with the rule that stops retry loops: after the same call fails twice, read the whole error and the docs, then change the approach. `validate.py` checks these lines.
8. `## References` — every file in `references/` with one line on when to read it, ending with `references/skill-feedback.md`.

### Code

- TypeScript first, using `@whop/sdk`: `import { WhopClient } from "@whop/sdk"` and `new WhopClient({ token: process.env.WHOP_API_KEY })`. Python (`whop-sdk`) where the docs show it.
- **TypeScript snippets that import only `@whop/sdk` / `@whop/sdk/helpers` (and Node built-ins) must compile on their own.** `npm run check:snippets` type-checks them against the pinned SDK with `strict`. Use literal placeholder IDs (`"biz_xxxxxxxxxxxxx"`) instead of undefined variables. Snippets that import a framework (Next.js, React) are skipped by the checker, so keep their Whop calls identical to a checked snippet.
- Money is in **major currency units** (dollars, `10.00` = $10.00) for prices, fees, transfers and payouts. Say so wherever an amount appears.
- Use current names: `variants` (not plans), `accounts` and `account_id` (not companies / `company_id`), `payouts` (not withdrawals), `deposits` (not top-ups), `unwrapWebhook` from `@whop/sdk/helpers`, `event.type`.
- Never put an API key in client-side code.

### Banned patterns

`scripts/validate.py` fails on these outside `skills/whop-migrate/references/legacy-map.md` (where they appear as the "old" column) and outside `skills/whop-communities/` for the chat embed packages, which chat still uses:

`btoa(`, `webhookKey`, `hosted_kyc`, `hosted_payouts`, `plans.create`, `companies.create`, `companies.list`, `companies.update`, `parent_company_id`, `withdrawals.create`, `topups.`, `chargeUser`, `mcp.whop.com/sse`, `new Whop(`, `plan_type`, `@whop/embedded-components`, `@whop/checkout`, `WhopCheckoutEmbed`, `membership.went_valid`, `from "@whop/api"`.

The list lives in `hooks/patterns.json` as each entry's `literal`. The same entries carry the `regex`, `fix` and `skill` the edit hook uses on code the agent writes, so the docs and the hook can't drift apart. When the API renames something, add one entry there with its fix (taken from `legacy-map.md`), plus a positive fixture in `tests/check-whop-code.test.mjs`; the test fails until every pattern has one.

### Self-contained

Each skill installs on its own (`npx skills add <repo> --skill whop-checkout`). No `../` paths. Every file in `references/` is linked from that skill's `SKILL.md`. If two skills need the same fact, each states it; small duplication beats a broken link. Naming another skill is fine, but never depend on it: say what to do when it isn't installed (a docs page, or the snippet itself).

### Skill feedback

Every skill has `references/skill-feedback.md`: when the user says the skill was wrong or outdated, the agent drafts a GitHub issue on `whopio/skills` with private data removed, shows it, and posts only after the user approves the exact text. The copies are generated from `scripts/skill-feedback.template.md`; edit the template and run `scripts/build-skill-feedback.py` (`validate.py` fails when they drift). People filing by hand use `.github/ISSUE_TEMPLATE/skill-feedback.md`.

## Commands, agents and hooks

The plugin ships more than skills. They are Claude Code features, so they never replace a skill's content: each one loads the matching skill and follows it.

| Path | What | Loaded by |
|---|---|---|
| `commands/*.md` | `/whop-developer:<file name>` slash commands (`connect`, `setup`, `test-webhook`, `audit`). Frontmatter: `description`, optional `argument-hint`; no `name`. After editing one, run `scripts/build-gemini-commands.py` to regenerate `commands/whop-developer/*.toml` | Claude Code, Cursor, Kimi Code; Gemini CLI through the generated TOML |
| `subagents/*.md` | Subagents (`whop-integration-reviewer`, `whop-migrator`), listed file by file in `agents` in the Claude and Cursor manifests (Claude Code takes `.md` paths, not a folder) and by folder in the Kimi manifest. `name` equals the file name; `skills` preloads skills from this repo; `tools` uses Claude Code tool names, which Kimi shares. Not `agents/`: Gemini CLI and Antigravity always load that folder and print errors for Claude-format agents | Claude Code, Cursor, Kimi Code |
| `hooks/claude-hooks.json` | `SessionStart`, `PostToolUse` and `PreToolUse` hooks (the last makes Claude Code ask the user before any Whop MCP call with `mcp_confirmation_token`, because evals showed models treat the original request as approval), declared in `.claude-plugin/plugin.json`. Not named `hooks/hooks.json`, because Cursor auto-loads that path and uses a different hook format | Claude Code |
| `hooks/*.mjs` | Hook scripts: Node built-ins only, read local files only, exit 0 on any error, print nothing when there is nothing to say | |
| `skills/<name>/scripts/` | Scripts that belong to one skill (`whop-webhooks/scripts/send-test-event.mjs`). Mention each from its `SKILL.md` | Every agent |
| `rules/whop.mdc`, `rules/whop.md` | The hooks' checks as a rule, for hosts without hooks. Both are generated from `scripts/rules.template.md` by `scripts/build-rules.py` (`validate.py` fails when they drift). Cursor reads only the `.mdc` (named in `.cursor-plugin/plugin.json`, which stops it scanning the folder); Antigravity reads `rules/*.md`. Both load the rule when the agent judges the description relevant, not on every message | Cursor, Antigravity |

Rules:

- **Hooks must be quiet and safe.** No network, no writes outside `$CLAUDE_PLUGIN_DATA` (or the OS temp dir), and no output for projects that don't use Whop. A hook that fires on a false positive costs the user's trust in every later message, so add a negative fixture for every new pattern too.
- **Commands and agents don't restate facts.** They say which skill to load and what to check; amounts, names and limits stay in the skills, which are the source of truth.
- **The MCP server is production.** `mcp.whop.com` acts on the signed-in user's live account and can't reach sandbox. Commands use it for reads; anything that creates or changes data goes through its prepare-and-confirm flow, and only when the user asks.
- **Test end to end.** `npm test` covers the scripts. Before changing a command, agent or hook, also run it in Claude Code against a scratch project: `claude -p "/whop-developer:audit" --plugin-dir .` (add `--output-format stream-json --verbose` to see hook output).

## Versioning

`VERSION` is the single version. It must match `metadata.version` in every `SKILL.md`, the `version` in every plugin manifest, and the `X-Whop-Plugin: skills/<version>` header in the MCP configs. `scripts/bump-version.py <new>` updates all of them.

| File | Read by |
|---|---|
| `plugin.json` + `mcp.json` | The [Agent Plugins](https://agent-plugins.org) 1.0 standard. Codex and GitHub Copilot CLI read this pair **first** whenever `plugin.json` carries the Agent Plugins `$schema`, so it must stay spec-valid: the manifest is a closed schema (OpenAI metadata goes under `extensions.com.openai`), and `mcp.json` needs its own `$schema` and `"type": "streamable-http"`. A non-conforming `mcp.json` makes those hosts drop the MCP server silently |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` + `.mcp.json` | Claude Code, `npx plugins`. `plugin.json` also points `hooks` at `hooks/claude-hooks.json` |
| `.codex-plugin/plugin.json` + `.mcp.json` | Older Codex builds and `npx plugins -t codex`, which otherwise generate a manifest with no branding. Current Codex reads `plugin.json` first. `interface` must equal `plugin.json`'s `extensions.com.openai.interface` |
| `.cursor-plugin/plugin.json` → `.mcp.json` | Cursor Marketplace. `mcpServers` points at `.mcp.json` explicitly: Cursor's format is Claude's (`"type": "http"`), and Whop's own Cursor plugin ships the same shape |
| `.grok-plugin/plugin.json` + `.mcp.json` | Grok Build |
| `.kimi-plugin/plugin.json` | Kimi Code. MCP is declared inline, because Kimi doesn't resolve file references. Kimi loads `skills/`, `commands/*.md` and `subagents/*.md` (it accepts Claude-style agent files and uses the same tool names) |
| `.antigravity-plugin/plugin.json` + `mcp_config.json` | Antigravity (takes precedence over the root `plugin.json`). Remote MCP uses `serverUrl`. Antigravity also loads `skills/` and `rules/*.md`; it would load an `agents/` folder or a root `hooks.json`, which is why subagents live in `subagents/` and Claude hooks in `hooks/`. `tests/manifests.test.mjs` checks the manifest against Antigravity's published schema; also run `agy plugin validate --strict .` when the CLI is available |
| `.agents/plugins/marketplace.json` | Codex marketplace (`codex plugin marketplace add whopio/skills`). One entry, `whop-developer`, with a local `./` source; its `name` matches the Claude marketplace so both install as `whop-developer@whop-skills` |
| `gemini-extension.json` | Gemini CLI (MCP inline, as `httpUrl`). Gemini reads commands only as TOML, so `commands/whop-developer/*.toml` is generated from `commands/*.md` by `scripts/build-gemini-commands.py`; `validate.py` fails when they drift. Gemini has no access to our subagents (they're Claude-format, outside the `agents/` folder Gemini scans), so `/whop-developer:audit` falls back to following `subagents/whop-integration-reviewer.md` |

Every host's MCP entry points at the same server: the official Whop MCP server, `https://mcp.whop.com/claude/mcp` (the route without money-out tools, until the hosted server offers a non-admin default on `/mcp`). Each sends `X-Whop-Plugin: skills/<version>` plus a host suffix, so Whop can tell where connections come from: none for `.mcp.json` (Claude Code, Cursor, Grok, older Codex), ` (agent-plugins)` for `mcp.json`, ` (gemini)`, ` (kimi)`, and ` (antigravity)` for `mcp_config.json`. `scripts/bump-version.py` and `validate.py` share that table.

**Hosts we don't ship to yet**, and why:

- OpenCode plugins are JavaScript modules rather than manifests. Skills already install with `npx skills add -a opencode`, and the MCP setup is in the README.

Before adding a host, read its loader or its docs for manifest precedence. Several hosts read the root `plugin.json` before their own folder.

## Checks

```bash
python3 scripts/validate.py      # structure, frontmatter, versions, references, banned patterns, commands, agents, hooks
npm run check:snippets           # type-check TypeScript snippets against the pinned @whop/sdk
npm test                         # hook scripts, the webhook test script, and plugin.json/mcp.json against the official Agent Plugins schemas
python3 scripts/check-links.py   # every docs.whop.com link in the skills returns 200
claude plugin validate .         # Claude Code's own manifest, command and agent checks (local; needs the claude CLI)
```

CI runs the first four on every PR. Dependabot bumps `@whop/sdk` weekly, so an SDK change that breaks a snippet fails CI instead of reaching users.

## Evals

Each `evals/<case>/` folder holds a `prompt.md` and `graders/*.md`. Claude Code's eval runner runs each case with and without the plugin and reports the difference:

```bash
claude plugin eval . --runs 3 --scaffold --allow-tools Write Edit   # all cases
claude plugin eval . --case 'whop-webhooks-*' --allow-tools Write Edit
```

Run the affected cases after any change to a `SKILL.md`, and compare scores before and after when rewording a description. When a bug is found by hand, add a case for it.

Eval notes:

- **MCP cases use mocks, never the live server.** `evals/mocks/whop/<tool>.md` holds the canned result for each mocked tool. `evals/mocks/whop/_tools.json` holds their real definitions (schemas, descriptions, the two-step notice), generated by `scripts/sync-mcp-tools.py`, so the model sees the server's actual contract. A tool with no mock isn't available in a run. Add a mock (and re-run the sync script) when a case needs another tool. Grade what reached the server with `target: mock_calls`, which also lists calls a hook denied; match `"verdict":"ok"` to count only the ones that ran.
- **Grant file tools** with `--allow-tools Write Edit` for cases that write files. Otherwise the file graders can't pass.
- **Test triggering, not only answers.** Most prompts name Whop. The `whop-router-*` cases don't: `whop-router-unnamed-paywall` runs in a project that already has `@whop/sdk` and asks for a paywall without saying "Whop", and `whop-router-stripe-project-quiet` asks the same in a Stripe project and fails if any `whop*` skill loads (`tool_used` with `max: 0` and `arm: both`). Run both whenever a description or the session-start hook changes.
- **Fixture projects come from a `case.yaml` `scaffold_script`**, which writes files into the empty workspace. It runs only with `--scaffold`; without it those cases score 0 because the files are missing.
- **Pass one `--case` per run.** A repeated `--case` keeps only the last value.
- **Hooks need a working `node` inside the eval sandbox,** which swaps `HOME`. A version manager's shim (mise, asdf) can break there, so put the real Node binary first on `PATH`, for example `PATH="$(dirname "$(mise which node)"):$PATH"`.
