#!/usr/bin/env node
// Send a signed Whop webhook event to a handler you are developing, without a
// tunnel or a Whop account. The payload is the example Whop publishes for that
// event in its OpenAPI spec, signed with your webhook secret the same way Whop
// signs deliveries (Standard Webhooks, HMAC-SHA256 over the secret's literal
// bytes). Node 18+, no dependencies.
//
//   node send-test-event.mjs --url http://localhost:3000/api/webhooks/whop
//   node send-test-event.mjs --url ... --type membership.updated --repeat 2
//   node send-test-event.mjs --url ... --tamper      # must be rejected
//   node send-test-event.mjs --list-types

import { createHmac, randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const OPENAPI_URL = "https://api.whop.com/api/v1/openapi.json";
const DEADLINE_MS = 5000;

const HELP = `Usage: send-test-event.mjs --url <handler URL> [options]

  --url <url>               Your webhook handler (http or https)
  --secret <ws_...>         Signing secret (default: $WHOP_WEBHOOK_SECRET)
  --type <event>            Event type (default: payment.succeeded)
  --data <file.json>        Use this envelope (or just its "data") instead of Whop's example
  --account-id <biz_...>    Set the envelope's account_id
  --repeat <n>              Send the same delivery n times (same webhook-id) to test dedupe
  --tamper                  Send a wrong signature; the handler must reject it
  --openapi <url|file>      Where to read event examples (default: ${OPENAPI_URL})
  --list-types              Print every event type and exit`;

export function parseArgs(argv) {
  const opts = { type: "payment.succeeded", repeat: 1, tamper: false, listTypes: false, openapi: OPENAPI_URL };
  const valueFlags = { "--url": "url", "--secret": "secret", "--type": "type", "--data": "data", "--account-id": "accountId", "--repeat": "repeat", "--openapi": "openapi" };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--tamper") opts.tamper = true;
    else if (arg === "--list-types") opts.listTypes = true;
    else if (arg === "-h" || arg === "--help") opts.help = true;
    else if (valueFlags[arg]) {
      if (i + 1 >= argv.length) throw new Error(`${arg} needs a value`);
      opts[valueFlags[arg]] = argv[++i];
    } else throw new Error(`Unknown argument: ${arg}`);
  }
  opts.repeat = Number(opts.repeat);
  if (!Number.isInteger(opts.repeat) || opts.repeat < 1 || opts.repeat > 10) throw new Error("--repeat must be 1-10");
  return opts;
}

/** Standard Webhooks signature, keyed with the secret's literal UTF-8 bytes (prefix included). */
export function sign(secret, id, timestamp, body) {
  return createHmac("sha256", Buffer.from(secret, "utf8")).update(`${id}.${timestamp}.${body}`).digest("base64");
}

export function newMessageId() {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  return `msg_${[...randomBytes(24)].map((b) => alphabet[b % alphabet.length]).join("")}`;
}

export function exampleEnvelope(openapi, type) {
  const op = openapi?.webhooks?.[type]?.post;
  const example = op?.requestBody?.content?.["application/json"]?.example;
  if (!example) {
    const known = Object.keys(openapi?.webhooks ?? {});
    throw new Error(`No example for "${type}" in the OpenAPI spec. Known types: ${known.join(", ") || "(none)"}`);
  }
  return structuredClone(example);
}

/** Build the delivery: fresh id and timestamp, and the exact body bytes that get signed. */
export function buildDelivery({ envelope, secret, accountId, now = new Date(), id = newMessageId(), tamper = false }) {
  const body = { ...envelope, id, timestamp: now.toISOString() };
  if (accountId) body.account_id = accountId;
  const raw = JSON.stringify(body);
  const unix = String(Math.floor(now.getTime() / 1000));
  let signature = sign(secret, id, unix, raw);
  if (tamper) signature = sign(`${secret}-wrong`, id, unix, raw);
  return {
    raw,
    headers: {
      "content-type": "application/json",
      "webhook-id": id,
      "webhook-timestamp": unix,
      "webhook-signature": `v1,${signature}`,
    },
  };
}

async function loadOpenapi(source) {
  if (/^https?:\/\//.test(source)) {
    const res = await fetch(source);
    if (!res.ok) throw new Error(`Fetching ${source} returned ${res.status}. Pass --data <file> to send your own payload.`);
    return res.json();
  }
  return JSON.parse(readFileSync(source, "utf8"));
}

async function send(url, delivery) {
  const started = Date.now();
  const res = await fetch(url, { method: "POST", headers: delivery.headers, body: delivery.raw, redirect: "manual" });
  const text = await res.text();
  return { status: res.status, ms: Date.now() - started, body: text.slice(0, 300) };
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) return console.log(HELP);

  if (opts.listTypes) {
    const openapi = await loadOpenapi(opts.openapi);
    return console.log(Object.keys(openapi.webhooks ?? {}).join("\n"));
  }

  if (!opts.url || !/^https?:\/\//.test(opts.url)) throw new Error(`--url must be an http(s) URL.\n\n${HELP}`);
  const secret = opts.secret ?? process.env.WHOP_WEBHOOK_SECRET;
  if (!secret) throw new Error("No signing secret: pass --secret or set WHOP_WEBHOOK_SECRET (the same value your handler reads).");

  let envelope;
  if (opts.data) {
    const supplied = JSON.parse(readFileSync(opts.data, "utf8"));
    envelope = supplied.type && supplied.data ? supplied : { ...exampleEnvelope(await loadOpenapi(opts.openapi), opts.type), data: supplied };
  } else {
    envelope = exampleEnvelope(await loadOpenapi(opts.openapi), opts.type);
  }

  const delivery = buildDelivery({ envelope, secret, accountId: opts.accountId, tamper: opts.tamper });
  console.log(`${opts.tamper ? "Tampered" : "Signed"} ${envelope.type} delivery ${delivery.headers["webhook-id"]} -> ${opts.url}`);

  let ok = true;
  for (let attempt = 1; attempt <= opts.repeat; attempt++) {
    const result = await send(opts.url, delivery);
    const accepted = result.status >= 200 && result.status < 300;
    console.log(`  attempt ${attempt}: HTTP ${result.status} in ${result.ms} ms${result.body ? ` - ${result.body}` : ""}`);
    if (opts.tamper) {
      if (accepted) {
        ok = false;
        console.log("  FAIL: the handler accepted a bad signature. It must verify with unwrapWebhook before reading the body.");
      }
    } else {
      if (!accepted) {
        ok = false;
        console.log("  FAIL: Whop treats any non-2xx (including redirects) as a failed delivery and retries.");
      }
      if (result.ms > DEADLINE_MS) {
        ok = false;
        console.log("  FAIL: slower than 5 seconds; Whop counts that as a failure. Return 2xx first, do the work in the background.");
      }
    }
  }
  if (!opts.tamper && opts.repeat > 1) {
    console.log("Check your logs: the handler should have done the work once and skipped the repeats (same webhook-id).");
  }
  if (ok) console.log(opts.tamper ? "PASS: bad signature rejected." : "PASS");
  process.exitCode = ok ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
