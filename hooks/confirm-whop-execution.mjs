#!/usr/bin/env node
// PreToolUse hook on the Whop MCP tools. The server runs every tool on the
// first call and leaves approval to the host, so a refund, a cancellation, a
// deletion or a new credential runs on the user's live account as soon as the
// model calls it. Make Claude Code ask the user before each one, even when the
// Whop tools are always-allowed, so a model can't treat the original request
// as the approval. Which tools ask comes from scripts/mcp-tools.json: every
// tool the server flags `confirm` (financial, credential and destructive).
// Reads and ordinary writes pass through untouched.

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PREFIX = /^mcp__(plugin_whop-developer_)?whop__/;

export function loadTools(path = fileURLToPath(new URL("../scripts/mcp-tools.json", import.meta.url))) {
  return JSON.parse(readFileSync(path, "utf8")).tools;
}

export function decide(input, tools = loadTools()) {
  const tool = String(input?.tool_name ?? "");
  if (!PREFIX.test(tool)) return null;
  const operation = tool.replace(PREFIX, "");
  const flags = String(tools[operation] ?? "").split(",");
  if (!flags.includes("confirm")) return null;
  const args = input?.tool_input ?? {};
  const target = ["id", "account_id"].map((key) => (typeof args[key] === "string" ? `${key} ${args[key]}` : null)).filter(Boolean).join(", ");
  const kind = flags.includes("financial") ? "moves money" : flags.includes("credential") ? "changes credentials" : "changes your account";
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason:
        `\`${operation}\`${target ? ` (${target})` : ""} ${kind} and runs on your live Whop account as soon as you approve. ` +
        "Check the arguments before you allow it.",
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
