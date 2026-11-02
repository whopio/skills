#!/usr/bin/env node
// PreToolUse hook on the Whop MCP tools: a call that carries an
// mcp_confirmation_token executes a prepared operation (a refund, a
// cancellation, a deletion, a new webhook secret...) on the user's live
// account. Make Claude Code ask the user every time, even when the Whop tools
// are always-allowed, so a model can't treat the original request as the
// approval. Preview calls (no token) and reads pass through untouched.

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function decide(input) {
  const tool = String(input?.tool_name ?? "");
  const args = input?.tool_input ?? {};
  if (!/^mcp__(plugin_whop-developer_)?whop__/.test(tool)) return null;
  if (typeof args.mcp_confirmation_token !== "string" || !args.mcp_confirmation_token) return null;
  const operation = tool.replace(/^mcp__(plugin_whop-developer_)?whop__/, "");
  const target = ["id", "account_id"].map((key) => (typeof args[key] === "string" ? `${key} ${args[key]}` : null)).filter(Boolean).join(", ");
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason:
        `This executes the prepared Whop operation \`${operation}\`${target ? ` (${target})` : ""} on your live account. ` +
        "Approve only if you've seen the preview and want it to run now.",
    },
  };
}

async function main() {
  let raw = "";
  for await (const chunk of process.stdin) raw += chunk;
  const output = decide(JSON.parse(raw));
  if (output) process.stdout.write(JSON.stringify(output));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => process.exit(0));
}
