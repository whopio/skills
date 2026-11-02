# Webhook handlers by framework

Every handler does the same four things: read the raw body, verify with the SDK helper, queue the work, return `200` within 5 seconds. The helper returns the parsed body, not a typed object: a plain object in TypeScript, a `dict` in Python, and a `Hash` with symbol keys in Ruby.

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

  if (event.type === "payment.succeeded") {
    waitUntil(handlePaymentSucceeded(event.data));
  }

  return new Response("OK", { status: 200 });
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

    if event["type"] == "payment.succeeded":
        background.add_task(handle_payment_succeeded, event["data"])

    return Response(status_code=200)


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

    if event[:type] == "payment.succeeded"
      HandlePaymentSucceededJob.perform_later(event[:data][:id])
    end

    head :ok
  end
end
```

## Other frameworks

Any framework works if it can give you the unparsed request body. Watch for middleware that parses JSON before your route runs (for example Express's global `express.json()`): mount the webhook route with a raw-body parser instead, then pass that string to `unwrapWebhook`. For a language without a Whop SDK, see `verify-without-sdk.md` in this folder.

## Sources

- https://docs.whop.com/developer/guides/webhooks.md
