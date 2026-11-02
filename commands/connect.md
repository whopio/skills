---
description: Check the Whop connection - who the MCP server is signed in as, which businesses it reaches, and how that differs from this project's API key
argument-hint: "[biz_... to check]"
---

# Check the Whop connection

Report what the agent can reach on Whop, and how that differs from what the project's code uses. A business the user mentioned: `$ARGUMENTS` (may be empty). This command only reads. It changes nothing.

Load the `whop-api` skill. Its `references/mcp.md` covers the MCP server.

## 1. The MCP server

Call `connection_status`.

- **It works.** Report the signed-in user, the permission profile and the number of tools, and whether `docs_search` is available for reading the docs. Then call `accounts_list` and name each business with its `biz_` ID. If `account_id` in the status is null, say that no business is bound: each call picks one with `account_id`. If the user named a business, say whether it's in the list.
- **The tool doesn't exist.** The server isn't loaded. In Claude Code, run `/plugin` to check that `whop-developer` is enabled, then `/mcp` to see the `whop` server's state. Restart after installing a plugin. In other tools, open their MCP settings.
- **It returns `not_authenticated`.** Sign-in isn't finished. In Claude Code, run `/mcp`, pick `whop` and authenticate: a browser opens to Whop. No API key is involved.

Say plainly what was granted: the connection acts as this user, on their **live** account, across every business they manage, and it can't reach sandbox. They can disconnect it from `/mcp`.

## 2. The project's own credentials

Look at the project, never printing values:

- `WHOP_*` variable names in `.env*` files and which environment the code selects (`WhopEnvironment.Sandbox` or production). A key under `NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_` or a similar prefix is a security problem: say so first.
- The installed `@whop/sdk` version (or `whop-sdk`, `whop_sdk`).

Explain the split in one or two sentences. The app's code authenticates with that API key, against sandbox while developing. The MCP server is the user's own sign-in, for the agent's lookups. A key from one environment doesn't work in the other.

## 3. Summarize

Give one short table: MCP (user, businesses, live), API key (variable name, sandbox or production, SDK version), and anything that needs fixing. If something is missing, say the single next step (`/whop-developer:setup` sets up the API key and client). Then stop.
