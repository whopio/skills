# Selling from iOS and React Native

| App | Use | Server code |
|---|---|---|
| Native iOS, subscriptions and digital unlocks | `WhopCheckout` (Swift package `https://github.com/whopio/whopsdk-checkout-swift`) | No |
| Native iOS, physical goods or real-world services | `Checkout.ApplePayButton` from `WhopCheckout` | No |
| SwiftUI payment form you design | `Elements` (Swift package `https://github.com/whopio/elements-swift`) | Yes, charge the token |
| Your own React Native app | `@whop/elements-react-native` | Yes, charge the token |
| A React Native app running inside Whop | Not this skill; use `whop-apps` | |

## iOS: WhopCheckout

In the United States it uses Whop's payment processing (2.7% + $0.30 instead of Apple's 15–30%); elsewhere it falls back to StoreKit. Requires iOS 17+, Xcode 15+, Swift 5.10+.

The SDK takes an API key scoped to **`iap:read` only**. That permission covers in-app purchase operations and is safe to embed in the app bundle. Never ship a key with broader permissions.

```swift
import SwiftUI
import WhopCheckout

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(Checkout.shared)
                .task {
                    try? await Checkout.shared.configure(
                        companyId: "biz_xxxxxxxxxxxxx",
                        apiKey: "your_iap_read_key",
                        planMappings: [.init(whopId: "plan_xxxxxxxxxxxxx", appleId: "monthly_sub")]
                    )
                }
        }
    }
}
```

`planMappings` pairs each Whop variant with its App Store product ID for the StoreKit fallback; one-time Apple Pay purchases don't need it. `checkout.plans` (type `CheckoutPlan`) lists the variants; the names are kept for compatibility.

Purchase:

```swift
do {
    let result = try await checkout.purchase(planId)
    print(result.receiptId)
} catch WhopCheckoutError.cancelled {
} catch WhopCheckoutError.paymentFailed(let message) {
    showError(message)
}
```

Entitlements: `checkout.hasAccess(to: "prod_xxxxxxxxxxxxx")` for one product, `checkout.isSubscribed` for any active subscription, `checkout.memberships` for the list. `Checkout` is `@Observable`, so views re-render when status changes. Call `checkout.logIn(appUserId:)` with your own user ID to sync purchases across devices, and `checkout.logOut()` on sign-out.

**Apple Pay is not for digital content.** `Checkout.ApplePayButton(planId:label:onCompletion:)` is only for physical goods (merch, food, hardware) and real-world services (tickets, deliveries). Premium features, subscriptions, in-app currency and content unlocks must use StoreKit (the `purchase` path above handles that).

## React Native: @whop/elements-react-native

```bash
npm install @whop/elements-react-native
```

Requires React Native 0.87+ with Swift Package Manager (0.86+ with CocoaPods), the New Architecture, iOS 15.1+ and Android `minSdk` 24.

1. Wrap the app in `<WhopElements getToken={...}>`. `getToken` calls **your server**, which calls Create Access Token (`POST /api/v1/access_tokens`) and returns the token; never ship a Whop API key in the app.
2. Mount `<Payments accountId="biz_xxxxxxxxxxxxx" plan="plan_xxxxxxxxxxxxx" returnUrl="https://example.com/return">` with the email, payment and branding elements. `returnUrl` must be `https`; custom URL schemes are refused.
3. `createConfirmationToken()` and post the token to your server, which calls `payments.create` exactly as on the web (see `SKILL.md`).
4. If the payment status is `requires_action`, call `handleNextAction` with the `client_secret`.

Apple Pay in the native elements uses the merchant registered on the Whop account. Errors you'll see while wiring it: `BrandingRequiredError` (no branding element mounted) and `ChargeConfigError` (`<Payments>` has neither a `plan` nor an `amount` and `currency` pair). `getToken` is called again before every request, so return a fresh access token rather than caching one; returning an API key fails with `Authentication failed`.

## SwiftUI: Elements

Add `https://github.com/whopio/elements-swift.git` from `"0.1.0"`, `import Elements`, apply `.whopElements(environment: .production)`, and build a `WhopPayments(accountID:charge: .plan(id:))` scope containing `WhopEmailElement`, `WhopPaymentElement` and `WhopBrandingElement`. Call `payments.createConfirmationToken()` and charge on your server.

## Sources

- https://docs.whop.com/developer/guides/ios/overview.md
- https://docs.whop.com/developer/guides/ios/installation.md
- https://docs.whop.com/developer/guides/ios/build-a-paywall.md
- https://docs.whop.com/developer/guides/ios/accept-one-time-payments.md
- https://docs.whop.com/developer/guides/ios/check-entitlements.md
- https://docs.whop.com/developer/guides/ios/checkout-reference.md
- https://docs.whop.com/elements/latest/getting-started.md
- https://docs.whop.com/developer/guides/react-native.md
