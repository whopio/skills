import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { findIssues, loadPatterns, run, writtenText } from "../hooks/check-whop-code.mjs";

const HOOK = fileURLToPath(new URL("../hooks/check-whop-code.mjs", import.meta.url));
const patterns = loadPatterns();

// One line per pattern that must be flagged in a file that mentions Whop.
const POSITIVE = {
  "whop-api-package": 'import { WhopServerSdk } from "@whop/api";',
  "sdk-default-import": 'import Whop from "@whop/sdk";',
  "new-whop": "const whop = new Whop({ apiKey: key });",
  "client-apikey-option": "const whop = new WhopClient({ apiKey: process.env.WHOP_API_KEY });",
  "sandbox-base-url": 'const whop = new WhopClient({ token, baseURL: "https://sandbox-api.whop.com/api/v1" });',
  "webhook-key-option": "const whop = new WhopClient({ token, webhookKey: key });",
  "base64-webhook-secret": "const key = btoa(process.env.WHOP_WEBHOOK_SECRET);",
  "webhooks-unwrap-method": "const event = whop.webhooks.unwrap(body, { headers });",
  "plans-namespace": 'await whop.plans.create({ product_id: "prod_x" });',
  "companies-namespace": "const company = await whop.companies.retrieve(id);",
  "parent-company-id": 'await whop.accounts.create({ parent_company_id: "biz_x" });',
  "company-id-field": 'await whop.products.list({ company_id: "biz_x" });',
  "withdrawals-namespace": "await whop.withdrawals.create({ amount: 10 });",
  "topups-namespace": "await whop.topups.create({ amount: 10 });",
  "renamed-namespaces": "await whop.payoutMethods.list();",
  "charge-user": "await whop.chargeUser({ userId });",
  "pay-user": "await whop.payUser({ userId, amount });",
  "checkout-sessions": "const session = await createCheckoutSession(plan);",
  "hosted-kyc": 'await whop.accountLinks.create({ use_case: "hosted_kyc" });',
  "hosted-payouts": 'await whop.accountLinks.create({ use_case: "hosted_payouts" });',
  "plan-type": 'await whop.variants.create({ plan_type: "renewal" });',
  "add-free-days": "await fetch(`${base}/memberships/${id}/add_free_days`);",
  "went-valid-events": 'if (event.type === "membership.went_valid") grant();',
  "membership-deactivated-event": 'if (event.type === "membership.deactivated") revoke();',
  "underscored-event-names": 'if (event.type === "payment_succeeded") fulfill();',
  "withdrawal-events": 'case "payout.completed":',
  "api-v2-and-graphql": 'fetch("https://api.whop.com/api/v2/memberships");',
  "mcp-sse-url": 'const url = "https://mcp.whop.com/sse";',
  "old-checkout-embed": 'import { WhopCheckoutEmbed } from "@whop/checkout/react";',
  "embedded-components-for-payouts": 'import { PayoutsSession } from "@whop/embedded-components-react-js"; // payouts',
  "amount-in-cents": "await whop.variants.create({ initial_price: price * 100 });",
  "public-env-secret": "const key = process.env.NEXT_PUBLIC_WHOP_API_KEY;",
  "secret-in-client-component": "const key = process.env.WHOP_API_KEY;",
  "hardcoded-webhook-secret": 'const secret = "ws_0123456789abcdef0123456789abcdef0123456789abcdef";',
  "webhook-parsed-body": "const event = unwrapWebhook(JSON.stringify(await request.json()), { headers, key });",
};

// Correct current code that must not be flagged.
const NEGATIVE = [
  'import { WhopClient, WhopEnvironment } from "@whop/sdk";',
  "const whop = new WhopClient({ token: process.env.WHOP_API_KEY!, environment: WhopEnvironment.Sandbox });",
  'import { unwrapWebhook } from "@whop/sdk/helpers";',
  "const event = unwrapWebhook(await request.text(), { headers: Object.fromEntries(request.headers), key: process.env.WHOP_WEBHOOK_SECRET! });",
  'await whop.variants.create({ product_id: "prod_x", billing_type: "renewal", initial_price: 10.0 });',
  'await whop.accounts.list({ parent_account_id: "biz_x" });',
  'await whop.payouts.create({ account_id: "biz_x", amount: 25.0, payout_method_id: "x" });',
  'if (event.type === "payment.succeeded") fulfill(event.data);',
  'if (event.type === "membership.updated") resync();',
  'case "ad_campaign.payment_failed":',
  'await whop.checkoutConfigurations.create({ plan: { initial_price: 29.0 } });',
  'const btn = btoa(JSON.stringify(state)); // unrelated base64',
  'import { ChatElement } from "@whop/embedded-components-react-js";',
  "const url = process.env.NEXT_PUBLIC_WHOP_APP_ID;",
];

const header = "// Whop integration\n";

test("every pattern has a positive fixture", () => {
  const missing = patterns.map((p) => p.id).filter((id) => !(id in POSITIVE));
  assert.deepEqual(missing, []);
});

for (const pattern of patterns) {
  test(`flags ${pattern.id}`, () => {
    const prefix = pattern.id === "secret-in-client-component" ? '"use client";\n' : "";
    const content = `${prefix}${header}${POSITIVE[pattern.id]}\n`;
    const ids = findIssues("/app/src/file.ts", content, null, patterns).map((f) => f.pattern.id);
    assert.ok(ids.includes(pattern.id), `expected ${pattern.id}, got ${JSON.stringify(ids)}`);
  });
}

