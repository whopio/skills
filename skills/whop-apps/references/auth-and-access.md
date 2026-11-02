# Authenticating the user inside a Whop app

Whop renders your app in an iframe on `whop.com` and passes a short-lived JWT in the `x-whop-user-token` header on every same-origin request. You verify it on your server to get the user ID, then call `users.checkAccess`. You never mint this token; Whop sends it.

## Verify the token by language

| Language | Helper | Notes |
|---|---|---|
| TypeScript | `jwtVerify` from `jose` with Whop's JWKS (the `verifyWhopUser` helper in `SKILL.md`) | `@whop/sdk` has no helper and `@whop/api` is deprecated. Issuer `urn:whopcom:exp-proxy`, algorithm `ES256`, audience your `app_` ID, user ID in `sub`. Keys are at `https://api.whop.com/.well-known/jwks.json`; `createRemoteJWKSet` caches them and refetches when Whop rotates. Throws on an invalid token. |
| Python | `from whop_sdk.lib.verify_user_token import verify_user_token` | Synchronous. `app_id` is required and checked against the token's audience. Install `pyjwt[crypto]` alongside `whop-sdk`. `try_verify_user_token` returns `None` instead of raising. |
| Ruby | `WhopSDK::Helpers::VerifyUserToken.verify_user_token!` | A module function, not a method on `Whop_sdk::Client`. Pass the token string or a plain Hash, not an `ActionDispatch` headers object. `app_id:` is optional and checks the audience. No non-raising variant: rescue `StandardError`. |

```python
from fastapi import FastAPI, Request
from whop_sdk.lib.verify_user_token import verify_user_token

app = FastAPI()

@app.get("/my-route")
async def my_route(request: Request):
    result = verify_user_token(request.headers, app_id="app_xxxxxxxxxxxxx")
    user_id = result.user_id
```

```ruby
class MyController < ApplicationController
  def my_action
    auth_result = WhopSDK::Helpers::VerifyUserToken.verify_user_token!(
      request.headers["x-whop-user-token"],
      app_id: "app_xxxxxxxxxxxxx",
    )
    user_id = auth_result.user_id
  end
end
```

Express: `const userId = await verifyWhopUser(req.get("x-whop-user-token"));`. Pass the header value, not `req.headers`.

This matches `whop-sdk`'s Python helper, which reads the same JWKS and checks the same issuer and audience.

## Same-origin only

The token is attached only to requests to your iframe's `window.location.origin`: relative navigation (`<a href="/sub_page">`) and fetches without a domain (`fetch("/api/quizzes")`). These resolve to the app's base URL.

If the frontend is on `example.com` and the API on `api.example.com`, reverse-proxy `example.com/api` to the API so requests carry the header: a Cloudflare origin rule, a Next.js `rewrites` entry in `next.config.mjs`, or the rewrite primitive in nginx or Caddy. Browsers' cross-origin cookie policies make this necessary.

Locally, run the development proxy (`@whop-apps/dev-proxy`); it injects the same header on `localhost`. Options: `--proxyPort` (default 3000), `--upstreamPort`, `--command`, `--npmCommand`, `--standalone`.

## Check access

`users.checkAccess({ id, resource_id })` (`GET /api/v1/users/{id}/access/{resource_id}`) returns `{ has_access, access_level }`.

| `resource_id` prefix | Checks access to |
|---|---|
| `exp_` | Experience: a membership to any product connected to it |
| `prod_` | Product: a membership to that product |
| `biz_` | Account: a membership to any product on it |

| `access_level` | Meaning |
|---|---|
| `customer` | Valid membership |
| `admin` | Team member of the account, any role including moderator |
| `no_access` | `has_access` is `false` |

Experience views gate on `has_access` using the `experienceId` path parameter. Dashboard views gate on `access_level === "admin"` using the `companyId` path parameter. In API routes return `403`; in pages render an access-denied state or redirect.

## Which credential

| Credential | Use it for |
|---|---|
| App API key | Your app server acting on accounts that installed the app. Server only. |
| iframe user token | Knowing who is viewing the app. Sent by Whop, verified by you. Don't forward it to unrelated clients. |
| OAuth token | A user who signed in with Whop and granted scopes; bounded by what that user can do. See `oauth.md` in this folder. |
| Injected key (Whop-hosted apps) | Server-side `fetch` to `WHOP_API_ORIGIN` is signed with the app's key automatically. It acts as your own business, can't move money, and never identifies the visitor. |

Never put an Account or App API key in browser, mobile, or iframe code.

## Sources

- https://docs.whop.com/developer/guides/authentication.md
- https://docs.whop.com/developer/guides/dev-proxy.md
- https://docs.whop.com/developer/guides/auth-scoping.md
- https://docs.whop.com/developer/guides/app-views.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
- https://docs.whop.com/developer/websites/hosting.md
- https://docs.whop.com/developer/troubleshooting.md
- https://api.whop.com/.well-known/jwks.json (the signing keys; `whop-sdk` Python `whop_sdk/lib/verify_user_token.py` reads the same set)
