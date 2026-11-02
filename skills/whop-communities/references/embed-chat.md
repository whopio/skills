# Chat elements: web and iOS

The chat elements come from the legacy `@whop/embedded-components-react-js` and `@whop/embedded-components-vanilla-js` packages. You load `WhopElements`, open one chat session with a token function, and mount elements. Each element renders in an isolated frame with its own theming and localization.

| Element | Type string (vanilla) | React component | Swift view |
|---|---|---|---|
| Chat | `chat-element` | `ChatElement` | `WhopChatView` |
| DMs list | `dms-list-element` | `DmsListElement` | `WhopDMsListView` |
| Search | `search-element` (or `session.showSearchModal`) | none documented | none documented |

Try them without code in the playground: `https://docs.whop.com/developer/guides/chat/playground.md` embeds `https://apollo.elements.whop.com/chat?embedded=1`.

## Vanilla JS

```js
import { loadWhopElements } from "@whop/embedded-components-vanilla-js";

const whopElements = await loadWhopElements();

const session = whopElements.createChatSession({
  token: async () => {
    const res = await fetch("/api/chat/token", { method: "POST" });
    return (await res.json()).token;
  },
});

const chat = session.createElement("chat-element", { channelId: "chat_feed_XXXXXXXXXXXXXX" });
chat.on("messageSent", (ev) => console.log(ev.detail.id, ev.detail.channelId));
chat.mount("#chat-container");
```

With the script tag (`https://apollo.elements.whop.com/release/elements.js`), use `new WhopElements()` instead of `loadWhopElements()`.

## Chat element options

| Option | Notes |
|---|---|
| `channelId` | Required. `chat_feed_...` for channels, `feed_...` for DMs and support chats |
| `deeplinkToPostId` | Scroll to and highlight a message |
| `style` | `"imessage"` (default, bubbles) or `"discord"` (full width) |
| `disableNavigation` | Don't follow links; handle `linkClick` yourself |
| `emptyState` | Custom empty state |
| `features` | `{ banUser, muteUser, previewAttachments, mentionExperiences }` booleans |
| `onReady`, `onEvent` | Callbacks; same as listening to the events |

Events (React `onEvent` with `event.type`, vanilla `element.on(name, ev => ev.detail)`):

| Event | `detail` |
|---|---|
| `profileClick` | `{ id }` |
| `linkClick` | `{ url }` |
| `messageSent` | `{ id, content, channelId }` |
| `experienceClick` | `{ id }` |

In React, build `options` with `useMemo` and the handler with `useCallback`; types `ChatElementOptions` and `ChatElementEvent` come from `@whop/embedded-components-vanilla-js/types`.

## DMs list element

Options: `companyId` (only show conversations for that account), `selectedChannel`, `emptyState`, `onReady`, `onEvent`. Event: `channelSelected` with `{ id }`; open that ID in a `ChatElement`.

```tsx
"use client";

import { useCallback, useMemo, useState } from "react";
import { ChatElement, ChatSession, DmsListElement, Elements } from "@whop/embedded-components-react-js";
import { loadWhopElements } from "@whop/embedded-components-vanilla-js";
import type { DmsListElementEvent, DmsListElementOptions } from "@whop/embedded-components-vanilla-js/types";

const elements = loadWhopElements();

async function getToken() {
  const res = await fetch("/api/chat/token", { method: "POST" });
  return (await res.json()).token;
}

export function Inbox() {
  const [channelId, setChannelId] = useState<string>();

  const onEvent = useCallback((event: DmsListElementEvent) => {
    if (event.type === "channelSelected") setChannelId(event.detail.id);
  }, []);

  const options: DmsListElementOptions = useMemo(
    () => ({ companyId: "biz_xxxxxxxxxxxxx", selectedChannel: channelId, onEvent }),
    [channelId, onEvent],
  );

  return (
    <Elements elements={elements}>
      <ChatSession token={getToken}>
        <DmsListElement options={options} />
        {channelId && <ChatElement options={{ channelId }} style={{ height: "100dvh", width: "100%" }} />}
      </ChatSession>
    </Elements>
  );
}
```

Create DMs with the same `account_id` you pass here as `companyId`, or they won't show. Admins don't see support chats in this list.

