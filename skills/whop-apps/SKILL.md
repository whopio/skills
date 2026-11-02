---
name: whop-apps
description: >-
  Build apps that run inside Whop and install from the Whop App Store:
  scaffold and deploy with the whop CLI, configure experience and dashboard
  views, verify the x-whop-user-token and check access with users.checkAccess,
  request permissions, track installs with app_installation webhooks, run cron
  jobs, send push notifications, upload files, Sign in with Whop, iframe SDK,
  Frosted UI, React Native. Use when: "build a Whop app", "whop apps init",
  "who is the user in my Whop app", "check access to this experience",
  "app permissions", "app installed webhook", "push notification to
  members", "x-whop-user-token is missing", "run my app on a schedule".
  Chain with: whop-api for client setup, whop-webhooks for deliveries,
  whop-checkout for in-app purchases, whop-communities for chat, forums and
  courses. NOT for: embedding chat in your own site (use whop-communities),
  checkout links (use whop-checkout), connected accounts (use
  whop-platforms), moving off @whop/api (use whop-migrate).
license: Apache-2.0
metadata:
  author: whop
  version: "0.3.0"
---

# Whop Apps

A Whop app installs into a business's Whop and renders inside an iframe on `whop.com`: members use it as an experience in the sidebar, the team uses it as a dashboard view. Your server learns who is looking from a signed token Whop attaches to every request, then checks what that user may see.

## Before you start

1. Fetch `https://docs.whop.com/developer/apps/overview.md`, `https://docs.whop.com/developer/guides/authentication.md` and the changelog at `https://docs.whop.com/developer/api/versioning.md`. If they disagree with this skill, follow the docs.
2. Get the **App API key**: dashboard → **Apps** → your app → the hidden `WHOP_API_KEY` under **Environment variables**. It reaches every account that installed the app. Set up the client with `whop-api`.
3. Decide where the app runs. `whop apps init` scaffolds an app hosted by Whop (`*.whop.site`); otherwise you host it and set its URL in the app's **Hosting** section.
4. The `whop` CLI has no sandbox: every command runs in production.

## Rules

1. **Never trust a user ID from the client.** Whop sends a short-lived JWT in the `x-whop-user-token` header. Verify it on every request on your server and take the user ID from it.
2. **TypeScript: verify the token with `jose`, and always check your app ID.** `@whop/sdk` has no token helper and `@whop/api` is deprecated on npm. The token is an ES256 JWT: issuer `urn:whopcom:exp-proxy`, audience your `app_` ID, subject the user ID, signed by a key in `https://api.whop.com/.well-known/jwks.json`. Without the audience check, a token Whop issued for any other app passes. Python: `whop_sdk.lib.verify_user_token` (needs `pyjwt[crypto]`, `app_id` required). Ruby: `WhopSDK::Helpers::VerifyUserToken.verify_user_token!` with `app_id:`.
3. **The token only rides same-origin requests.** Relative links and `fetch("/api/...")` carry it. An API on another domain doesn't see it; reverse-proxy it under your app's origin.
4. **Gate experience views on `has_access`, dashboard views on `access_level === "admin"`.** `users.checkAccess` takes `id` (the verified user) and `resource_id` (`exp_`, `biz_` or `prod_`). `admin` means any team member, including moderators.
5. **Every API call needs a granted permission.** Declare it in the app's **Permissions** tab with a justification; creators approve at install. A permission you add later fails on every existing install until that creator re-approves, so handle the error. Re-approve on your own test account in **Authorized apps** too.
6. **`apps.updatePermissions` replaces the whole list.** Permissions you leave out are removed.
7. **Install events only reach the app's own webhook.** Create it with `resource_id` set to your `app_` ID. An account's webhooks never receive `app_installation.*`, even for apps installed on it.
8. **Notifications need exactly one of `experience_id` or `account_id`.** `user_ids` narrows the audience to users inside that experience or team. The app needs `notification:create`, and the experience must belong to your app (or the account must have it installed).
9. **Keep API keys on the server.** iframe, browser and React Native code call your server; your server calls Whop.
10. **Don't use `@whop/api`.** Its GraphQL API stopped working on October 26, 2026, and the package is deprecated. `checkIfUserHasAccessToExperience` is now `users.checkAccess`; `sendPushNotification` is `notifications.create`.

## Pick a path

