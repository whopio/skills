import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { decide, loadTools } from "../hooks/confirm-whop-execution.mjs";

const HOOK = fileURLToPath(new URL("../hooks/confirm-whop-execution.mjs", import.meta.url));
const call = (tool_name, tool_input) => ({ hook_event_name: "PreToolUse", tool_name, tool_input });
const TOOLS = {
  payments_refund: "mutating,financial,confirm",
  "api-keys_create": "mutating,credential,confirm",
  webhooks_delete: "destructive,confirm",
  payments_list: "read_only",
  products_create: "mutating",
};

test("asks before a flagged tool runs, for the plugin's server and a hand-added one", () => {
  for (const tool of ["mcp__plugin_whop-developer_whop__payments_refund", "mcp__whop__payments_refund"]) {
    const out = decide(call(tool, { id: "pay_x", idempotency_key: "k" }), TOOLS);
    assert.equal(out.hookSpecificOutput.hookEventName, "PreToolUse");
    assert.equal(out.hookSpecificOutput.permissionDecision, "ask");
    assert.match(out.hookSpecificOutput.permissionDecisionReason, /payments_refund/);
    assert.match(out.hookSpecificOutput.permissionDecisionReason, /id pay_x/);
    assert.match(out.hookSpecificOutput.permissionDecisionReason, /moves money/);
  }
  assert.match(decide(call("mcp__whop__api-keys_create", {}), TOOLS).hookSpecificOutput.permissionDecisionReason, /changes credentials/);
  assert.match(decide(call("mcp__whop__webhooks_delete", { id: "hook_x" }), TOOLS).hookSpecificOutput.permissionDecisionReason, /id hook_x/);
});

test("reads, ordinary writes, unknown tools and other servers pass through", () => {
  assert.equal(decide(call("mcp__plugin_whop-developer_whop__payments_list", { account_id: "biz_x" }), TOOLS), null);
  assert.equal(decide(call("mcp__plugin_whop-developer_whop__products_create", {}), TOOLS), null);
  assert.equal(decide(call("mcp__plugin_whop-developer_whop__not_a_tool", {}), TOOLS), null);
  assert.equal(decide(call("mcp__stripe__payments_refund", { id: "ch_x" }), TOOLS), null);
  assert.equal(decide(call("Bash", { command: "ls" }), TOOLS), null);
});

test("the shipped tool list asks before refunds and cancellations, not reads", () => {
  const tools = loadTools();
  for (const name of ["payments_refund", "memberships_cancel"]) assert.ok(decide(call(`mcp__whop__${name}`, {}), tools), name);
  assert.equal(decide(call("mcp__whop__payments_list", {}), tools), null);
});

test("the hook process prints the decision as JSON and exits 0 on bad input", () => {
  const hit = spawnSync(process.execPath, [HOOK], {
    input: JSON.stringify(call("mcp__plugin_whop-developer_whop__payments_refund", { id: "pay_x" })),
    encoding: "utf8",
  });
  assert.equal(hit.status, 0);
  assert.equal(JSON.parse(hit.stdout).hookSpecificOutput.permissionDecision, "ask");

  const bad = spawnSync(process.execPath, [HOOK], { input: "nope", encoding: "utf8" });
  assert.equal(bad.status, 0);
  assert.equal(bad.stdout, "");
});
