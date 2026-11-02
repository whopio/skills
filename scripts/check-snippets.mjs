#!/usr/bin/env node
// Type-checks every TypeScript snippet in skills/ that only imports @whop/sdk, jose
// (and Node built-ins) against the SDK version pinned in package.json.

import { execFileSync } from "node:child_process";
import { mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { builtinModules } from "node:module";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(root, ".snippets");
const checkedImports = /^(@whop\/sdk(\/helpers)?|jose)$/;
const builtins = new Set(builtinModules.flatMap((m) => [m, `node:${m}`]));

function markdownFiles(dir) {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return markdownFiles(path);
    return path.endsWith(".md") ? [path] : [];
  });
}

function snippets(file) {
  const text = readFileSync(file, "utf8");
  const fence = /^```(ts|typescript)\b[^\n]*\n([\s\S]*?)^```/gm;
  const found = [];
  for (let match; (match = fence.exec(text)); ) {
    const line = text.slice(0, match.index).split("\n").length;
    found.push({ code: match[2], line });
  }
  return found;
}

function imports(code) {
  return [...code.matchAll(/^\s*import\s[^;]*?from\s+["']([^"']+)["']/gm)].map((m) => m[1]);
}

rmSync(outDir, { recursive: true, force: true });
mkdirSync(outDir, { recursive: true });

const checked = [];
let skipped = 0;
for (const file of markdownFiles(join(root, "skills"))) {
  for (const { code, line } of snippets(file)) {
    const specifiers = imports(code);
    const usesSdk = specifiers.some((s) => checkedImports.test(s));
    const onlyAllowed = specifiers.every((s) => checkedImports.test(s) || builtins.has(s));
    if (!usesSdk || !onlyAllowed) {
      skipped++;
      continue;
    }
    const name = `${relative(join(root, "skills"), file).replace(/[/.]/g, "_")}_L${line}.ts`;
    const body = /^\s*export\s/m.test(code) ? code : `${code}\nexport {};\n`;
    writeFileSync(join(outDir, name), body);
    checked.push({ name, source: `${relative(root, file)}:${line}` });
  }
}

if (checked.length === 0) {
  console.error("No snippets found to check.");
  process.exit(1);
}

writeFileSync(
  join(outDir, "tsconfig.json"),
  JSON.stringify({
    compilerOptions: {
      target: "es2022",
      lib: ["es2022", "dom", "dom.iterable"],
      module: "esnext",
      moduleResolution: "bundler",
      strict: true,
      noEmit: true,
      skipLibCheck: true,
      types: ["node"],
      typeRoots: [join(root, "node_modules/@types")],
    },
    include: ["*.ts"],
  }),
);

const sourceFor = Object.fromEntries(checked.map((c) => [c.name, c.source]));
try {
  execFileSync(join(root, "node_modules/.bin/tsc"), ["-p", outDir], { stdio: "pipe" });
  console.log(`OK: ${checked.length} snippets type-check against @whop/sdk (${skipped} framework snippets skipped)`);
} catch (failure) {
  const output = `${failure.stdout ?? ""}${failure.stderr ?? ""}`;
  for (const line of output.split("\n").filter(Boolean)) {
    const match = line.match(/^(?:.*\/)?([^/(]+\.ts)\((\d+),(\d+)\):\s*(.*)$/);
    if (match && sourceFor[match[1]]) {
      const [file, snippetLine] = sourceFor[match[1]].split(/:(?=\d+$)/);
      console.error(`${file}:${Number(snippetLine) + Number(match[2])}  ${match[4]}`);
    } else {
      console.error(line);
    }
  }
  process.exit(1);
}