test("current code is not flagged", () => {
  for (const line of NEGATIVE) {
    const findings = findIssues("/app/src/file.ts", `${header}${line}\n`, null, patterns);
    assert.deepEqual(findings.map((f) => f.pattern.id), [], line);
  }
});

test("Elements code may convert to minor units", () => {
  const content = `${header}import { Payments } from "@whop/elements";\nconst handle = payments.create({ amount: price * 100 });\n`;
  assert.deepEqual(findIssues("/app/pay.ts", content, null, patterns), []);
});

test("server code may read WHOP_API_KEY", () => {
  const findings = findIssues("/app/server.ts", `${header}const key = process.env.WHOP_API_KEY;\n`, null, patterns);
  assert.deepEqual(findings, []);
});

test("files that never mention Whop are skipped", () => {
  assert.deepEqual(findIssues("/app/a.ts", "await client.plans.create({});\nconst k = btoa(secret);\n", null, patterns), []);
});

test(".env files only get the public-prefix check", () => {
  const env = "NEXT_PUBLIC_WHOP_API_KEY=apik_x\nWHOP_WEBHOOK_SECRET=ws_0123456789abcdef0123456789abcdef0123\nWHOP_COMPANY_ID=biz_x\n";
  const ids = findIssues("/app/.env.local", env, null, patterns).map((f) => f.pattern.id);
  assert.deepEqual(ids, ["public-env-secret"]);
});

test("Edit only reports lines the edit wrote", () => {
  const content = `${header}await whop.plans.create({});\nawait whop.companies.list();\n`;
  const written = writtenText("Edit", { new_string: "await whop.companies.list();" });
  const ids = findIssues("/app/a.ts", content, written, patterns).map((f) => f.pattern.id);
  assert.deepEqual(ids, ["companies-namespace"]);
});

test("MultiEdit joins every new_string", () => {
  assert.equal(writtenText("MultiEdit", { edits: [{ new_string: "a" }, { new_string: "b" }] }), "a\nb");
  assert.equal(writtenText("Write", { content: "x" }), null);
});

function hookInput(dir, filePath, extra = {}) {
  return { session_id: `test-${Math.random()}`, cwd: dir, hook_event_name: "PostToolUse", tool_name: "Write", tool_input: { file_path: filePath }, ...extra };
}

test("run() blocks with a report naming file, line, fix and skill", () => {
  const dir = mkdtempSync(join(tmpdir(), "whop-hook-"));
  const file = join(dir, "route.ts");
  writeFileSync(file, `${header}import Whop from "@whop/sdk";\nconst k = btoa(process.env.WHOP_WEBHOOK_SECRET);\n`);
  process.env.CLAUDE_PLUGIN_DATA = dir;
  const out = run(hookInput(dir, file));
  assert.equal(out.decision, "block");
  assert.match(out.reason, /route\.ts:2/);
  assert.match(out.reason, /route\.ts:3/);
  assert.match(out.reason, /WhopClient/);
  assert.match(out.reason, /skill: whop-webhooks/);
});

test("run() reports a finding once per session", () => {
  const dir = mkdtempSync(join(tmpdir(), "whop-hook-"));
  const file = join(dir, "a.ts");
  writeFileSync(file, `${header}await whop.plans.list();\n`);
  process.env.CLAUDE_PLUGIN_DATA = dir;
  const input = hookInput(dir, file, { session_id: "same-session" });
  assert.ok(run(input));
  assert.equal(run(input), null);
});

test("run() ignores clean files, non-code files and missing files", () => {
  const dir = mkdtempSync(join(tmpdir(), "whop-hook-"));
  process.env.CLAUDE_PLUGIN_DATA = dir;
  const clean = join(dir, "ok.ts");
  writeFileSync(clean, `${header}import { WhopClient } from "@whop/sdk";\n`);
  const md = join(dir, "notes.md");
  writeFileSync(md, "Whop plans.create( is old\n");
  assert.equal(run(hookInput(dir, clean)), null);
  assert.equal(run(hookInput(dir, md)), null);
  assert.equal(run(hookInput(dir, join(dir, "missing.ts"))), null);
  assert.equal(run({ tool_name: "Bash", tool_input: { command: "ls" } }), null);
});

test("the hook process prints JSON on findings and nothing otherwise, always exit 0", () => {
  const dir = mkdtempSync(join(tmpdir(), "whop-hook-"));
  const file = join(dir, "a.ts");
  writeFileSync(file, `${header}const k = process.env.NEXT_PUBLIC_WHOP_API_KEY;\n`);
  const env = { ...process.env, CLAUDE_PLUGIN_DATA: dir };
  const hit = spawnSync(process.execPath, [HOOK], { input: JSON.stringify(hookInput(dir, file)), env, encoding: "utf8" });
  assert.equal(hit.status, 0);
  const parsed = JSON.parse(hit.stdout);
  assert.equal(parsed.decision, "block");
  assert.match(parsed.reason, /security/);

  const bad = spawnSync(process.execPath, [HOOK], { input: "not json", env, encoding: "utf8" });
  assert.equal(bad.status, 0);
  assert.equal(bad.stdout, "");
});
