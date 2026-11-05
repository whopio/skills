#!/usr/bin/env node
// SessionStart hook: when the project already uses Whop, tell the agent which
// Whop packages it has, which of them are deprecated, and how the bundled MCP
// server relates to the code it writes. Prints nothing for non-Whop projects.
// Reads only dependency manifests and .env variable names (never values).

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// The SDK version every TypeScript snippet in the skills is type-checked against:
// the plugin's own pinned dev dependency (bumped by Dependabot).
export const CHECKED_SDK_VERSION = (() => {
  try {
    const pkg = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "package.json"), "utf8"));
    return pkg.devDependencies?.["@whop/sdk"] ?? null;
  } catch {
    return null;
  }
})();

const LEGACY_JS = {
  "@whop/api": "deprecated; the public GraphQL API behind it stopped on October 26, 2026. Move to `@whop/sdk` (`whop-migrate`).",
  "@whop/checkout": "replaced by `@whop/elements-react` / `@whop/elements` (`whop-checkout`).",
};
const WORKSPACE_DIRS = ["apps", "packages", "services", "web", "server", "backend", "frontend"];
const MAX_MANIFESTS = 40;

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return null;
  }
}

function readText(path) {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}

/** package.json files at the root and one level into common workspace folders. */
export function findPackageJsons(root) {
  const found = [];
  if (existsSync(join(root, "package.json"))) found.push(join(root, "package.json"));
  for (const dir of WORKSPACE_DIRS) {
    let entries = [];
    try {
      entries = readdirSync(join(root, dir), { withFileTypes: true });
    } catch {
      continue;
    }
    const direct = join(root, dir, "package.json");
    if (existsSync(direct)) found.push(direct);
    for (const entry of entries) {
      if (found.length >= MAX_MANIFESTS) return found;
      if (!entry.isDirectory() || entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      const candidate = join(root, dir, entry.name, "package.json");
      if (existsSync(candidate)) found.push(candidate);
    }
  }
  return found;
}

function installedVersion(root, manifestPath, name) {
  for (const base of [dirname(manifestPath), root]) {
    const pkg = readJson(join(base, "node_modules", ...name.split("/"), "package.json"));
    if (pkg?.version) return pkg.version;
  }
  return null;
}

function major(version) {
  const match = /(\d+)\./.exec(version ?? "");
  return match ? Number(match[1]) : null;
}

export function profile(root) {
  const js = new Map();
  for (const manifestPath of findPackageJsons(root)) {
    const pkg = readJson(manifestPath);
    if (!pkg) continue;
    const deps = { ...pkg.dependencies, ...pkg.devDependencies, ...pkg.peerDependencies };
    for (const [name, range] of Object.entries(deps)) {
      if (!name.startsWith("@whop/") && !name.startsWith("@whop-apps/")) continue;
      if (js.has(name)) continue;
      js.set(name, { range, installed: installedVersion(root, manifestPath, name), where: relative(root, manifestPath) });
    }
  }

  const python = /(^|[\s"'])whop[-_]sdk\b/im.test(
    ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "Pipfile", "setup.py"].map((f) => readText(join(root, f))).join("\n"),
  );
  const ruby = /['"]whop_sdk['"]/.test(readText(join(root, "Gemfile")));

  const envNames = new Set();
  let envFiles = [];
  try {
    envFiles = readdirSync(root).filter((f) => /^\.env(\..+)?$/.test(f));
  } catch {
    // unreadable root
  }
  for (const file of envFiles) {
    for (const match of readText(join(root, file)).matchAll(/^\s*(?:export\s+)?([A-Z0-9_]*WHOP[A-Z0-9_]*)\s*=/gm)) {
      envNames.add(`${match[1]} (${file})`);
    }
  }

  return { js, python, ruby, envNames: [...envNames] };
}

export function buildContext(info) {
  const { js, python, ruby, envNames } = info;
  if (!js.size && !python && !ruby && !envNames.length) return null;

  const lines = ["This project uses Whop. Notes from the whop-developer plugin:"];
  const packages = [...js.entries()].map(([name, d]) => `${name}${d.installed ? ` ${d.installed}` : ` (${d.range}, not installed)`}`);
  if (python) packages.push("whop-sdk (Python)");
  if (ruby) packages.push("whop_sdk (Ruby)");
  if (packages.length) lines.push(`- Whop packages: ${packages.join(", ")}.`);

  const sdk = js.get("@whop/sdk");
  const sdkVersion = sdk?.installed ?? null;
  if (sdk && major(sdkVersion ?? sdk.range) !== null && major(sdkVersion ?? sdk.range) < 2) {
    lines.push(`- @whop/sdk ${sdkVersion ?? sdk.range} predates 2.x: \`WhopClient\`, \`variants\`, \`accounts\` and \`unwrapWebhook\` don't exist there. Upgrade before following the skills (\`whop-migrate\`).`);
  } else if (sdkVersion && CHECKED_SDK_VERSION && sdkVersion !== CHECKED_SDK_VERSION) {
    lines.push(`- The skills' snippets were type-checked against @whop/sdk ${CHECKED_SDK_VERSION}; this project has ${sdkVersion}. If a name doesn't compile, trust node_modules/@whop/sdk/reference.md.`);
  }

  for (const [name, note] of Object.entries(LEGACY_JS)) {
    if (js.has(name)) lines.push(`- ${name} is ${note}`);
  }

  const publicSecrets = envNames.filter((n) => /^(NEXT_PUBLIC|VITE|EXPO_PUBLIC|REACT_APP|NUXT_PUBLIC|GATSBY|PUBLIC)_\w*(API_KEY|SECRET)\b/.test(n));
  if (publicSecrets.length) {
    lines.push(`- Security: ${publicSecrets.join(", ")} would be bundled into client code. Whop API keys and webhook secrets must stay server-only; tell the user.`);
  }

  lines.push(
    "- Skills: for payments, subscriptions, paywalls, access checks, webhooks, payouts, marketplaces, chat or a Whop app in this project, load the matching `whop-*` skill (or the `whop` skill to pick one) before writing code, even if the user doesn't say \"Whop\".",
    "- The `whop` MCP server acts on the signed-in user's live (production) Whop account and cannot reach sandbox. Use it to look things up (IDs, products, webhooks, payment status) and to read the docs (`docs_search`, then `docs_query`), not to test code. Call `connection_status` first; pass `account_id` (`biz_...`) explicitly, plus `intent` (the user's request) and `intent_id` (one UUID per user message) on every operation tool. Tools that change data run on the first call: before a refund, cancellation, deletion or new credential, tell the user what will happen and get their yes, then call once with a stable `idempotency_key` and reuse it on retries.",
    "- Commands: /whop-developer:connect (MCP sign-in vs the project's API key), /whop-developer:setup (SDK, env and a sandbox check), /whop-developer:test-webhook (signed test events against a local handler), /whop-developer:audit (integration review).",
  );
  return lines.join("\n");
}

async function main() {
  let raw = "";
  for await (const chunk of process.stdin) raw += chunk;
  let input = {};
  try {
    input = JSON.parse(raw || "{}");
  } catch {
    // run with defaults
  }
  const root = resolve(process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd());
  const context = buildContext(profile(root));
  if (!context) return;
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: context } }));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => process.exit(0));
}
