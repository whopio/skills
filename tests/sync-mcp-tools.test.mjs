import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = fileURLToPath(new URL("../scripts/sync-mcp-tools.py", import.meta.url));

function write(root, path, content) {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), typeof content === "string" ? content : JSON.stringify(content, null, 2));
}

// 120 registry tools (the script refuses fewer than 100), plus the ones a test names.
function summary(extra = []) {
  const lines = [];
  for (let i = 0; i < 120; i++) lines.push(`things_list${i}  GET /things${i}  [native]  read_only`);
  lines.push(...extra, "", "120 operations (120 native), 0 exclusions, 0 pending review, API version 2026-10-30, generator 2.2.0.");
  return lines.join("\n");
}

function operation(toolName, method, path, safety) {
  return {
    toolName,
    method,
    path,
    surface: "native",
    description: `${toolName} description`,
    summary: toolName,
    inputSchema: { type: "object", properties: { id: { type: "string" } }, required: ["id"], additionalProperties: false },
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
    safety: { classification: "mutating", confirmationRequired: false, idempotency: "none", ...safety },
  };
}

function fakeServer({ docs = true, operations = [] } = {}) {
  const repo = mkdtempSync(join(tmpdir(), "fake-mcp-"));
  write(repo, "packages/server/src/policy/surfaces.ts", 'export const CLAUDE_DIRECTORY_EXCLUSIONS = new Map([\n\t["POST /payouts", "moves money"],\n]);\n');
  write(repo, "apps/worker/src/mcp-handler.ts", `createHandler({\n\tfeedbackSink: sink,\n\tdocs: ${docs},\n\tchatGptCompat: true,\n});\n`);
  write(repo, "packages/server/src/runtime/server.ts", 'const CONNECTION_STATUS_TOOL = { name: "connection_status" };\n');
  write(repo, "packages/server/src/runtime/feedback.ts", '\t{\n\t\tname: "report_feedback",\n\t},\n\t{\n\t\tname: "ask_question",\n\t},\n');
  write(repo, "packages/server/src/runtime/docs.ts", '\tname: "docs_search",\n\tname: "docs_query",\n');
  write(repo, "packages/server/src/runtime/chatgpt-compat.ts", '\tname: "search",\n\tname: "fetch",\n');
  write(repo, "packages/server/generated/manifest.json", { operations });
  execFileSync("git", ["init", "-q"], { cwd: repo });
  execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x"], { cwd: repo });
  return repo;
}

function skillsRoot(mocks = {}) {
  const root = mkdtempSync(join(tmpdir(), "fake-skills-"));
  mkdirSync(join(root, "scripts"), { recursive: true });
  for (const [path, body] of Object.entries(mocks)) write(root, path, body);
  return root;
}

