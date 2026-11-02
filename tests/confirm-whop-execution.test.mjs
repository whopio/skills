import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { decide } from "../hooks/confirm-whop-execution.mjs";

const HOOK = fileURLToPath(new URL("../hooks/confirm-whop-execution.mjs", import.meta.url));
const call = (tool_name, tool_input) => ({ hook_event_name: "PreToolUse", tool_name, tool_input });

test("asks before a prepared operation executes, for the plugin's server and a hand-added one", () => {
  for (const tool of ["mcp__plugin_whop-developer_whop__payments_refund", "mcp__whop__payments_refund"]) {
    const out = decide(call(tool, { id: "pay_x", mcp_confirmation_token: "tok", idempotency_key: "k" }));
    assert.equal(out.hookSpecificOutput.hookEventName, "PreToolUse");
    assert.equal(out.hookSpecificOutput.permissionDecision, "ask");
    assert.match(out.hookSpecificOutput.permissionDecisionReason, /payments_refund/);
    assert.match(out.hookSpecificOutput.permissionDecisionReason, /id pay_x/);
  }
});

test("previews, reads and other servers pass through", () => {
  assert.equal(decide(call("mcp__plugin_whop-developer_whop__payments_refund", { id: "pay_x" })), null);
  assert.equal(decide(call("mcp__plugin_whop-developer_whop__payments_list", { account_id: "biz_x" })), null);
  assert.equal(decide(call("mcp__plugin_whop-developer_whop__payments_refund", { id: "pay_x", mcp_confirmation_token: "" })), null);
  assert.equal(decide(call("mcp__stripe__refunds_create", { mcp_confirmation_token: "tok" })), null);
  assert.equal(decide(call("mcp__notwhop__x", { mcp_confirmation_token: "tok" })), null);
  assert.equal(decide(call("Bash", { command: "ls" })), null);
});

test("the hook process prints the decision as JSON and exits 0 on bad input", () => {
  const hit = spawnSync(process.execPath, [HOOK], {
    input: JSON.stringify(call("mcp__plugin_whop-developer_whop__memberships_cancel", { id: "mem_x", mcp_confirmation_token: "tok" })),
    encoding: "utf8",
  });
  assert.equal(hit.status, 0);
  assert.equal(JSON.parse(hit.stdout).hookSpecificOutput.permissionDecision, "ask");

  const bad = spawnSync(process.execPath, [HOOK], { input: "nope", encoding: "utf8" });
  assert.equal(bad.status, 0);
  assert.equal(bad.stdout, "");
});
