# Ads — nothing to a live campaign

Read this before creating or launching ads. Enums and field lists live in each tool's
own schema — do not invent them.

Drafts can be created without billing. Launching (`status: "active"`) cannot.

## Setup

1. **Auth.** First-time ads billing needs a user login, not an API key — an API key
   can only reorder already-configured payment methods. A scope error saying the
   login predates the scope means the user must authorize again.
2. **Facebook page.** `social-accounts_list` must show `"platform": "facebook"`.
   - Connect an existing Meta Business: `social-accounts_connect` with
     `platform: "meta_business"`, `scopes: ["advertise"]`, and a `redirect_url`, then
     give the user the returned `authorize_url`.
   - Or create a Whop-managed page: `social-accounts_create` with
     `platform: "facebook"`. That needs the account's `banner_image`, `logo`, and
     `description` set via `accounts_update` first. Account API keys cannot update
     their own account's branding — that needs a user login. `meta_business` is
     invalid on create; use `facebook`.
3. **Payment method.** Check `accounts_preferences`. If its ads payment method
   is null, set `{"primary": {"type": "platform_balance"}}` via
   `accounts_update-preferences`. To fund the balance, send the user to their
   Whop dashboard to add funds; this connection can't create deposits.

TikTok uses `social-accounts_connect` with `platform: "tiktok"`. Same authorize-url
rule.

## Launch

1. **Get the creative from the user.** Ads use images or videos the user supplies —
   a file they give you, or one already on their Whop account. This plugin does not
   generate images. Upload a local file with `files_create`, then
   `files_complete`; the resulting `file.id` is what `creatives` wants. If the user
   has no creative yet, ask them for one.
2. `ads_create`:

```json
{
  "title": "Launch ad",
  "headlines": ["Find your stride"],
  "call_to_action": "sign_up",
  "url": "https://whop.com/your-store",
  "creatives": [{ "id": "file_x" }],
  "social_accounts": [{ "id": "sacc_x" }],
  "ad_group": {
    "title": "US broad",
    "conversion_location": "website",
    "ad_campaign": {
      "title": "Growth", "platform": "meta", "objective": "sales",
      "status": "draft", "budget_amount": 25,
      "budget_optimization": "ad_campaign"
    }
  }
}
```

3. **Confirm, then launch.** Show the user the campaign, the budget, and the
   destination URL, and ask whether to launch. Only after a clear yes, call
   `ad-campaigns_update` with `status: "active"`. Launching spends money.

Pass exactly one of `ad_group` or `ad_group_id`. A nested `ad_campaign` object inside
`ad_group` creates campaign + group + ad in one call — the API description
understates this. Reuse an existing container with `ad_group_id`, or `ad_campaign_id`
inside `ad_group`.

Keep `status: "draft"` until the user has reviewed. **Omitting draft launches
immediately**, which then requires billing and a destination URL.

| Field | Rule |
| --- | --- |
| `creatives` | One entry with no `format` is the base asset. Optional crops: `square` / `vertical` / `horizontal` only — not `portrait`. No duplicate formats. Two or more unformatted entries is a carousel (2–10). |
| `url` | Required to launch a website ad. A whop.com store page works as-is; an external page needs the Whop pixel. Drafts may omit it. |
| Budget | CBO: `budget_amount` on the campaign with `budget_optimization: "ad_campaign"`. ABO: `budget_amount` on the ad group with `budget_optimization: "ad_group"`. Never both. |
| Targeting | Omit `demographics` / `placements` / `devices` for automatic optimization. `regions` uses ISO 3166 (`"US"`, `"US-CA"`). |
| `lead_form` | Only with an instant-form `conversion_location`. |

`ads_update` with `creatives` replaces the whole set — include the base entry.
`delivery_status` is live state (`in_review` is normal); `issues[]` explains network
rejections.

## Sources

- https://docs.whop.com/developer/ai/connect.md
- https://docs.whop.com/developer/guides/ai_and_mcp.md