function sync(root, repo, summaryText) {
  const summaryPath = join(root, "summary.txt");
  const reportPath = join(root, "report.md");
  writeFileSync(summaryPath, summaryText);
  const result = spawnSync("python3", [SCRIPT, repo, summaryPath, "--report", reportPath], {
    env: { ...process.env, WHOP_SKILLS_ROOT: root },
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  return {
    stdout: result.stdout,
    stderr: result.stderr,
    report: readFileSync(reportPath, "utf8"),
    tools: JSON.parse(readFileSync(join(root, "scripts/mcp-tools.json"), "utf8")),
  };
}

test("first sync writes the surface's tools, built-ins included, exclusions left out", () => {
  const root = skillsRoot();
  const { tools, report } = sync(root, fakeServer(), summary(["payouts_create  POST /payouts  [native]  mutating,financial,confirm"]));
  assert.equal(tools.tools.things_list0, "read_only");
  assert.equal(tools.tools.payouts_create, undefined, "excluded on claude_directory");
  for (const name of ["connection_status", "report_feedback", "ask_question", "docs_search", "docs_query", "search", "fetch"]) {
    assert.ok(name in tools.tools, name);
  }
  assert.equal(tools.surface, "claude_directory (https://mcp.whop.com/claude/mcp)");
  assert.match(tools.source, /^https:\/\/github\.com\/whopio\/whop-mcp-server\/tree\/[0-9a-f]{40}$/);
  assert.match(report, /127 tools\*\* \(127 added, 0 removed/);
});

test("a second sync with the same tools changes nothing, even from a new server commit", () => {
  const root = skillsRoot();
  sync(root, fakeServer(), summary());
  const before = readFileSync(join(root, "scripts/mcp-tools.json"), "utf8");
  const again = sync(root, fakeServer(), summary());
  assert.equal(readFileSync(join(root, "scripts/mcp-tools.json"), "utf8"), before);
  assert.match(again.stdout, /unchanged/);
  assert.match(again.report, /No tool or schema changes\./);
});

test("the report lists added, removed and re-flagged tools", () => {
  const root = skillsRoot();
  sync(root, fakeServer(), summary(["widgets_delete  DELETE /widgets/{id}  [native]  destructive,confirm", "widgets_get  GET /widgets/{id}  [native]  read_only"]));
  const { report, tools } = sync(root, fakeServer(), summary(["widgets_get  GET /widgets/{id}  [native]  mutating", "gadgets_list  GET /gadgets  [native]  read_only"]));
  assert.match(report, /### Added\n\n- `gadgets_list` \(read_only\)/);
  assert.match(report, /### Removed\n\n- `widgets_delete` \(destructive,confirm\)/);
  assert.match(report, /### Safety flags changed\n\n- `widgets_get` \(read_only -> mutating\)/);
  assert.match(report, /fails `validate.py`/);
  assert.equal(tools.tools.widgets_delete, undefined);
});

test("built-in tools follow the worker's options", () => {
  const root = skillsRoot();
  const { tools } = sync(root, fakeServer({ docs: false }), summary());
  assert.equal(tools.tools.docs_search, undefined);
  assert.equal(tools.tools.search, "read_only");
});

test("eval mock schemas mirror the server, and mocks of missing tools are reported", () => {
  const root = skillsRoot({
    "evals/mocks/whop/widgets_delete.md": "{}",
    "evals/mocks/whop/connection_status.md": "{}",
    "evals/case-a/mocks/whop/docs_search.md": "results",
  });
  const ops = [operation("widgets_delete", "delete", "/widgets/{id}", { classification: "destructive", confirmationRequired: true, idempotency: "supported" })];
  const repo = fakeServer({ docs: false, operations: ops });
  const { report, stderr } = sync(root, repo, summary(["widgets_delete  DELETE /widgets/{id}  [native]  destructive,confirm"]));

  const shared = JSON.parse(readFileSync(join(root, "evals/mocks/whop/_tools.json"), "utf8")).tools;
  assert.deepEqual(shared.map((t) => t.name), ["connection_status", "widgets_delete"]);
  const del = shared[1];
  assert.deepEqual(del.inputSchema.required, ["id", "intent", "intent_id"]);
  assert.equal(del.inputSchema.properties.mcp_confirmation_token, undefined);
  assert.ok(del.inputSchema.properties.idempotency_key);
  assert.doesNotMatch(del.description, /Two-step/);

  assert.match(stderr, /case-a\/mocks\/whop\/docs_search\.md mocks a tool the server doesn't have/);
  assert.match(report, /### Eval mocks for tools the server no longer has\n\n- `evals\/case-a\/mocks\/whop\/docs_search\.md`/);
  assert.match(report, /### Eval mock schemas updated/);
});

test("a tool group stays known after the server drops it, so validate.py still checks its names", () => {
  const root = skillsRoot();
  sync(root, fakeServer(), summary(["widgets_get  GET /widgets/{id}  [native]  read_only"]));
  const { tools } = sync(root, fakeServer({ docs: false }), summary());
  assert.equal(tools.tools.widgets_get, undefined);
  assert.equal(tools.tools.docs_search, undefined);
  assert.ok(tools.knownGroups.includes("widgets"));
  assert.ok(tools.knownGroups.includes("docs"));
  assert.ok(!tools.knownGroups.includes("search"), "names without an underscore aren't groups");
});
