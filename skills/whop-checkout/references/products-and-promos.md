# Products, variants, promo codes and tax IDs

A **product** (`prod_...`) is what the buyer gets access to. A **variant** (`plan_...`) is one way to pay for it: a price, a currency and a billing type. Memberships, payments and checkout configurations all point at a variant.

## Variant fields

| Field | Meaning |
|---|---|
| `billing_type` | `one_time` or `renewal` |
| `initial_price` | Major units of `currency` (`10.43` = $10.43). The full price for a one-time variant; for a renewal variant, an extra amount charged **on top of** the first `renewal_price` |
| `renewal_price` | Major units, charged every `billing_period` (zero for one-time) |
| `billing_period` | Days between charges: `30` monthly, `365` yearly. `null` for one-time |
| `trial_period_days` | Free days before the first renewal charge; at checkout only `initial_price` is due while a trial applies |
| `currency` | Defaults to USD |
| `title` | 30 characters max |
| `expiration_days` | Access ends after this many days |
| `visibility`, `metadata` | Listing visibility and your own key/value pairs |

A paid variant charges at least 1.00; a free one has price `0`. The response's `purchase_url` is a ready checkout link, and `initial_price_due` states what one unit costs at checkout.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const lifetime = await whop.variants.create({
  account_id: "biz_xxxxxxxxxxxxx",
  product_id: "prod_xxxxxxxxxxxxx",
  billing_type: "one_time",
  initial_price: 99,
  currency: "usd",
  title: "Lifetime",
});

const yearlyWithTrial = await whop.variants.create({
  account_id: "biz_xxxxxxxxxxxxx",
  product_id: "prod_xxxxxxxxxxxxx",
  billing_type: "renewal",
  billing_period: 365,
  renewal_price: 290,
  initial_price: 0,
  trial_period_days: 7,
  currency: "usd",
  title: "Yearly",
});

console.log(lifetime.purchase_url, yearlyWithTrial.purchase_url);
```

Use `whop.variants.*`; the `/plans` endpoints are deprecated, and `plan.*` webhook names are unchanged. Products expose their `default_variant`.

## Promo codes

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const promo = await whop.promoCodes.create({
  account_id: "biz_xxxxxxxxxxxxx",
  code: "LAUNCH25",
  promo_type: "percentage",
  amount_off: 25,
  base_currency: "usd",
  new_users_only: false,
  promo_duration_months: 3,
  unlimited_stock: true,
  variant_ids: ["plan_xxxxxxxxxxxxx"],
});

console.log(promo.id);
```

- `promo_type: "percentage"`: send `amount_off: 25` for 25% off. The API stores and returns it as a fraction (`0.25`).
- `promo_type: "flat_amount"`: `amount_off` is in `base_currency` major units.
- Set `stock` or `unlimited_stock: true`; one of them is required.
- `promo_duration_months` is how many billing periods the discount lasts. Limit scope with `product_id` or `variant_ids`, and redemption with `one_per_customer`, `expires_at`, `new_users_only`.

Apply a code with `promoCode="LAUNCH25"` on the `Checkout` handle, or `promo_code_id` (or `promo_code`) on `payments.create`. The code must be active and valid for the variant.

## Tax IDs

- **Your account's** registrations: `whop.accounts.update({ id, tax_identifiers: [{ tax_id_type: "eu_vat", tax_id_value: "DE123456789" }] })`. One per `tax_id_type`.
- **A buyer's** tax ID prices a business purchase: `tax_ids: [{ type, value }]` on Create Payment Quote (one per quote), or the `TaxIdElement` inside a `Payments` handle.
- Greece uses `EL`, not `GR`. Northern Ireland is `xi_vat` on a quote. An invalid EU VAT number is refused with `eu_vat_number_invalid` on an account.
- Payment quotes replace the deprecated `calculate_tax` on variants.

## Sources

- https://docs.whop.com/api-reference/beta/variants/variant.md
- https://docs.whop.com/api-reference/beta/variants/create-variant.md
- https://docs.whop.com/api-reference/beta/promo-codes/promo-code.md
- https://docs.whop.com/api-reference/beta/promo-codes/create-promo-code.md
- https://docs.whop.com/developer/guides/save-payment-methods.md
- https://docs.whop.com/developer/guides/tax-ids.md
- https://docs.whop.com/developer/api/versioning.md
