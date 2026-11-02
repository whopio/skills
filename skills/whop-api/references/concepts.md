# Whop objects and IDs

## Accounts and people

- **Account** (`biz_`): a business on Whop. Owns API keys, products, webhooks and money. Older surfaces call it a company; same object.
- **Connected account**: an account you enroll and act for when you run a marketplace (also called a sub-merchant). See `whop-platforms`.
- **User** (`user_`): a person with a Whop login. Can buy from many accounts and help run one.
- **Team member**: a user granted a role on an account.
- **Member**: a user seen as a customer of an account, across all their purchases.
- **Verification**: the KYC (individual) or KYB (business) check an account clears before payouts. Produces an identity profile (`idpf_`).

## What you sell

- **Product** (`prod_`): the thing sold. Holds description, media, and variants.
- **Variant** (`plan_`): one purchasable configuration of a product: price, billing shape (`billing_type`), stock, SKU. Variant IDs keep the `plan_` prefix.
- **Membership** (`mem_`): what a buyer gets when they pay. Ties a user to a variant and carries a `status` saying whether access is valid now.
- **Experience** (`exp_`): content or functionality a product connects to. A membership to the product grants access to its experiences. Apps inside Whop render into an experience.
- **Entitlement**: the stored answer to "may this user use this now", checked against an account, product or experience with `users.checkAccess`.

## How money moves

- **Checkout configuration** (`ch_`): a reusable purchase definition that produces a live checkout page (`purchase_url`).
- **Payment** (`pay_`): one attempt to move money from a buyer to an account, with a status. "Charge" describes the same event from the card network's side; the API object is the payment.
- **Ledger** (`ldgr_`): the running record of credits and debits on an account's money. **Balance** is what you can spend or withdraw; **reserve** is held back against refunds and disputes; **fee** is Whop's cut.
- **Deposit**: money added to a balance from outside Whop. **Payout**: money leaving for a bank or wallet. **Transfer**: money moving between two Whop balances. **Swap**: converting a balance between tokens or chains. **Card** (`icrd_`): a Whop-issued virtual card spending from a balance.
- **Refund**: a completed payment returned by you. **Dispute**: a payment reversed by the buyer's bank, which you can contest.

## Building on Whop

- **App** (`app_`): software that runs inside Whop and reaches businesses through its marketplace. **App view**: one screen it renders (experience view or dashboard view).
- **Permission**: one capability an API key may exercise. **Scope**: the same idea on an OAuth token, what a user agreed to.
- **Element**: a prebuilt UI component you drop into your product.
- **Event** and **webhook**: something that happened, and the signed HTTP request telling your server.
- **`Api-Version-Date`**: the header pinning your integration to a dated API version. **Idempotency key**: the header that makes a `POST` safe to retry.

## Environments

| | Sandbox | Production |
|---|---|---|
| Dashboard | `https://sandbox.whop.com` | `https://whop.com` |
| API | `https://sandbox-api.whop.com/api/v1` | `https://api.whop.com/api/v1` |
| Money | Never moves | Real |
| Keys, webhooks, data | Own set | Own set |

The sandbox doesn't support payouts yet, apps and messaging, or payment methods other than cards. Test cards: `4242 4242 4242 4242` succeeds, `4000 0000 0000 0002` declines, any future expiry and any 3-digit CVC.

## ID prefixes

| Prefix | Object |
|---|---|
| `biz_` | Account |
| `user_` | User |
| `prod_` | Product |
| `plan_` | Variant |
| `mem_` | Membership |
| `mber_` | Member |
| `exp_` | Experience |
| `app_` | App |
| `pay_` | Payment |
| `ch_` | Checkout configuration |
| `ldgr_` | Ledger account |
| `idpf_` | Identity profile |
| `sacc_` | External account |
| `aff_` | Affiliate |
| `adcamp_`, `adgrp_`, `ad_` | Ad campaign, ad group, ad |
| `bnty_`, `btys_` | Bounty, bounty submission |
| `coma_` | Referred business |
| `icrd_` | Card |
| `course_` | Course |
| `file_` | File |

Use these tags everywhere the API takes an ID. Never send internal numeric IDs.

## Sources

- https://docs.whop.com/developer/concepts.md
- https://docs.whop.com/developer/guides/sandbox.md
- https://docs.whop.com/developer/troubleshooting.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
