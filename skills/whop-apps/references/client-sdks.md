# Client-side SDKs: iframe SDK, Frosted UI, React Native

## Iframe SDK

`@whop/iframe` talks to the Whop page around your app over `window.postMessage`, so it works only in client components or browser JavaScript. `@whop/react` wraps it.

```tsx
// app/layout.tsx
import { WhopIframeSdkProvider } from "@whop/react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <WhopIframeSdkProvider>{children}</WhopIframeSdkProvider>
      </body>
    </html>
  );
}
```

```tsx
"use client";
import { useIframeSdk } from "@whop/react";

export function OpenProfile() {
  const iframeSdk = useIframeSdk();
  return <button onClick={() => iframeSdk.openExternalUrl({ url: "https://whop.com/@j" })}>View profile</button>;
}
```

Outside React: `createSdk({ appId: process.env.NEXT_PUBLIC_WHOP_APP_ID })` from `@whop/iframe`.

- `openExternalUrl({ url })` closes the app and navigates. A `https://whop.com/@username` (or `@user_...`) URL opens the profile in a modal instead.
- `inAppPurchase({ planId, id })` opens Whop's payment modal. Create the checkout configuration on your server first (with `whop-checkout`); `planId` is the configuration's `plan.id` and `id` its ID. On `res.status === "ok"`, `res.data.receipt_id` is the payment. Grant access from the `payment.succeeded` webhook, not from this client result.

## Frosted UI

Whop's React component library and design system (Radix UI and Tailwind based), shipped in `@whop/react`.

1. `pnpm add @whop/react`
2. Wrap the root layout in `<WhopApp accentColor="blue" appearance="inherit">`. It sets up the theme and the iframe SDK.
3. Optional: `withWhopAppConfig(nextConfig)` from `@whop/react/next.config`; `frostedThemePlugin()` from `@whop/react/tailwind` for design tokens.
4. Import components from `@whop/react`: `Text`, `Heading` (sizes `0`–`9`), `Button`, `Badge`, `Card`, `Dialog`, `Select`, `TextInput`, `TextArea`, `Checkbox`, `RadioGroup`, `IconButton`, `Theme`, `useThemeContext`.

## React Native apps

Run natively inside the Whop iOS and Android apps, and on the web, from one codebase.

- Create: `pnpm create @whop/react-native@latest` (Node 22+, pnpm 9.15+). Views live in `src/views/`: `experience-view.tsx`, `dashboard-view.tsx`, optional `discover-view.tsx`, each exporting a named component (`export function ExperienceView(props: ExperienceViewProps)`).
- `.env.local`: `WHOP_API_KEY`, `NEXT_PUBLIC_WHOP_APP_ID`, `NEXT_PUBLIC_WHOP_AGENT_USER_ID`, `NEXT_PUBLIC_WHOP_COMPANY_ID`.
- View props: experience view gets `experienceId`, `companyId`, `currentUserId` (or `null`), `path`, `params`; dashboard view gets `companyId`, `currentUserId`, `path`, `params`.
- Server calls: set the app's **Base URL** in the developer dashboard, read `const { apiOrigin } = __internal_execSync("getAppApiOrigin", {})` from `@whop/react-native`, and `fetch(`${apiOrigin}/api/...`)`. Requests through `apiOrigin` carry Whop's auth headers, so your server verifies the user and calls `users.checkAccess` exactly as a web app does.
- The guide's `whopSdk` client-side examples and `access.checkIfUserHasAccessToExperience` server example use a deprecated SDK interface; use the current server pattern instead.
- In-app purchase: `__internal_execAsync("inAppPurchase", { planId, id })` returns `sessionId` and `receiptId`.
- Ship: `pnpm ship` (flags `--ios`, `--android`, `--web`) uploads a development build, visible only in **Dev mode** (shake the phone). `pnpm preview` prints an install QR code. Promote to production from the app's **Builds** tab; Whop reviews it first. Roll back from the same screen.
- Libraries must support React Native; packages that need native modules outside the guide's recommended list aren't supported.

## Sources

- https://docs.whop.com/developer/guides/iframe.md
- https://docs.whop.com/developer/guides/frosted_ui.md
- https://docs.whop.com/developer/guides/react-native.md
