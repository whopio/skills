---
description: Test this project's Whop webhook handler with signed events - valid signature, tampered signature, duplicate delivery and the 5-second deadline
argument-hint: "[handler URL] [event type]"
---

# Test the Whop webhook handler

Prove the project's webhook handler does what Whop requires, against the running dev server, with no tunnel and no Whop account. Arguments from the user: `$ARGUMENTS` (an optional handler URL and event type, default `payment.succeeded`).

Load the `whop-webhooks` skill first; its Rules are the pass criteria.

## 1. Find and read the handler

Search for `unwrapWebhook`, `webhook-signature` and routes named like `webhooks/whop`. Read the handler and check it against the skill's Rules: it verifies before reading anything, uses the raw body, passes the `ws_` secret unchanged, deduplicates on `webhook-id` / `event.id`, branches on dotted `event.type` names, and returns `2xx` quickly while the work runs in the background. Note each problem with `file:line`. If there is no handler yet, offer to write one with the skill instead.

## 2. Pick the secret and URL

- The handler reads its secret from an env var (usually `WHOP_WEBHOOK_SECRET`). The test only needs the script and the server to use **the same value**. If the user has no secret yet, generate a throwaway one for local use (`ws_` followed by 64 random hex characters) and have them start the dev server with it. Never print a real secret.
- The URL is the argument, or the dev server's origin plus the handler route. If the server isn't running, ask the user to start it, or start it in the background with their OK.

## 3. Send the events

The script ships with this plugin's `whop-webhooks` skill and needs Node 18+. It signs Whop's published example payload for the event the same way Whop signs deliveries:

```bash
node "${CLAUDE_PLUGIN_ROOT}/skills/whop-webhooks/scripts/send-test-event.mjs" --url <handler URL> --type <event> --repeat 2
node "${CLAUDE_PLUGIN_ROOT}/skills/whop-webhooks/scripts/send-test-event.mjs" --url <handler URL> --tamper
```

Pass the secret with `--secret` or `WHOP_WEBHOOK_SECRET` in the environment. Other flags: `--list-types`, `--data <file.json>` for a custom payload, `--account-id <biz_...>`. If `${CLAUDE_PLUGIN_ROOT}` doesn't expand in this environment, the script is at `scripts/send-test-event.mjs` inside the installed `whop-webhooks` skill.

## 4. Judge the result

| Check | Pass |
|---|---|
| Valid delivery | Every attempt returns `2xx` within 5 seconds (no redirects) |
| Duplicate delivery (`--repeat 2`) | The server logs show the work ran **once** |
| Tampered signature (`--tamper`) | The handler returns non-`2xx` and does no work |
| Event routing | The handler did the right thing for that `type` |

The script exits non-zero on the first three when they fail. For a failure, name the cause and the fix from the skill's Errors table, offer to fix the code, then run the script again.

## 5. Then test with real Whop deliveries

Local signing proves the code. Before going live, also run it against Whop: expose the server with a tunnel, create a **sandbox** webhook pointing at it, and send a test event (`webhooks.test` in the SDK, or the dashboard). Then make a sandbox purchase, as in the skill's Verify section. The Whop MCP server's `webhooks_test` tool only reaches **production** webhooks: use it only on a webhook the user names, and only after they say yes to sending it.
