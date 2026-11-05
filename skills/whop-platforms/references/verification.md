# Verification through the API

Verification (KYC for a person, KYB for a business) is required before an account can pay out. Accepting payments doesn't need it until the account reaches $5,000 in payments. Every call needs an Account API key with `identity:read` (reads) or `identity:write` (writes).

## Create

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const verification = await whop.verifications.create({
  account_id: "biz_xxxxxxxxxxxxx",
  body: {
    kind: "individual",
    first_name: "Jane",
    last_name: "Doe",
    date_of_birth: "1995-01-15",
    country: "US",
    tax_identification_number: "123-45-6789",
    address: { line1: "123 Main St", city: "San Francisco", state: "CA", postal_code: "94105" },
  },
});

if (verification.status === "pending" && verification.session_url) {
  console.log("Send the user to", verification.session_url);
}
```

- Every field except `kind` is optional prefill; the hosted session at `session_url` collects the rest.
- `tax_identification_number` (the SSN for a US person) is **required when `country` is `US`**. Send it as is; it is tokenized in transit.
- An address in a sanctioned country or region fails with `400` and code `address_country_sanctioned`.
- An account has at most one `individual` and one `business` verification.
- A person who operates through a company stays `kind: "individual"` and adds `business_name` and `business_structure`, so payouts can go to a business bank account.
- `kind: "business"` (KYB) takes `business_name`, `business_structure`, `business_tax_identification_number` (EIN in the US), `registration_number`, `incorporation_date`, `place_of_incorporation`, `documents` (`file_` IDs for `articles_of_incorporation` / `certificate_of_incorporation`, up to 10MB each) and up to 10 `owners`.
- `business_website` must be an external site or social link; Whop store pages are rejected.
- `rejected` is final for that session: call `verifications.create` again to start a new one.
- Calling `verifications.create` while a session is still in progress resumes it rather than starting over. To abandon it and start fresh, send `restart: true`. The API accepts it, but `@whop/sdk` 2.7.0 doesn't type it. A session in `manual_review` can't be restarted.

## Reuse an existing verification

- **Sumsub share token**: if you already verified the person with Sumsub and have a Reusable KYC agreement with Whop, send `share_token`. The response is `approved`, or `pending` with a `session_url` covering only what is missing. Each token works once and can't be combined with `documents` or `document_type`.
- **`verification_id`** (`idpf_`) reuses an approved verification, but only for the signed-in Whop user who started it. API keys, OAuth tokens and onboarding links are refused, so a platform can't use it server-side.

## Identity documents without a hosted session

Send the photos in the create request and skip the session. Individual verifications only; the request must also carry `document_type`, `first_name`, `last_name`, `date_of_birth`, `country`, `phone`, `tax_identification_number` and an `address` with `line1`, `city`, `state` and `postal_code`.

| `document_type` | `documents` keys |
|---|---|
| `id_card` | `id_card_front`, `id_card_back`, `selfie` |
| `drivers` | `drivers_front`, `drivers_back`, `selfie` |
| `residence_permit` | `residence_permit_front`, `residence_permit_back`, `selfie` |
| `passport` | `passport_front`, `selfie` |

- Each value is the file's raw bytes, base64-encoded. JPEG, PNG or PDF; the selfie must be JPEG or PNG; 5MB per file before encoding.
- Send the complete set in one request. A missing, oversized or unreadable file fails the whole request with an error naming the key; nothing partial is submitted.
- A `201` means review started and `required_documents` shows each key as `submitted`. Poll `verifications.retrieve({ id })` until `approved` or `rejected`.
- A rejected photo returns the verification to `action_required` with that key `pending_upload` and a `rejection_reason`. Send the same create request again with a better photo.
- Some countries accept only some document types, and people in a few countries can't be verified at all. A type that isn't valid for the person's country fails in review with a `rejection_reason`, not upfront. Check the country table in the identity documents guide.

## Read status

`verifications.list({ account_id })` returns the account's verifications (`include_subaccounts` adds subaccounts); `verifications.retrieve({ id })` returns one.

| Status | Meaning | Your move |
|---|---|---|
| `not_started` | No session yet | Create one |
| `pending` | Waiting on the user | Send them to `session_url` |
| `processing` | Automated checks running | Wait |
| `action_required` | Open items in `requested_information` | Answer RFIs |
| `manual_review` | Under review, nothing to submit | Wait (usually within 3 business days) |
| `approved` | Verified | Payouts can proceed |
| `rejected` | Failed | Create a new verification |

The webhook `identity_profile.updated` fires on every change and names the profile, not its state: re-read. `identity_profile.needs_action`, `identity_profile.approved` and `identity_profile.rejected` also fire for those transitions.

## Update

`verifications.update({ id, body })` corrects prefill before approval: `first_name`, `last_name`, `date_of_birth`, `country`, `personal_address`, `business_name`, `business_address`, `business_structure`. An empty body fails with `at least one field is required`; an approved verification fails with `Cannot update an approved verification.`.

Deleting a verification exists in the API but is turned off by default (`403 Deleting verifications is not enabled for this account.`). Don't build on it.

## Answer RFIs

Each open item has `id` (`inrqi_`), `requirement`, `type`, `label`, and, when they apply, `options`, `optional` and `errors`. Answer with `verifications.update({ id, body: { requested_information: [...] } })`, one payload per item:

| Item `type` | Answer |
|---|---|
| `text`, `date`, `phone`, `select` | `value`: dates `YYYY-MM-DD`, phones E.164 (`+12125550123`), selects one of `options` |
| `address` | `address` object (no PO boxes) |
| `files` | `files`: `file_` IDs from the upload flow, one per page in order (JPEG, PNG or PDF, up to 32 MB) |
| `id_document` | `documents`: slot keys for one ID (`passport_front`; `id_card_front` + `id_card_back`; `drivers_front` + `drivers_back`; `residence_permit_front` + `residence_permit_back`) as `file_` IDs |

- Tax and ID numbers (`ssn`, `ein`, `company_tax_id`, `personal_id_number`) are sent as plain `value`s and tokenized in transit. If you already hold a Basis Theory token, send it with `value_type: "vault_token"`.
- A rejected answer comes back with `errors: [{ code, reason }]`. Show `reason`, treat unknown codes as a generic rejection, and also handle a rejected item with no `errors`. Resubmit with the same item `id`.
- Common document codes: `expiration_date`, `unsatisfactory_photos`, `screenshots`, `bad_selfie`, `bad_face_matching`, `problematic_applicant_data`, `document_page_missing`, `additional_document_required`.

## Business structures

`business_structure` depends on the country of incorporation. US values: `single_member_llc`, `multi_member_llc`, `private_corporation`, `private_partnership`, `public_corporation`, `public_partnership`, `sole_proprietorship`, `unincorporated_association`, `incorporated_non_profit`, `unincorporated_non_profit`. For countries not in the business structures table, send `business_name` and omit `business_structure`. Look up other countries in the guide rather than guessing.

## Sources

- https://docs.whop.com/developer/verification/overview.md
- https://docs.whop.com/developer/verification/retrieve.md
- https://docs.whop.com/developer/verification/rfis.md
- https://docs.whop.com/developer/verification/manage.md
- https://docs.whop.com/developer/verification/identity-documents.md
- https://docs.whop.com/developer/verification/business-structures.md
- https://docs.whop.com/api-reference/beta/verifications/create-verification.md
