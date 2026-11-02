# Whop credentials

Whop has five credential types. Pick by whose data you reach and where the code runs, then scope it down before production.

## API keys

- **Account API key.** Authenticates your server as one account (`biz_`) and its connected accounts. Create it in the dashboard's Developer page under **Account API Keys** → **Create**. Name it for its use (`Local development`, `Production payments`). For a first call use the Admin role or the read permissions listed on [Retrieve Account](https://docs.whop.com/api-reference/beta/accounts/retrieve-account.md); for production switch to a custom permission set covering only the endpoints you call.
- **App API key.** Authenticates your app across every account that installed it. In the dashboard open **Apps** → **Create app**; the key is the hidden value after `WHOP_API_KEY` under **Environment variables**. Calls fail for accounts that haven't installed or authorized the app. App setup is `whop-apps`.
- Both are secrets. Server only. Send as `Authorization: Bearer <key>`.
- Sandbox keys come from `sandbox.whop.com/dashboard/developer` and only work against `https://sandbox-api.whop.com/api/v1` (SDK: `WhopEnvironment.Sandbox`).

## Minted tokens (`POST /api/v1/access_tokens`)

Your server mints these with an API key and hands them to a client, so the client never holds the key.

| Token | Pass | Acts as |
|---|---|---|
| Account-scoped user token | `account_id` (`biz_`) and `user_id` (`user_`) | That user inside that account |
| Account access token | `account_id` only | The account, no user attached. Endpoints that act as a user (notifications, preferences) reject it |

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const accessToken = await whop.accessTokens.create({
  account_id: "biz_xxxxxxxxxxxxx",
  scoped_actions: ["company:balance:read"],
});

console.log(accessToken.token, accessToken.expires_at);
```

- The docs' curl example sends `company_id`; SDK 2.7.0 and the OpenAPI spec name it `account_id`. Use the name your installed SDK's types accept.
- Default lifetime one hour; set `expires_at` for up to three hours. Mint on demand.
- `scoped_actions` must be a subset of the minting key's own permissions. **Empty or omitted inherits everything the key can do**, so a token in a browser would carry the key's full reach. Always pass a list.
- Actions documented across Whop's guides (not a complete list; the key's permissions are the real bound):

| Action | Grants |
|---|---|
| `chat:read` | Read chat channels and messages |
| `chat:message:create` | Send chat messages |
| `dms:read` | Read direct messages |
| `dms:message:manage` | Send and manage direct messages |
| `dms:channel:manage` | Create and manage DM channels |
| `support_chat:read` | Read support chats |
| `support_chat:message:create` | Send support chat messages |
| `company:balance:read` | Read an account's balance |

## iframe user tokens

When your app renders inside Whop, every same-origin request carries a short-lived JWT in `x-whop-user-token`. You never mint it; you verify it and get the user ID, then check access with `users.checkAccess({ id, resource_id })`.

- TypeScript: `@whop/sdk` has no helper. Verify with `jose`: `jwtVerify(token, createRemoteJWKSet(new URL("https://api.whop.com/.well-known/jwks.json")), { issuer: "urn:whopcom:exp-proxy", audience: "app_...", algorithms: ["ES256"] })`; the user ID is `payload.sub`. Always pass `audience`. Full helper in `whop-apps`.
- Python: `whop_sdk.lib.verify_user_token.verify_user_token(headers, app_id="app_...")` (needs `pip install "pyjwt[crypto]"`); `try_verify_user_token` returns `None` instead of raising.
- Ruby: `WhopSDK::Helpers::VerifyUserToken.verify_user_token!(token, app_id: "app_...")`, a module function, not a client method.
- The header only reaches requests to your iframe's own origin. If your API is on another domain, reverse-proxy it under the app's origin.

Full flow: `whop-apps`.

## OAuth tokens

A user signs in to Whop and approves your app for a set of scopes. The token's reach is what that user can do, not what your app can do. Use it for "Sign in with Whop" and acting on a user's own account. A permission is what a key can do; a scope is what a user let you do. Flow (OAuth 2.1 with PKCE): `whop-apps` and [the OAuth guide](https://docs.whop.com/developer/guides/oauth.md).

## Checking what a credential can do

`permissions.list` answers for whatever authenticated the request:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const { data } = await whop.permissions.list({
  resource_id: "biz_xxxxxxxxxxxxx",
  actions: "payment:basic:read,plan:basic:read",
});

for (const permission of data) console.log(permission.action, permission.granted);
```

A resource the credential can't see reports every action as not granted rather than erroring.

## Scoping checklist

- Explicit `scoped_actions` on every minted token.
- Custom permission sets on API keys once you know the endpoints, instead of Admin.
- API keys server-side only; only minted user tokens belong in a client.
- Short-lived tokens minted on demand.
- Separate credentials per environment, checked before anything moves money.

## Sources

- https://docs.whop.com/developer/guides/auth-scoping.md
- https://docs.whop.com/developer/quickstart.md
- https://docs.whop.com/developer/concepts.md
- https://docs.whop.com/developer/guides/authentication.md
- https://docs.whop.com/developer/troubleshooting.md
- https://docs.whop.com/developer/guides/sandbox.md
- https://docs.whop.com/api-reference/beta/permissions/permission.md
