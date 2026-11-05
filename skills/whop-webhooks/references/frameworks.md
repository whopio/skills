# Webhook handlers by framework

Every handler does the same five things: read the raw body, verify with the SDK helper, skip an event `id` it has already handled (Whop retries with the same `id`), queue the work, return `200` within 5 seconds. `alreadyHandled` / `already_handled` below stands for your own durable check: insert the event `id` into a table with a unique constraint and treat a conflict as "seen". The helper returns the parsed body, not a typed object: a plain object in TypeScript, a `dict` in Python, and a `Hash` with symbol keys in Ruby.

## Next.js (App Router, on Vercel)

```ts
import { waitUntil } from "@vercel/functions";
import { unwrapWebhook } from "@whop/sdk/helpers";
import type { Whop } from "@whop/sdk";
import type { NextRequest } from "next/server";

export async function POST(request: NextRequest): Promise<Response> {
  const payload = await request.text();
  const headers = Object.fromEntries(request.headers);

  const event = unwrapWebhook<{ id: string; type: string; data: Whop.Payment }>(payload, {
    headers,
    key: process.env.WHOP_WEBHOOK_SECRET!,
  });

  // Whop delivers at least once; retries carry the same id.
  if (await alreadyHandled(event.id)) return new Response("OK", { status: 200 });

  if (event.type === "payment.succeeded") {
    waitUntil(handlePaymentSucceeded(event.data));
  }

  return new Response("OK", { status: 200 });
}

async function alreadyHandled(eventId: string): Promise<boolean> {
  // Record eventId in your database (unique constraint); return true if it was already there.
  return false;
}

async function handlePaymentSucceeded(payment: Whop.Payment) {
  console.log("[PAYMENT SUCCEEDED]", payment.id);
}
```

`waitUntil` comes from `@vercel/functions`. Off Vercel, use your platform's equivalent (`ctx.waitUntil` on Cloudflare Workers) or a job queue.

## Python (FastAPI)

```python
import os

from fastapi import BackgroundTasks, FastAPI, Request, Response
from whop_sdk.lib.verify_webhook import unwrap

app = FastAPI()

@app.post("/api/webhooks/whop")
async def whop_webhook(request: Request, background: BackgroundTasks):
    payload = await request.body()

    event = unwrap(payload, headers=dict(request.headers), key=os.environ["WHOP_WEBHOOK_SECRET"])

    # Whop delivers at least once; retries carry the same id.
    if already_handled(event["id"]):
        return Response(status_code=200)

    if event["type"] == "payment.succeeded":
        background.add_task(handle_payment_succeeded, event["data"])

    return Response(status_code=200)


def already_handled(event_id: str) -> bool:
    # Record event_id in your database (unique constraint); return True if it was already there.
    return False


def handle_payment_succeeded(payment):
    print(f"[PAYMENT SUCCEEDED] {payment['id']}")
```

## Ruby on Rails

```ruby
require "whop_sdk"

class Api::WebhooksController < ApplicationController
  skip_before_action :verify_authenticity_token

  def whop
    event = WhopSDK::Helpers::VerifyWebhook.unwrap(
      request.raw_post,
      headers: {
        "webhook-id" => request.headers["webhook-id"],
        "webhook-timestamp" => request.headers["webhook-timestamp"],
        "webhook-signature" => request.headers["webhook-signature"],
      },
      key: ENV.fetch("WHOP_WEBHOOK_SECRET"),
    )

    # Whop delivers at least once; retries carry the same id.
    return head(:ok) if already_handled?(event[:id])

    if event[:type] == "payment.succeeded"
      HandlePaymentSucceededJob.perform_later(event[:data][:id])
    end

    head :ok
  end

  private

  def already_handled?(event_id)
    # Record event_id in your database (unique constraint); return true if it was already there.
    false
  end
end
```

## Other frameworks

Any framework works if it can give you the unparsed request body. Watch for middleware that parses JSON before your route runs (for example Express's global `express.json()`): mount the webhook route with a raw-body parser instead, then pass that string to `unwrapWebhook`. For a language without a Whop SDK, see `verify-without-sdk.md` in this folder.

## Sources

- https://docs.whop.com/developer/guides/webhooks.md
