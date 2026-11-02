# Installations, scheduled runs, and hosting

## App installations

An installation is one install of your app on one account, ID prefixed `aag_`. Your app's webhook (created with `resource_id: "app_..."`) gets `app_installation.created` and `app_installation.deleted` for every account, plus the other events those accounts granted through `webhook_receive:*` permissions. An account's own webhooks never receive installation events.

`app_installation.created` payload:

```json
{
  "type": "app_installation.created",
  "account_id": "biz_J8n2R5p9T1w4Kx",
  "data": {
    "id": "aag_T4k8M2p6W9r3Qx",
    "app": { "id": "app_XXXXXXXX", "name": "Market Lane" },
    "account": { "id": "biz_J8n2R5p9T1w4Kx", "title": "River Coffee" },
    "external_id": null,
    "metadata": {},
    "requesting_reauthorization": false
  }
}
```

### Link an installation to your records

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.appInstallations.update({
  id: "aag_xxxxxxxxxxxxx",
  external_id: "river-coffee",
  metadata: { connected_at: "2026-10-26T00:00:00Z" },
});

const installations = await whop.appInstallations.list({ external_id: "river-coffee" });
for await (const installation of installations) {
  console.log(installation.account.id);
}
```

- `external_id` is unique across your app's installations and case-sensitive. A value another installation holds returns `409`. At most 255 characters. Filtering by it returns at most one installation, so the installation can be your whole mapping table.
- `metadata` merges: keys you send are set, a key set to `null` is removed, keys you omit stay, `{}` clears all. Values are strings; at most 50 keys, keys up to 100 characters, values up to 500.
- A removed installation keeps its `external_id`; no other installation can take it while removed. A reinstall is the same installation: `id`, `created_at`, `external_id` and `metadata` come back.
- Don't store secrets there; your developer account can read both fields. The account the app is installed on always sees them as `null`.
- After `app_installation.deleted` the installation leaves `GET /app_installations` and your app can no longer act on that account.
- Retries keep the same `webhook-id`; ignore duplicates by it.

| Caller | Access |
|---|---|
| App API key | List, retrieve, update your app's installations. Needs `developer:app_installation:read` / `developer:app_installation:update`. |
| Developer account | `GET /app_installations?app_id=app_...` lists every installation. Needs `developer:basic:read`. |
| Installing account | Lists apps installed on it; `metadata` and `external_id` are `null`. |

Creating the app-owned webhook needs `developer:manage_webhook` on the account that owns the app.

## Scheduled runs

For Whop-hosted apps with a production web build that has a server entry. Set either schedule with `apps.update`; the key needs `developer:update_app`.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.apps.update({
  id: "app_xxxxxxxxxxxxx",
  schedule: "0 3 * * *",
  per_install_schedule: "*/15 * * * *",
});
```

| Field | Runs |
|---|---|
| `schedule` | Once per slot for the whole app. No minimum interval. |
| `per_install_schedule` | Once per slot for every installation. No more often than every 15 minutes. |

Five-field cron, UTC, at most 64 characters, must fire at least once. `null` or `""` clears it. An invalid expression returns `400`.

Export `scheduled()` next to `fetch()` in the build's server entry:

```ts
export default {
  async scheduled(controller: { cron: string; scheduledTime: number; noRetry(): void }, env: unknown, ctx: { props: any }) {
    const { kind, app_installation, run_id } = ctx.props;
    if (kind === "global") return;
    console.log(run_id, app_installation.id, app_installation.metadata.orders_cursor);
  },
};
```

| `ctx.props` | Value |
|---|---|
| `kind` | `global` (from `schedule`) or `install` (from `per_install_schedule`) |
| `app_installation` | The installation object; `null` on a global run |
| `run_id` | Shared by every installation's run in the same slot |
| `scheduled_at` | The slot, ISO 8601 |
| `attempt` | `1`, or `2` on the retry |

- A run can last 15 minutes (requests get 30 seconds) and shares the request handlers' secrets and injected API key.
- A failed run is retried once, a minute later, then dropped. Call `controller.noRetry()` before throwing to skip the retry.
- The same slot can arrive twice, and a retry can overlap the next slot. If work must not repeat, record `run_id` plus `app_installation.id` and skip ones you've done.
- Slots skipped while there's no production web build with a server entry are never made up. Keep a sync cursor in the installation's `metadata` and continue from it.
- `console` output and uncaught errors appear in `whop apps logs`.

## Hosting (apps from `whop apps init`)

- `whop apps deploy` builds, uploads and promotes; `--preview` uploads only; `whop apps builds promote abld_...` makes a build live and is the rollback.
- `whop apps secrets set --secret NAME=value`, `list`, `unset --key NAME`. `whop apps dev` injects them locally; a variable you export yourself wins.
- Reserved bindings: `APP_ID`, `BUILD_ID`, `WHOP_API_ORIGIN`, `WHOP_ACCOUNT_ID`, `ASSETS`, `REALTIME`.
- Server-side `fetch` to `${process.env.WHOP_API_ORIGIN}/api/v1/...` is signed with the app's key; the key never reaches your code. Send `x-whop-inject-key: none` to skip it. Browser fetches aren't signed: route them through your own handler. The injected key can't withdraw, transfer, or manage payout destinations.
- Logs keep `console.log`, uncaught exceptions and failed requests for 7 days: `whop apps logs app_... --level error --query "checkout"`.

## Sources

- https://docs.whop.com/developer/guides/app-installations.md
- https://docs.whop.com/developer/guides/scheduled-runs.md
- https://docs.whop.com/developer/websites/hosting.md
- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/cli/commands.md
