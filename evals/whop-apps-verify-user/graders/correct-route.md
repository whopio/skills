---
type: llm
focus: { source: file, path: app/api/me/route.ts }
---

PASS if all of these hold in the file:
- The user ID comes from verifying the `x-whop-user-token` header by checking its signature against Whop's keys (for example `jwtVerify` from `jose` with `https://api.whop.com/.well-known/jwks.json`), not from a query parameter, body field, or other client-sent value.
- Verification checks the audience against `WHOP_APP_ID` (a token issued for another app must fail).
- Verification failure returns 401.
- It calls `users.checkAccess` with the verified user ID as `id` and the experience ID as `resource_id`, and returns 403 when `has_access` is false.
- The API key is read from `process.env.WHOP_API_KEY`.

FAIL if any of these is missing, if it decodes the JWT without verifying it, or if it uses the deprecated `@whop/api` package or the GraphQL-era `checkIfUserHasAccessToExperience`.