## Search element

Searches messages in a channel, DM or support chat. Options: `channelId`, `companyId`, `onReady`, `onClose`, `onResultClick` (`detail: { messageId, channelId }`). It unmounts on close or result click unless you call `ev.preventDefault()`.

```js
session.showSearchModal({
  channelId: "feed_XXXXXXXXXXXXXX",
  onResultClick: (ev) => console.log(ev.detail.messageId),
});
```

## Session

- `token`: a function (called and awaited, refreshed before expiry) or a string (never refreshed; swap it with `session.updateOptions({ token })`).
- Events: `ready`, `tokenRefreshed`, `tokenRefreshError`, `error`, `optionsUpdated`.
- `session.destroy()` unmounts every element.

## WhopElements options

| Option | Values |
|---|---|
| `appearance` | `theme` and `classes` (below) |
| `locale` | `en` (default), `es`, `zh`, `nl`, `pt`, `de`, `hu`, `it`, `fr`, `ja`, `pl`, `tr` |
| `environment` | `"production"` (default) or `"sandbox"` |

`updateOptions(partial)` changes them at runtime and propagates to every session and element.

## Theming

React: `<Elements elements={elements} appearance={{ theme: { ... } }}>`. Vanilla: `whopElements.updateOptions({ appearance: { theme: { ... } } })`.

| Web option | Swift (`WhopTheme`) | Purpose |
|---|---|---|
| `appearance` | follows the app | `"light"` or `"dark"` |
| `accentColor` | `accent` | Links, selection, primary actions |
| `grayColor` | `neutral` | Text, borders, backgrounds |
| `dangerColor`, `warningColor`, `successColor`, `infoColor` | `danger`, `warning`, `success`, `info` | Semantic states |

Colors: `amber`, `blue`, `bronze`, `brown`, `crimson`, `cyan`, `gold`, `grass`, `gray`, `green`, `indigo`, `iris`, `jade`, `lemon`, `lime`, `magenta`, `mint`, `orange`, `pink`, `plum`, `purple`, `red`, `ruby`, `sky`, `teal`, `tomato`, `violet`, `yellow`.

`appearance.classes` takes CSS selectors as keys and emits them into the element's frame. Only the documented class names (for example `DialogContent`, `DialogTitle`) are a stable contract; anything else may stop matching.

## iOS (Swift)

1. Add `https://github.com/whopio/whopsdk-elements-swift` in Xcode and import `WhopElements`.
2. Add `NSCameraUsageDescription`, `NSMicrophoneUsageDescription` and `NSPhotoLibraryUsageDescription` to `Info.plist` (photos, video, voice messages).
3. As soon as the user is signed in: `await WhopSDK.configure(tokenProvider: MyProvider())`, where the provider's `getToken()` calls your token endpoint and returns `WhopTokenResponse(accessToken:)`. Or use `WhopSDK.configureWithOAuth` (see `chat-auth.md` in this folder).
4. Render `WhopChatView(channelId:, style: .imessage)` (or `.discord`, `deeplinkToPostId:`, `onEvent:` with `.profileTap`, `.urlTap`, `.messageSent`) and `WhopDMsListView(companyId:, onEvent:)` with `.channelSelected(channel)`. Apply `.whopTheme(WhopTheme(accent: .plum, neutral: .gray))`.

## Sources

- https://docs.whop.com/developer/guides/chat/quickstart.md
- https://docs.whop.com/developer/guides/chat/chat-element.md
- https://docs.whop.com/developer/guides/chat/dms-list-element.md
- https://docs.whop.com/developer/guides/chat/theming-and-styles.md
- https://docs.whop.com/developer/guides/chat/playground.md
- https://docs.whop.com/sdk/elements/overview.md
- https://docs.whop.com/sdk/elements/whop-elements.md
- https://docs.whop.com/sdk/elements/chat-session.md
- https://docs.whop.com/sdk/elements/chat-element.md
- https://docs.whop.com/sdk/elements/dms-list-element.md
- https://docs.whop.com/sdk/elements/search-element.md
- https://docs.whop.com/sdk/elements/types.md
- https://docs.whop.com/sdk/elements/styling-reference.md
