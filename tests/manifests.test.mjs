// The root plugin.json and mcp.json must satisfy the official Agent Plugins
// 1.0 schemas: Copilot CLI and other conformant hosts disable a plugin's MCP
// servers when mcp.json doesn't. The schemas are fetched from agent-plugins.org;
// set AGENT_PLUGINS_SCHEMA_DIR to a folder holding plugin.schema.json and
// mcp.schema.json to run offline.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const readJson = (path) => JSON.parse(readFileSync(join(ROOT, path), "utf8"));

async function loadSchema(name) {
  const dir = process.env.AGENT_PLUGINS_SCHEMA_DIR;
  if (dir) return JSON.parse(readFileSync(join(dir, name), "utf8"));
  const res = await fetch(`https://agent-plugins.org/schemas/1.0.0/${name}`);
  assert.equal(res.status, 200, `fetching ${name}`);
  return res.json();
}

// Just the JSON Schema keywords the Agent Plugins 1.0 schemas use.
export function validate(schema, value, root = schema, path = "$") {
  if (schema.$ref) {
    const target = schema.$ref.replace(/^#\//, "").split("/").reduce((node, key) => node[key], root);
    return validate(target, value, root, path);
  }
  const errors = [];
  const isObject = value !== null && typeof value === "object" && !Array.isArray(value);
  if ("const" in schema && value !== schema.const) errors.push(`${path} must be ${JSON.stringify(schema.const)}`);
  if (schema.type === "object" && !isObject) return [`${path} must be an object`];
  if (schema.type === "string" && typeof value !== "string") return [`${path} must be a string`];
  if (schema.type === "array" && !Array.isArray(value)) return [`${path} must be an array`];
  if (typeof value === "string") {
    if (schema.minLength !== undefined && value.length < schema.minLength) errors.push(`${path} is too short`);
    if (schema.maxLength !== undefined && value.length > schema.maxLength) errors.push(`${path} is too long`);
    if (schema.pattern && !new RegExp(schema.pattern, "u").test(value)) errors.push(`${path} doesn't match ${schema.pattern}`);
  }
  if (Array.isArray(value) && schema.items) value.forEach((item, i) => errors.push(...validate(schema.items, item, root, `${path}[${i}]`)));
  if (isObject) {
    for (const key of schema.required ?? []) if (!(key in value)) errors.push(`${path}.${key} is required`);
    for (const [key, child] of Object.entries(value)) {
      if (schema.propertyNames?.not?.enum?.includes(key)) errors.push(`${path}.${key} is not an allowed name`);
      if (schema.properties?.[key]) errors.push(...validate(schema.properties[key], child, root, `${path}.${key}`));
      else if (schema.additionalProperties === false) errors.push(`${path}.${key} is not allowed`);
      else if (typeof schema.additionalProperties === "object") errors.push(...validate(schema.additionalProperties, child, root, `${path}.${key}`));
    }
  }
  if (schema.oneOf) {
    const matches = schema.oneOf.filter((option) => validate(option, value, root, path).length === 0).length;
    if (matches !== 1) errors.push(`${path} must match exactly one variant (matched ${matches})`);
  }
  return errors;
}

test("plugin.json satisfies the Agent Plugins 1.0 plugin schema", async () => {
  assert.deepEqual(validate(await loadSchema("plugin.schema.json"), readJson("plugin.json")), []);
});

test("mcp.json satisfies the Agent Plugins 1.0 MCP schema", async () => {
  assert.deepEqual(validate(await loadSchema("mcp.schema.json"), readJson("mcp.json")), []);
});

test("the validator rejects what the spec rejects", async () => {
  const mcp = await loadSchema("mcp.schema.json");
  const good = readJson("mcp.json");
  // The shape we used to ship: Claude's "http" type and no $schema.
  assert.notDeepEqual(validate(mcp, { mcpServers: { whop: { type: "http", url: "https://x" } } }), []);
  assert.notDeepEqual(validate(mcp, { ...good, extra: true }), []);
  assert.notDeepEqual(validate(mcp, { ...good, mcpServers: { whop: { ...good.mcpServers.whop, env: {} } } }), []);
  const plugin = await loadSchema("plugin.schema.json");
  assert.notDeepEqual(validate(plugin, { ...readJson("plugin.json"), skills: "./skills/" }), []);
  assert.notDeepEqual(validate(plugin, { ...readJson("plugin.json"), name: "Whop--Dev" }), []);
});

test("every host's MCP entry points at the same server", () => {
  const url = readJson(".mcp.json").mcpServers.whop.url;
  assert.equal(readJson("mcp.json").mcpServers.whop.url, url);
  assert.equal(readJson("gemini-extension.json").mcpServers.whop.httpUrl, url);
  assert.equal(readJson(".kimi-plugin/plugin.json").mcpServers.whop.url, url);
  assert.equal(readJson(".cursor-plugin/plugin.json").mcpServers, "./.mcp.json");
  assert.equal(readJson(".codex-plugin/plugin.json").mcpServers, "./.mcp.json");
});
