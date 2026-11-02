# Sign in with Whop (OAuth 2.1 + PKCE)

Use OAuth when users should sign in with their Whop account and grant your app access to act for them. Inside the Whop iframe you don't need it: the `x-whop-user-token` already identifies the viewer. On a Whop-hosted site, the hosting docs point to OAuth for visitor identity, because the injected key acts as your business, not the visitor.

Endpoints live under `https://api.whop.com/oauth/`.

## 1. Register the app

- Dashboard: Developer → your app → **OAuth**. Add every redirect URI (exact match), copy the `client_id` (`app_...`) and `client_secret`, and pick only the scopes you need under **View available scopes**.
- API: `apps.create({ name, redirect_uris })`; update later with `apps.update`. The returned `App` has no `client_secret` field in the current `@whop/sdk`, so copy the secret from the dashboard.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const app = await whop.apps.create({
  name: "My App",
  redirect_uris: ["https://myapp.com/api/auth/callback/whop"],
});

console.log(app.id);
```

## 2. Send the user to authorize

Generate a random `code_verifier`, `state` and `nonce`, store them for the callback (the guide uses `sessionStorage`), and redirect to `https://api.whop.com/oauth/authorize` with:

| Param | Value |
|---|---|
| `response_type` | `code` |
| `client_id` | `app_...` |
| `redirect_uri` | A registered URI |
| `scope` | `openid profile email`, plus any custom scopes |
| `state`, `nonce` | Your random values |
| `code_challenge` | base64url of SHA-256 of the verifier |
| `code_challenge_method` | `S256` |
| `company_id` | Optional `biz_` ID: tokens are scoped to what this user controls on that account |

The guide's helper builds these in the browser with `crypto.getRandomValues` and `crypto.subtle.digest`. A user who already approved these scopes is redirected straight back.

## 3. Exchange the code

On the callback, reject if `state` doesn't match, then:

```ts
async function exchangeCode(code: string, codeVerifier: string) {
  const res = await fetch("https://api.whop.com/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      code,
      redirect_uri: "https://myapp.com/api/auth/callback/whop",
      client_id: "app_xxxxxxxxxxxxx",
      code_verifier: codeVerifier,
    }),
  });
  if (!res.ok) throw new Error(`Token exchange failed: ${res.status}`);
  return res.json() as Promise<{ access_token: string; refresh_token: string; id_token?: string; expires_in: number }>;
}
```

`id_token` is present only with the `openid` scope. Use the access token as the SDK token: `new WhopClient({ token: accessToken })`.

## 4. Refresh, userinfo, revoke

- Access tokens expire after 1 hour. Refresh with `grant_type: "refresh_token"`, `refresh_token`, `client_id` (and the same `company_id` if you sent one). Refresh tokens rotate on every use: store the new pair. `401` or `invalid_grant` means sign in again.
- `GET https://api.whop.com/oauth/userinfo` with `Authorization: Bearer <access_token>` returns `sub` (the `user_` ID); `profile` adds `name`, `preferred_username`, `picture`; `email` adds `email`, `email_verified`.
- On logout, `POST https://api.whop.com/oauth/revoke` with `{ token: refresh_token, client_id }`. Access tokens can't be revoked server-side.

Error codes: `invalid_request`, `invalid_grant`, `invalid_client`, `insufficient_scope`, `rate_limit_exceeded` (honor `Retry-After`).

## Sources

- https://docs.whop.com/developer/guides/oauth.md
- https://docs.whop.com/developer/guides/auth-scoping.md
- https://docs.whop.com/developer/websites/hosting.md
