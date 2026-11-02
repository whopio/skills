---
type: llm
focus: { source: file, path: components/BuyButton.tsx }
---

PASS if the client component never holds a Whop API key and instead calls the app's own server code (a route handler under `app/api/...` or a server action) that creates the checkout configuration with a server-only key (`WHOP_API_KEY`, not a `NEXT_PUBLIC_` variable), then redirects to the returned `purchase_url`.

FAIL if any Whop API key or `NEXT_PUBLIC_WHOP_API_KEY` is read in client code, or if the component calls the Whop API directly from the browser.
