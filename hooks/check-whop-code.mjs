#!/usr/bin/env node
// PostToolUse hook: after the agent writes or edits a file, flag stale Whop API
// names and unsafe patterns (API keys in client code, parsed webhook bodies) in
// the lines it just wrote. Patterns live in patterns.json, shared with
// scripts/validate.py. Never fails the tool call: any error exits 0 silently.

import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, extname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const CODE_EXTENSIONS = new Set([
  ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs",
  ".vue", ".svelte", ".astro", ".py", ".rb", ".go", ".php", ".java", ".kt", ".cs", ".rs", ".ex", ".exs",
]);
const MAX_FILE_BYTES = 1_000_000;
const MAX_FINDINGS = 15;

export function loadPatterns(path = join(HERE, "patterns.json")) {
  return JSON.parse(readFileSync(path, "utf8")).patterns.map((p) => ({
    ...p,
    re: new RegExp(p.regex, p.flags ?? ""),
    requiresRe: p.requires ? new RegExp(p.requires, p.requiresFlags ?? "") : null,
    unlessRe: p.unless ? new RegExp(p.unless) : null,
  }));
}

export function isEnvFile(filePath) {
  return /^\.env(\..+)?$/.test(basename(filePath));
}

export function isCheckedFile(filePath) {
  return isEnvFile(filePath) || CODE_EXTENSIONS.has(extname(filePath).toLowerCase());
}

/** The text the tool just put in the file, or null when the whole file is new. */
export function writtenText(toolName, toolInput) {
  if (toolName === "Write") return null;
  if (toolName === "Edit") return toolInput.new_string ?? "";
  if (toolName === "MultiEdit") return (toolInput.edits ?? []).map((e) => e.new_string ?? "").join("\n");
  return null;
}

/**
 * Findings for `content`. When `written` is a string, only lines that appear in
 * it are reported, so pre-existing code the agent didn't touch stays quiet.
 */
export function findIssues(filePath, content, written, patterns) {
  const envFile = isEnvFile(filePath);
  // Outside .env files, only look at files that are about Whop at all.
  if (!envFile && !/whop/i.test(content)) return [];
  const touched = written == null ? null : new Set(written.split("\n").map((l) => l.trim()).filter(Boolean));
  const lines = content.split("\n");
  const findings = [];
  for (const pattern of patterns) {
    // .env files only get the check for secrets under a client-bundled prefix.
    if (envFile && pattern.id !== "public-env-secret") continue;
    if (pattern.requiresRe && !pattern.requiresRe.test(content)) continue;
    if (pattern.unlessRe && pattern.unlessRe.test(content)) continue;
    lines.forEach((line, index) => {
      if (!pattern.re.test(line)) return;
      if (touched && !touched.has(line.trim())) return;
      findings.push({ pattern, line: index + 1, text: line.trim().slice(0, 160) });
    });
  }
  return findings;
}

export function formatReport(displayPath, findings) {
  const security = findings.filter((f) => f.pattern.severity === "security");
  const stale = findings.filter((f) => f.pattern.severity !== "security");
  const out = [];
  const render = (f) =>
    `- ${displayPath}:${f.line} \`${f.text}\`\n  ${f.pattern.fix} (skill: ${f.pattern.skill})`;
  if (security.length) {
    out.push("Whop security check: fix these before continuing.", ...security.slice(0, MAX_FINDINGS).map(render));
  }
  if (stale.length) {
    out.push(
      "Whop API check: these lines use names the current API replaced. Rewrite them unless you are deliberately keeping legacy code. Load the named skill for details; to confirm a name, check node_modules/@whop/sdk/reference.md or https://docs.whop.com/developer/api/migrate-from-previous-versions.md.",
      ...stale.slice(0, MAX_FINDINGS).map(render),
    );
  }
  const hidden = Math.max(0, security.length - MAX_FINDINGS) + Math.max(0, stale.length - MAX_FINDINGS);
  if (hidden) out.push(`(${hidden} more not shown)`);
  return out.join("\n");
}

function stateFile(sessionId) {
  const base = process.env.CLAUDE_PLUGIN_DATA || join(tmpdir(), "whop-developer-plugin");
  const dir = join(base, "check-whop-code");
  mkdirSync(dir, { recursive: true });
  const safe = createHash("sha256").update(String(sessionId || "no-session")).digest("hex").slice(0, 24);
  return join(dir, `${safe}.json`);
}

/** Drop findings already reported this session, and remember the new ones. */
export function dedupe(sessionId, filePath, findings) {
  let path;
  let seen = [];
  try {
    path = stateFile(sessionId);
    seen = JSON.parse(readFileSync(path, "utf8"));
  } catch {
    // first finding this session, or no writable state dir
  }
  const known = new Set(seen);
  const key = (f) => createHash("sha256").update(`${filePath}\0${f.pattern.id}\0${f.text}`).digest("hex").slice(0, 16);
  const fresh = findings.filter((f) => !known.has(key(f)));
  if (path && fresh.length) {
    try {
      writeFileSync(path, JSON.stringify([...known, ...fresh.map(key)].slice(-2000)));
    } catch {
      // dedupe is best effort
    }
  }
  return fresh;
}

export function run(input, patterns = loadPatterns()) {
  const toolInput = input.tool_input ?? {};
  const rawPath = toolInput.file_path;
  if (typeof rawPath !== "string" || !isCheckedFile(rawPath)) return null;
  const cwd = input.cwd || process.cwd();
  const filePath = isAbsolute(rawPath) ? rawPath : resolve(cwd, rawPath);
  let content;
  try {
    content = readFileSync(filePath, "utf8");
  } catch {
    return null;
  }
  if (content.length > MAX_FILE_BYTES) return null;
  const findings = dedupe(input.session_id, filePath, findIssues(filePath, content, writtenText(input.tool_name, toolInput), patterns));
  if (!findings.length) return null;
  const rel = relative(cwd, filePath);
  const displayPath = rel && !rel.startsWith("..") ? rel : filePath;
  return { decision: "block", reason: formatReport(displayPath, findings) };
}

async function main() {
  let raw = "";
  for await (const chunk of process.stdin) raw += chunk;
  const output = run(JSON.parse(raw));
  if (output) process.stdout.write(JSON.stringify(output));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => process.exit(0));
}