| Goal | Do this |
|---|---|
| Start a new app | [Scaffold and run](#scaffold-and-run) |
| Know who is using the app and what they can see | [Verify the user and check access](#verify-the-user-and-check-access) |
| Read or change data on installing accounts | [Request permissions](#request-permissions) |
| React when an account installs or removes the app | [Track installations](#track-installations) |
| Ping members or the team | [Send notifications](#send-notifications) |
| Run work on a cron | [references/installs-and-schedules.md](references/installs-and-schedules.md) |
| Attach images or files | [references/notifications-and-files.md](references/notifications-and-files.md) |
| Sign in with Whop outside the iframe | [references/oauth.md](references/oauth.md) |
| Open links, profiles or an in-app purchase from the iframe; Frosted UI; React Native | [references/client-sdks.md](references/client-sdks.md) |
| Post to chat or forums, manage courses | `whop-communities` |

## Scaffold and run

1. Hosted by Whop:

   ```bash
   whop apps init --name "My App" --app_type b2c_app   # register, scaffold, link
   whop apps dev                                        # run locally
   whop apps deploy                                     # build, typecheck, upload, promote
   ```

   `whop apps deploy --preview` uploads without promoting; `whop apps builds promote <build_id>` ships it, and promoting an older build is the rollback. `whop apps secrets set --secret NAME=value` adds runtime secrets.
2. Self-hosted: run the dev proxy so `localhost` gets the same `x-whop-user-token` header as production: `pnpm add -D @whop-apps/dev-proxy` and `"dev": "whop-proxy --command 'next dev --turbopack'"`. Non-Node servers: `pnpm dlx @whop-apps/dev-proxy --standalone --upstreamPort=5000 --proxyPort=3000`.
3. In the developer dashboard → your app → **Hosting**, set the view paths. Defaults: experience `/experiences/[experienceId]`, dashboard `/dashboard/[companyId]`. Add `[restPath]` at the end for deep links.
4. Install the app on your own whop, open it, then in the cog menu set the environment to **localhost**.

| View | Appears | Path parameter | Gate |
|---|---|---|---|
| Experience | Sidebar of a whop, one per experience (`exp_`) | `[experienceId]` | `has_access` |
| Dashboard | Business dashboard → apps | `[companyId]` (a `biz_` ID) | `access_level === "admin"` |
| Discover (optional) | Discovery, where users browse content | none | your choice |

## Verify the user and check access

The access check, with the SDK's exact shape:

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const access = await whop.users.checkAccess({
  id: "user_xxxxxxxxxxxxx",
  resource_id: "exp_xxxxxxxxxxxxx",
});

console.log(access.has_access, access.access_level);
```

Verify the token once, in a server-only module (`lib/whop-user.ts`). `npm install jose`; set `WHOP_APP_ID` to your `app_` ID:

```ts
import { createRemoteJWKSet, jwtVerify } from "jose";

const whopKeys = createRemoteJWKSet(new URL("https://api.whop.com/.well-known/jwks.json"));

export async function verifyWhopUser(token: string | null | undefined): Promise<string> {
  if (!token) throw new Error("Missing x-whop-user-token");
  const { payload } = await jwtVerify(token, whopKeys, {
    issuer: "urn:whopcom:exp-proxy",
    audience: process.env.WHOP_APP_ID!,
    algorithms: ["ES256"],
  });
  if (!payload.sub) throw new Error("Whop user token has no subject");
  return payload.sub;
}
```

Then in a Next.js route handler (`app/api/experiences/[experienceId]/me/route.ts`):

```ts
import { WhopClient } from "@whop/sdk";
import { verifyWhopUser } from "@/lib/whop-user";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

export async function GET(
  request: Request,
  { params }: { params: Promise<{ experienceId: string }> },
): Promise<Response> {
  const { experienceId } = await params;

  let userId: string;
  try {
    userId = await verifyWhopUser(request.headers.get("x-whop-user-token"));
  } catch {
    return new Response("Unauthorized", { status: 401 });
  }

  const access = await whop.users.checkAccess({ id: userId, resource_id: experienceId });
  if (!access.has_access) return new Response("Forbidden", { status: 403 });

  return Response.json({ userId, accessLevel: access.access_level });
}
```

In a server component, pass `(await headers()).get("x-whop-user-token")` from `next/headers`. For a dashboard view, pass the `companyId` path parameter as `resource_id` and require `access_level === "admin"`. Python, Ruby and cross-domain setups are in [references/auth-and-access.md](references/auth-and-access.md).

## Request permissions

1. Find what each endpoint needs: every operation page in the API reference lists its required permissions.
2. Developer dashboard → your app → **Permissions** → **Add permissions**. Give each a justification and mark it **required** (creator can't disable) or **optional** (creator can decline; the app must still work). Up to 100 per app.
3. Install on a test account at `https://whop.com/apps/app_xxxxxxxxx/install` and approve the prompt. The flow is the same for self-testing.
4. Receiving webhooks needs its own `webhook_receive:*` permissions, for example `webhook_receive:payments`.

From code or CI, `whop apps permissions` or `apps.updatePermissions` sets the full list; each entry is `{ action, is_required, justification }` and the justification is 20 to 512 characters.

## Track installations

1. Create one webhook owned by the app:

   ```ts
   import { WhopClient } from "@whop/sdk";

   const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

   const webhook = await whop.webhooks.create({
     url: "https://example.com/webhooks/whop",
     resource_id: "app_xxxxxxxxxxxxx",
     events: ["app_installation.created", "app_installation.deleted"],
     api_version_date: "2026-08-14",
   });

   console.log(webhook.webhook_secret);
   ```

   The key needs `developer:manage_webhook` on the account that owns the app. Verify each delivery with `whop-webhooks`.
2. On `app_installation.created`, `data.id` is the installation (`aag_`) and the envelope's `account_id` is the business. Store your own record ID on it as `external_id`, then find it later with `appInstallations.list({ external_id })`. Treat a `created` for an installation you know as a reinstall: `external_id` and `metadata` come back with it.
3. On `app_installation.deleted`, stop acting for that account; the app can no longer reach it.

Details, limits and the per-install cron are in [references/installs-and-schedules.md](references/installs-and-schedules.md).

## Send notifications

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const result = await whop.notifications.create({
  experience_id: "exp_xxxxxxxxxxxxx",
  title: "New post",
  content: "A new workout program just dropped.",
  rest_path: "/posts/post_xxxxxxxxxxxxx",
});

console.log(result.success);
```

Use `account_id: "biz_..."` instead of `experience_id` to reach the team (dashboard apps). `rest_path` is appended to your view path, so it only routes if the path ends in `[restPath]`. More options in [references/notifications-and-files.md](references/notifications-and-files.md).

## Verify

1. Install the app on your own whop through the install link and approve every permission.
2. Open the experience with the environment set to **localhost** (dev proxy running) and confirm your route sees `x-whop-user-token` and returns the right user.
3. Visit as a non-member (or a second account) and confirm the experience returns `403`; open the dashboard view as a non-admin and confirm it's refused.
4. Uninstall and reinstall on the test account; confirm one `app_installation.deleted` then one `app_installation.created` with your `external_id` still set.
5. Send a notification to your test experience with `user_ids` set to your own user.

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| `x-whop-user-token` missing locally | No dev proxy | Run the app through `whop-proxy` and set the environment to **localhost** |
| Token missing on API calls in production | API on another origin | Reverse-proxy the API under the app's own origin |
| `whopsdk.verifyUserToken` doesn't exist on `WhopClient` | The helper isn't in `@whop/sdk` | Use the `jose` helper above (TS) or the Python/Ruby helper |
| `JWTClaimValidationFailed` on `aud` | `WHOP_APP_ID` is unset or another app's ID | Set it to the `app_` ID of the app the token was issued for |
| `403` from an API call | Permission not requested, or not re-approved after you added it | Add it in **Permissions**; re-approve in **Authorized apps** |
| No `app_installation.*` events | Webhook belongs to the account, not the app | Create it with `resource_id: "app_..."` |
| `409` updating an installation | `external_id` already used by another installation of your app | Values are unique (case-sensitive) across your installs |
| Notification rejected | Both or neither of `experience_id` / `account_id`, or missing `notification:create` | Send exactly one; add the permission |
| Deep link opens the app root | View path has no `[restPath]` | Add `[restPath]` to the path in **Hosting** |

## References

- [references/auth-and-access.md](references/auth-and-access.md): read when verifying the user in Python, Ruby or Express, proxying a cross-domain API, or choosing a credential.
- [references/installs-and-schedules.md](references/installs-and-schedules.md): read when linking installs to your records, using `metadata`, or setting up scheduled runs and hosting secrets.
- [references/notifications-and-files.md](references/notifications-and-files.md): read when targeting specific users, custom icons, or uploading files and multipart uploads.
- [references/oauth.md](references/oauth.md): read when adding Sign in with Whop or acting as a user outside the iframe.
- [references/client-sdks.md](references/client-sdks.md): read when using the iframe SDK, in-app purchases, Frosted UI, or building a React Native app.
