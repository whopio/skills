import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { buildContext, CHECKED_SDK_VERSION, profile } from "../hooks/session-start.mjs";

const HOOK = fileURLToPath(new URL("../hooks/session-start.mjs", import.meta.url));
const SKILLS_PACKAGE = JSON.parse(
  (await import("node:fs")).readFileSync(fileURLToPath(new URL("../package.json", import.meta.url)), "utf8"),
);

function project(files) {
  const dir = mkdtempSync(join(tmpdir(), "whop-session-"));
  for (const [path, content] of Object.entries(files)) {
    mkdirSync(join(dir, path, ".."), { recursive: true });
    writeFileSync(join(dir, path), typeof content === "string" ? content : JSON.stringify(content));
  }
  return dir;
}

test("CHECKED_SDK_VERSION matches the SDK the snippets are checked against", () => {
  assert.equal(CHECKED_SDK_VERSION, SKILLS_PACKAGE.devDependencies["@whop/sdk"]);
});

test("non-Whop projects get no context", () => {
  const dir = project({ "package.json": { dependencies: { stripe: "^17.0.0", next: "15.0.0" } }, ".env": "STRIPE_KEY=x\n" });
  assert.equal(buildContext(profile(dir)), null);
});

test("current SDK at the checked version: packages and MCP notes, no warnings", () => {
  const dir = project({
    "package.json": { dependencies: { "@whop/sdk": "^2.7.0" } },
    "node_modules/@whop/sdk/package.json": { version: CHECKED_SDK_VERSION },
  });
  const context = buildContext(profile(dir));
  assert.match(context, /@whop\/sdk 2\.7\.0/);
  assert.match(context, /connection_status/);
  assert.match(context, /production/);
  assert.doesNotMatch(context, /type-checked against/);
});

test("a different installed SDK version is called out", () => {
  const dir = project({
    "package.json": { dependencies: { "@whop/sdk": "^2.9.0" } },
    "node_modules/@whop/sdk/package.json": { version: "2.9.1" },
  });
  assert.match(buildContext(profile(dir)), /this project has 2\.9\.1/);
});

test("SDK 1.x and @whop/api point to whop-migrate", () => {
  const dir = project({ "package.json": { dependencies: { "@whop/sdk": "^1.4.0", "@whop/api": "^0.0.50" } } });
  const context = buildContext(profile(dir));
  assert.match(context, /predates 2\.x/);
  assert.match(context, /@whop\/api is deprecated/);
});

test("workspace packages are found", () => {
  const dir = project({
    "package.json": { private: true, workspaces: ["apps/*"] },
    "apps/web/package.json": { dependencies: { "@whop/checkout": "^0.0.30" } },
  });
  assert.match(buildContext(profile(dir)), /@whop\/checkout is replaced/);
});

test("Python and Ruby SDKs are detected", () => {
  assert.match(buildContext(profile(project({ "requirements.txt": "whop-sdk==0.4.0\n" }))), /whop-sdk \(Python\)/);
  assert.match(buildContext(profile(project({ Gemfile: 'gem "whop_sdk"\n' }))), /whop_sdk \(Ruby\)/);
});

test("client-prefixed Whop secrets in .env are flagged by name only", () => {
  const dir = project({ ".env.local": "NEXT_PUBLIC_WHOP_API_KEY=apik_super_secret\nWHOP_WEBHOOK_SECRET=ws_abc\n" });
  const context = buildContext(profile(dir));
  assert.match(context, /NEXT_PUBLIC_WHOP_API_KEY \(\.env\.local\)/);
  assert.doesNotMatch(context, /apik_super_secret|ws_abc/);
});

test("the hook process emits SessionStart additionalContext and exits 0", () => {
  const dir = project({ "package.json": { dependencies: { "@whop/sdk": "^2.7.0" } } });
  const result = spawnSync(process.execPath, [HOOK], {
    input: JSON.stringify({ hook_event_name: "SessionStart", source: "startup", cwd: dir }),
    env: { ...process.env, CLAUDE_PROJECT_DIR: "" },
    encoding: "utf8",
  });
  assert.equal(result.status, 0);
  const out = JSON.parse(result.stdout);
  assert.equal(out.hookSpecificOutput.hookEventName, "SessionStart");
  assert.match(out.hookSpecificOutput.additionalContext, /This project uses Whop/);

  const empty = spawnSync(process.execPath, [HOOK], { input: JSON.stringify({ cwd: project({}) }), env: { ...process.env, CLAUDE_PROJECT_DIR: "" }, encoding: "utf8" });
  assert.equal(empty.status, 0);
  assert.equal(empty.stdout, "");
});
