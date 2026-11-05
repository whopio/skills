# Websites and apps (`*.whop.app`)

Read this before creating or deploying an app. Field lists and enums live in each
tool's own schema — do not invent them.

## Create the app

`apps_create` takes only `name` as required. The fields that matter for a hosted
site:

| Field | Notes |
| --- | --- |
| `name` | Required. Shown to users on the app store. |
| `app_type` | `website` (visitors browse `<route>.whop.app`), `b2c_app` (creators install it), plus `b2b_app`, `company_app`, `component`. Ask; do not guess. |
| `route` | The subdomain the hosted build is served from. A hosted app with no route cannot go live. |
| `account_id` | `biz_` tag. Defaults to the account behind the credential. |
| `base_url` | Only for an app you host yourself elsewhere. |

Ask which `app_type` before creating. The choice shapes how the app is surfaced, and
changing a website back to an app is not a supported move.

## Deploy

```
apps_deploy(id: "app_xxx", draft: false)
```

`apps_deploy` **builds the app's current source on Whop and ships it.** Nothing local
is required to deploy source Whop already holds.

- Only one deployment runs per app at a time. Calling it again while one is in flight
  reports that run rather than starting a second.
- Calling it with nothing to publish says so rather than starting a run.
- `draft: true` uploads the build without making it live. The default deploys and
  promotes in one step, so ask the user before a non-draft deploy.
- It returns the run it started. Follow progress on the app's `deployment` field via
  `apps_get`.

## Shipping code that only exists locally

`apps_deploy` builds what Whop already has. To get new local code up, do the local
half with your own tools and the rest over MCP:

1. Write and build the files yourself.
2. `files_create`, then `files_complete` for the archive. Web takes a JavaScript file
   or a `.zip` of the hosted site.
3. `app-builds_create` referencing the uploaded file — `attachment` takes `{ id }`
   for an existing file or `{ direct_upload_id }` for a completed direct upload.
4. Ask the user, then `app-builds_promote` to make that build live.

Promoting an older build rolls back to it.

Do not tell the user to install a CLI for any of this.

## Reading state

- `apps_get` — live state, including `deployment`.
- `apps_list` — every app on the account.
- `app-builds_list` / `app-builds_get` — build history.
- `apps_logs` — runtime logs.

`hosted_url` on an app is the live URL. Display it; it is not a "finish this step"
action link.

## Sources

- https://docs.whop.com/developer/websites/quickstart.md
- https://docs.whop.com/developer/guides/ai_and_mcp.md
