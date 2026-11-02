# Chat authentication and user sync

| Approach | Best for |
|---|---|
| Account-scoped user tokens | Your product has its own users and login. Your server mints a Whop token for whoever is signed in; no Whop sign-in step. |
| OAuth | Users sign in to Whop themselves (sign-in page or iOS webview), or you need their own Whop account. No user sync. |

## Account-scoped user tokens

`POST /api/v1/access_tokens` (`accessTokens.create`) with your API key:

| Field | Notes |
|---|---|
| `account_id` | Your `biz_` ID. The guides' snippets call it `company_id`; the SDK and API use `account_id`. |
| `user_id` | The `user_` ID of the signed-in user. Required together with `account_id` for embedded chat. Your key must be able to reach both. |
| `scoped_actions` | Explicit list. Empty or omitted inherits every permission of the minting key. Must be a subset of the key's permissions. |
| `expires_at` | Defaults to 1 hour from now, at most 3 hours. Mint on demand; don't cache. |

The response is `{ token, expires_at }`.

| Scopes | For |
|---|---|
| `chat:message:create`, `chat:read` | Channels |
| `dms:read`, `dms:message:manage`, `dms:channel:manage` | Direct messages |
| `support_chat:read`, `support_chat:message:create` | Support chats |

The chat elements call your token function whenever they need to authenticate, and again when the token expires.

An account access token (only `account_id`, no `user_id`) acts as the account with no user attached. Chat needs a user, so pass both.

## Sync your users

The `user_id` must be a Whop user. Enroll each of your users as a connected account (the same flow as payouts; see `whop-platforms`):

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const account = await whop.accounts.create({
  email: "user@example.com",
  title: "Jane Doe",
  metadata: { internal_user_id: "user_12345" },
});

const whopUserId = account.owner.id;

await whop.users.update({
  id: whopUserId,
  account_id: "biz_xxxxxxxxxxxxx",
  name: "Jane D.",
  profile_picture: { id: "file_xxxxxxxxxxxxx" },
});
```

- The chat quickstart reads the user ID as `owner_user.id`; in the current SDK the `Account` field is `owner`.
- `users.update` with `account_id` sets a name and avatar shown only in your account's context; without it, it edits the user's global profile. It needs `user:profile:update` (an owner-level account key, or a key with that scope).
- Upload avatars with `files.create`, `PUT` the bytes, then pass the file ID.
- Call it whenever the profile changes on your side.

## OAuth

1. Register the app (dashboard → Developer → app → **OAuth**, or `apps.create({ name, redirect_uris })`). The SDK's `App` has no `client_secret`; copy it from the dashboard.
2. Add redirect URIs: your web callback (for example `https://yourapp.com/oauth/callback`), or `com.yourapp.bundle://oauth/callback` on iOS.
3. Request scopes `openid`, `profile`, `email` plus the chat scope groups above.
4. Web: run the OAuth 2.1 + PKCE flow from the general guide (`https://docs.whop.com/developer/guides/oauth.md`) on your server, and have your token endpoint return the user's current access token (refresh it when it expires; refresh tokens rotate).
5. iOS: `await WhopSDK.configureWithOAuth(appId: "app_...", scopes: [...])` at launch. It shows the sign-in webview, stores and refreshes tokens, and starts sign-in when a chat view needs it. Optional `redirectUri:` must match the dashboard. Also `WhopSDK.signIn()`, `WhopSDK.signOut()`, `.whopAuthState($isAuthenticated)`, and `WhopSDK.preSignIn(accessToken:refreshToken:)` to reuse tokens you already have.

## Security

- Keep `WHOP_API_KEY` on the server; only the minted token goes to the client.
- Derive `user_id` from your session, never from client input.
- Request only the scope groups you render.
- Mint tokens with an account API key: a federated (OIDC) access token can't create access tokens.

## Sources

- https://docs.whop.com/developer/guides/chat/authentication.md
- https://docs.whop.com/developer/guides/chat/sync-users.md
- https://docs.whop.com/developer/guides/chat/oauth.md
- https://docs.whop.com/developer/guides/auth-scoping.md
- https://docs.whop.com/developer/guides/oauth.md
- https://docs.whop.com/developer/guides/oidc-federation.md
