# Company formation

The tool is `accounts_form_company`. Taxonomy values, state enums, and founder field
lists live in its schema — do not invent them.

It creates a **hosted checkout**. It does not charge and it does not file. Give the
user the returned `checkout_url` so they review the total and pay. Filing starts
after payment. Track progress on the account's `company_formation` field via
`accounts_get`.

## Checkout

`accounts_form_company` on a `biz_` account id — not `user_`. Required: `business_name`,
`formation_state`, `business_type`, `industry_group`, `industry_type`, `founders`.

```json
{
  "business_name": "Acme Holdings",
  "formation_state": "DE",
  "business_type": "services",
  "industry_group": "marketing_and_advertising",
  "industry_type": "seo_agency",
  "business_address": {
    "line1": "1 Market St", "city": "San Francisco",
    "state": "CA", "postal_code": "94105", "country": "US"
  },
  "business_phone": "+12125550100",
  "founders": [{
    "is_primary": true, "first_name": "Jane", "last_name": "Doe",
    "email": "jane@example.com", "phone": "+12125550100",
    "address": {
      "line1": "1 Market St", "city": "San Francisco",
      "state": "CA", "postal_code": "94105", "country": "US"
    },
    "ownership_percentage": 100
  }]
}
```

Always pass a unique idempotency key. If a result is uncertain, retry with the
**same** key — a new key would create a second checkout.

Founder identity (SSN, date of birth, home address) is required by the filing, and
the user may choose to provide it. When they do, pass it to the tool as given. Do not
infer a missing value, echo it back, or write it to a file. If the user would rather
not share it here, give them the `checkout_url` and let them enter it on Whop.

## LLC vs C-corp vs registered agent

| Path | Extra rules |
| --- | --- |
| LLC (default `entity_type: "llc"`) | Each founder needs `ownership_percentage`; they must total 100. |
| C-corp (`entity_type: "c_corp"`) | Requires `share_structure`. Every founder needs at least one `role` (`president`, `secretary`, `treasurer`, `director`), and those officer roles must all be covered across the set. Ask before executing. |
| Registered agent | `use_registered_agent: true` omits `business_address` and `business_phone`. Otherwise both are required. |

`expedite_ein` is only valid when no founder supplies an SSN.

Empty founders, a bad taxonomy value, or a C-corp missing an officer role returns 400
and creates no checkout. Re-read the tool's schema; do not guess industry slugs.

## Sources

- https://docs.whop.com/developer/guides/ai_and_mcp.md
