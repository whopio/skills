# Request conventions

Base URL `https://api.whop.com/api/v1` (sandbox `https://sandbox-api.whop.com/api/v1`). Every request sends `Authorization: Bearer <credential>`. Field names are `snake_case`.

## Idempotency

Every authenticated `POST` on the Current API accepts an `Idempotency-Key` header.

| Your retry | You get |
|---|---|
| Same key, same request | The original response replayed, with `Idempotent-Replayed: true`. Nothing runs twice |
| Same key, different request | `400`, `error.code` `idempotency_key_mismatch` |
| Same key while the first request still runs | `409`, `error.code` `idempotency_request_in_progress`. Retry after it finishes |
| Same key more than 24 hours later | A fresh execution |

- "Same request" means the method, path, query string, body and `Api-Version-Date` all match.
- Error responses are replayed too. A `4xx` was the real outcome; send a new key with the fixed request.
- If the first request ended with an unknown outcome (a server crash mid-request), retries keep getting `409` until the key expires rather than risk a second run.
- Keys are scoped to the caller, up to 255 bytes. A UUID is a good default.
- Ignored on `GET`, `PATCH`, `DELETE` and unauthenticated requests. Those are safe to retry.

SDK: pass `idempotencyKey` in the second (request options) argument of any create call, or once on the client. The SDK doesn't generate keys for you, and it retries `408`, `429` and `5xx` responses twice by default (`maxRetries`), so pass a key on anything that charges, transfers, pays out or creates.

```bash
curl -X POST https://api.whop.com/api/v1/transfers \
  -H "Authorization: Bearer $WHOP_API_KEY" \
  -H "Idempotency-Key: d9105228-4a08-46b1-8b91-42fed586d383" \
  -H "Content-Type: application/json" \
  -d '{"type": "balance", "amount": "10.00", "currency": "usd", "destination_id": "user_XXXXXXXX"}'
```

## Pagination

Lists return `data` and `page_info`. Pass `first` for the page size and `after` with the previous `page_info.end_cursor` for the next page; stop when `page_info.has_next_page` is `false`.

TypeScript: `list()` returns a promise of a page. Await it, then iterate across every page, or walk pages by hand:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

let page = await whop.payments.list({ account_id: "biz_xxxxxxxxxxxxx", first: 50 });
while (true) {
  for (const payment of page.data) console.log(payment.id, payment.status);
  if (!page.hasNextPage()) break;
  page = await page.getNextPage();
}
```

`for await (const item of client.x.list(...))` without the inner `await` doesn't type-check; write `for await (const item of await client.x.list(...))`.

Python iterates every page directly:

```python
for membership in client.memberships.list(product_id="prod_xxxxxxxxxxxxx"):
    print(membership.id)
```

## Errors

Failed requests return an HTTP status and one `error` object. `type` is machine-readable and `message` explains it; some errors add a `code`:

```json
{ "error": { "type": "invalid_parameters", "message": "initial_price must be greater than 0" } }
```

OAuth endpoints use the OAuth-standard `error` and `error_description` instead.

| Status | Meaning | Do |
|---|---|---|
| `400` | Invalid shape or missing field | Check required params, enum values, IDs, nested shape |
| `401` | No valid authentication | Check the credential is present, valid, server-side, same environment |
| `403` | Valid credential, action not allowed | Check key permissions, app permissions, OAuth scopes, account ownership, connected-account context |
| `404` | Resource or route not found | Check the route, API version, and tag prefix |
| `409` | Conflicts with current state | Re-read the resource; retry only if the action still applies |
| `410` | Endpoint retired at this version | Move to the successor named in the changelog |
| `422` | Valid JSON, fails validation | Show the message to the user |
| `429` | Rate limited | Wait the time in `message` |
| `5xx` | Whop couldn't complete it | Retry with backoff, with an idempotency key on `POST` |

The SDK throws a `WhopError` subclass per status (`Whop.BadRequestError`, `Whop.UnauthorizedError`, `Whop.ForbiddenError`, `Whop.NotFoundError`, `Whop.ConflictError`, `Whop.UnprocessableEntityError`, `Whop.TooManyRequestsError`, `Whop.InternalServerError`, ...). Every one has `statusCode`, `body` and `requestId`. Log those when asking for help, with the environment and the IDs involved, never the key.

## Rate limits

`/api/v1` allows 600 requests per minute per API operation and credential. Over it you get `429`:

```json
{ "error": { "type": "rate_limit_exceeded", "message": "Try again in 12 seconds." } }
```

Wait the stated delay, then back off exponentially on idempotent requests. Don't retry validation, authentication or permission errors without changing the request.

## Sources

- https://docs.whop.com/developer/api/idempotency.md
- https://docs.whop.com/api-reference/beta/overview.md
- https://docs.whop.com/developer/troubleshooting.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
