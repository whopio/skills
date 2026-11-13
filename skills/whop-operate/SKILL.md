---
name: whop-operate
description: >-
  Run the user's live Whop business through the Whop MCP tools: websites on
  *.whop.app, products, checkout links, payments, refunds, disputes,
  memberships, ads, LLC/C-corp formation, and stats. Use when: "refund this
  customer", "how much did I make this month", "launch a product on Whop",
  "create a checkout link", "pause my Whop ads", "deploy my Whop site", "form
  an LLC with Whop", "who cancelled this week". NOT for: writing code that
  calls the Whop API (pick the skill with the whop router), sending payouts
  or transfers (not available on this connection; send the user to whop.com).
license: Apache-2.0
metadata:
  author: whop
  version: "0.5.0"
---

# Run a Whop business

This skill works on the user's live Whop business through the Whop MCP
server. Use these tools for work on the user's Whop account. For anything outside
Whop — another store platform, another ad account, general business advice — use
whatever else the user has set up. No CLI is needed.

## Before anything else

1. **Check the connection.** Call `connection_status`. It returns the authenticated
   identity, the selected account, granted scopes, and tool coverage. If it fails or
   the plugin's tools are missing, the user has not completed OAuth — tell them to
   run `/whop-developer:connect` (or `/mcp` in Claude Code and sign in to `whop`).
2. **Discover, do not guess.** Tool names follow `<group>_<operation>`, with
   hyphens inside multi-word groups (`payments_list`, `ad-campaigns_get`). Read
   the tool's own schema before calling it. Never invent a tool name, a field, or an
   enum value — if you cannot find it, say so and ask.
3. **Know the account.** `connection_status` returns `account_id`, and it is often
   **null** — a user grant is not bound to one business. When it is null, nothing is
   selected for you: get the id from `accounts_list` and pass `account_id` (`biz_…`)
   explicitly on account-scoped calls. Never assume a default business.

## What to run

| Job | Start here | Playbook |
| --- | --- | --- |
| Check who I am / what I can do | `connection_status` | — |
| Ship a website on `*.whop.app` | `apps_create`, then `apps_deploy` | [references/websites.md](references/websites.md) |
| Sell something | `products_*`, `plans_*`, `checkout-configurations_*` | — |
| Customers and access | `members_*`, `memberships_*` | — |
| Payments, refunds, disputes | `payments_*`, `refunds_*`, `disputes_*` | — |
| Run ads | `ads_*`, `ad-campaigns_*`, `ad-groups_*` | [references/ads.md](references/ads.md) |
| Form an LLC or C-corp | `accounts_form_company` | [references/formation.md](references/formation.md) |
| Measure | `stats_*`, `exports_*`, `events_*`, `people_*` | — |
| Developer surface | `apps_*`, `app-builds_*`, `api-keys_*`, `webhooks_*` | — |

The table is a router, not a schema. Read the playbook before websites, ads, or
formation — each has ordering traps that a tool description alone does not teach.

## Working with app source

`apps_deploy` builds the app's **current source on Whop** and ships it, so deploying
an app Whop already holds needs nothing local. Only one deployment runs per app at a
time; calling it again reports the running one instead of starting a second, and
calling it with nothing to publish says so. Pass `draft: true` to upload without
making it live.

To ship code that only exists on this machine, do the local half yourself and the
rest over MCP: write and build the files with your own tools, upload the artifact
with `files_create` / `files_complete`, register it with `app-builds_create`, then
`app-builds_promote`. Do not tell the user to install a CLI for this.

## Working agreement

- **Confirm before anything spends money or goes live.** Before launching or
  unpausing an ad campaign, raising a budget, retrying an ad payment, deploying or
  promoting a site build (anything but `draft: true`), or charging a customer, say
  what will happen and what it costs, and wait for the user to say yes. The same
  goes for refunds, cancellations and deletions: every tool runs on the first
  call, so the yes comes before the call. Pass a stable `idempotency_key` and
  reuse it on retries. Drafts and reads need no confirmation.
- **Action links are for the user, not for you.** When a response carries
  `authorize_url`, `session_url`, `deposit_url`, or `checkout_url`, give the link to
  the user and say what they need to finish there. Do not fetch or curl it to
  "verify" — that does not complete the flow and can consume a single-use URL.
  Re-run the matching `get`/`list` afterwards to confirm the outcome.
- `hosted_url` is not an action link. For an app it is the live app URL — display it.
- **Never echo secrets.** API keys, access tokens, and founder identity data (SSN,
  date of birth, home address) are legitimate inputs to the flows that need them.
  Pass them straight through to the tool. Never repeat them back in your response,
  write them to a file, or infer a value the user did not supply.

## What these tools cannot reach

This connection deliberately leaves out AI media generation and anything that moves
money out of the account: payouts, transfers, bounty rewards, card issuing, balance
top-ups, and trading. If the user asks for one of those, say it is not available
here and send them to whop.com to do it themselves. Do not look for a workaround.

Passkeys and OAuth grants (`users_me_passkeys*`, `users_me_oauth_grants*`) need a
first-party whop.com browser session and are also absent. Send the user to whop.com
for those.

## Verify

1. After a change, read it back with the matching `get` or `list` tool (`payments_get` after a refund, `products_get` after an edit) and check the fields you meant to change.
2. For a website or app deploy, open the `hosted_url` it returns and check the page loads.
3. For anything the user finishes in the browser (an authorization, a checkout, onboarding), re-run the matching `get` or `list` once they say they're done.

When you're done, tell the user what changed, which environment it targets (sandbox or production; if that isn't decided yet, say so and recommend sandbox first), which of these checks you ran, and what is still unverified. This connection always works on production.

## Errors

If the same call fails twice, stop retrying it. Read the whole error (`code`, message and request ID), check the tool's schema and the docs (`docs_search`), then change the request or the approach.

| Symptom | Cause | Fix |
|---|---|---|
| `not_authenticated`, or no Whop tools at all | The user hasn't signed in to the MCP server | Ask them to run `/mcp` and sign in to `whop` |
| `account_required` | No business picked | Get the `biz_` ID from `accounts_list` and pass `account_id` |
| `missing_scope` | The sign-in doesn't cover this tool | Tell the user which scope is missing |
| The tool the user wants isn't listed | Payouts, transfers and deposits aren't on this connection | Send the user to whop.com to do it |

## References

- [references/websites.md](references/websites.md): read before creating, building or deploying a website.
- [references/ads.md](references/ads.md): read before creating, launching or funding an ad campaign.
- [references/formation.md](references/formation.md): read before forming an LLC or C-corp.
- [references/skill-feedback.md](references/skill-feedback.md): read when the user says this skill gave wrong, outdated or missing guidance, or the docs contradicted it during the task.
