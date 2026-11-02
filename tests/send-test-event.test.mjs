import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { unwrapWebhook } from "@whop/sdk/helpers";

import { buildDelivery, exampleEnvelope, parseArgs } from "../skills/whop-webhooks/scripts/send-test-event.mjs";

const SCRIPT = fileURLToPath(new URL("../skills/whop-webhooks/scripts/send-test-event.mjs", import.meta.url));
// Same shape as the docs' example secret.
const SECRET = "ws_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

const ENVELOPE = {
  account_id: "biz_xxxxxxxxxxxxxx",
  api_version: "v1",
  api_version_date: "2026-10-30",
  id: "msg_xxxxxxxxxxxxxxxxxxxxxxxx",
  timestamp: "2025-01-01T00:00:00.000Z",
  type: "payment.succeeded",
  data: { id: "pay_xxxxxxxxxxxxxx", status: "paid" },
};
const SPEC = { webhooks: { "payment.succeeded": { post: { requestBody: { content: { "application/json": { example: ENVELOPE } } } } } } };

test("a signed delivery verifies with the SDK's unwrapWebhook", () => {
  const delivery = buildDelivery({ envelope: ENVELOPE, secret: SECRET, accountId: "biz_mine" });
  const event = unwrapWebhook(delivery.raw, { headers: delivery.headers, key: SECRET });
  assert.equal(event.type, "payment.succeeded");
  assert.equal(event.account_id, "biz_mine");
  assert.equal(event.id, delivery.headers["webhook-id"]);
  assert.match(event.id, /^msg_[A-Za-z0-9]{24}$/);
});

test("a tampered delivery fails the SDK's verification", () => {
  const delivery = buildDelivery({ envelope: ENVELOPE, secret: SECRET, tamper: true });
  assert.throws(() => unwrapWebhook(delivery.raw, { headers: delivery.headers, key: SECRET }));
});

test("the wrong secret fails verification", () => {
  const delivery = buildDelivery({ envelope: ENVELOPE, secret: SECRET });
  assert.throws(() => unwrapWebhook(delivery.raw, { headers: delivery.headers, key: `${SECRET}x` }));
});

test("exampleEnvelope reads the OpenAPI example and names known types on a miss", () => {
  assert.equal(exampleEnvelope(SPEC, "payment.succeeded").data.id, "pay_xxxxxxxxxxxxxx");
  assert.throws(() => exampleEnvelope(SPEC, "payment.paid"), /Known types: payment\.succeeded/);
});

test("parseArgs validates flags", () => {
  assert.equal(parseArgs(["--url", "http://x", "--repeat", "2"]).repeat, 2);
  assert.throws(() => parseArgs(["--repeat", "0"]), /--repeat/);
  assert.throws(() => parseArgs(["--bogus"]), /Unknown argument/);
  assert.throws(() => parseArgs(["--url"]), /needs a value/);
});

test("every event example in the pinned OpenAPI copy verifies (when present)", async (t) => {
  let spec;
  try {
    spec = JSON.parse(readFileSync(process.env.WHOP_OPENAPI_FILE ?? "", "utf8"));
  } catch {
    t.skip("set WHOP_OPENAPI_FILE to a local openapi.json to run this");
    return;
  }
  const types = Object.keys(spec.webhooks ?? {});
  assert.ok(types.length > 0);
  for (const type of types) {
    const delivery = buildDelivery({ envelope: exampleEnvelope(spec, type), secret: SECRET });
    assert.equal(unwrapWebhook(delivery.raw, { headers: delivery.headers, key: SECRET }).type, type);
  }
});

// A handler written the way whop-webhooks teaches, with a dedupe set.
function startHandler() {
  const handled = [];
  const seen = new Set();
  const server = createServer(async (req, res) => {
    let raw = "";
    for await (const chunk of req) raw += chunk;
    try {
      const event = unwrapWebhook(raw, { headers: req.headers, key: SECRET });
      if (!seen.has(event.id)) {
        seen.add(event.id);
        handled.push(event.type);
      }
      res.writeHead(200).end("OK");
    } catch {
      res.writeHead(401).end("bad signature");
    }
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve({ server, handled, url: `http://127.0.0.1:${server.address().port}/webhooks/whop` })));
}

function runScript(args) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [SCRIPT, ...args], { env: { ...process.env, WHOP_WEBHOOK_SECRET: SECRET } });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (out += d));
    child.on("close", (code) => resolve({ code, out }));
  });
}

test("end to end: the script passes against a correct handler and catches a bad one", async () => {
  const { writeFileSync, mkdtempSync } = await import("node:fs");
  const { join } = await import("node:path");
  const { tmpdir } = await import("node:os");
  const specFile = join(mkdtempSync(join(tmpdir(), "whop-spec-")), "openapi.json");
  writeFileSync(specFile, JSON.stringify(SPEC));

  const { server, handled, url } = await startHandler();
  try {
    const ok = await runScript(["--url", url, "--openapi", specFile, "--repeat", "2"]);
    assert.equal(ok.code, 0, ok.out);
    assert.match(ok.out, /PASS/);
    assert.deepEqual(handled, ["payment.succeeded"], "deduped on webhook-id");

    const tampered = await runScript(["--url", url, "--openapi", specFile, "--tamper"]);
    assert.equal(tampered.code, 0, tampered.out);
    assert.match(tampered.out, /bad signature rejected/);
  } finally {
    server.close();
  }

  const lax = createServer((req, res) => res.writeHead(200).end("OK"));
  await new Promise((r) => lax.listen(0, "127.0.0.1", r));
  try {
    const laxUrl = `http://127.0.0.1:${lax.address().port}/`;
    const result = await runScript(["--url", laxUrl, "--openapi", specFile, "--tamper"]);
    assert.equal(result.code, 1);
    assert.match(result.out, /accepted a bad signature/);
  } finally {
    lax.close();
  }
});
