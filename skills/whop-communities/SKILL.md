---
name: whop-communities
description: >-
  Embed Whop chat in your own web or iOS app and use Whop's community APIs:
  mint chat access tokens, sync your users, render the Chat, DMs list and
  search elements, theme them, create channels, DMs and support chats, send
  messages and reactions, and manage forums, forum posts, courses, chapters,
  lessons and students. Use when: "embed Whop chat", "add chat to my React
  app", "chat token endpoint", "ChatElement", "DMs list", "support chat for a
  customer", "open a DM between two users", "send a message to a Whop
  channel", "post to a Whop forum", "create a course with the API", "read
  lesson completions", "chat shows unauthorized".
  Chain with: whop-api for client setup, whop-platforms for enrolling your
  users as connected accounts, whop-webhooks for chat.message.created,
  whop-apps when the code runs inside a Whop app. NOT for: building an app
  that runs inside Whop (use whop-apps), checkout or payment elements (use
  whop-checkout), payout or wallet elements (use whop-payouts).
license: Apache-2.0
metadata:
  author: whop
  version: "0.2.0"
---

# Whop Communities

Whop chat renders inside your own product through the chat elements, authenticated by a short-lived token your server mints for the signed-in user. The same chat, forum and course data is also reachable from your backend through `@whop/sdk`.

## Before you start

1. Fetch `https://docs.whop.com/developer/guides/chat/quickstart.md`, `https://docs.whop.com/developer/communities/overview.md` and the changelog at `https://docs.whop.com/developer/api/versioning.md`. If they disagree with this skill, follow the docs.
2. Create an account API key in the developer dashboard and keep it on the server as `WHOP_API_KEY`. Set up the client with `whop-api`.
3. Find your account ID (`biz_...`) in the dashboard URL: `whop.com/dashboard/biz_XXXXXXXXX/`.
4. Decide how users authenticate: **account-scoped tokens** (your app has its own users; no Whop sign-in) or **OAuth** (users sign in to Whop). Most products want account-scoped tokens.

## Rules

1. **Chat embeds use the legacy packages.** `@whop/embedded-components-react-js` plus `@whop/embedded-components-vanilla-js` on web, the `whopsdk-elements-swift` package on iOS. The newer Whop Elements cover checkout, payments, wallet and payouts, not chat.
2. **Mint tokens on your server with `accessTokens.create`, passing `account_id` and `user_id` together.** The docs' snippets still show `company_id`; the SDK and the API take `account_id`.
3. **Always pass explicit `scoped_actions`.** An empty or missing list gives the token every permission your API key has, and the token goes to the browser.
4. **Take `user_id` from your own session**, never from the request body. The token acts as that user.
5. **Give `ChatSession` a token function, not a string.** A function is called again before the token expires (1 hour by default, 3 hours max); a string is never refreshed.
6. **The user must exist on Whop first.** Enroll each of your users as a connected account with `accounts.create` and store `account.owner.id` (`user_...`). OAuth users skip this.
7. **Pick the chat type by who may read it.** Channels (`chat_feed_...`) follow product membership and have no member cap. DMs (`feed_...`) are private, up to 50 members. Support chats (`feed_...`) are one customer and your account, with an open/resolved inbox.
8. **Create DMs and support chats with your `account_id`** so they land in your account's inbox and the DMs list filtered by `companyId`, not the user's unrelated Whop messages.
9. **Don't poll for messages.** Subscribe to the `chat.message.created` webhook; use `messages.list` only for history.
10. **Forum paywalls are in dollars with a currency.** `paywall_amount: 5.00` plus `paywall_currency: "usd"` is $5.00. The forums guide says cents; the SDK and backend take major units, and sending one field without the other is rejected.

## Pick a path

| Goal | Do this |
|---|---|
| Show live chat in my web app | [Embed chat](#embed-chat) |
| My users aren't on Whop yet | [Sync your users](#sync-your-users) |
| A room for everyone who bought a product | [Create a conversation](#create-a-conversation): channel |
| Private chat between specific users | [Create a conversation](#create-a-conversation): DM, then the DMs list element |
| A help desk between customers and my team | [Create a conversation](#create-a-conversation): support chat |
| Post, read, moderate or react from my backend | [references/chat-api.md](references/chat-api.md) |
| Forums, courses, lessons, students | [Forums and courses](#forums-and-courses) |
| Users sign in with Whop, or iOS | [references/chat-auth.md](references/chat-auth.md), [references/embed-chat.md](references/embed-chat.md) |
| Code that runs inside a Whop app | `whop-apps` for auth, then the APIs here |

## Embed chat

1. Install: `pnpm add @whop/sdk` on the server; `pnpm add @whop/embedded-components-react-js @whop/embedded-components-vanilla-js` in the React frontend. Plain HTML: `<script src="https://apollo.elements.whop.com/release/elements.js"></script>`.
2. Add a token endpoint. The minting call:

   ```ts
   import { WhopClient } from "@whop/sdk";

   const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

   const { token } = await whop.accessTokens.create({
     account_id: "biz_xxxxxxxxxxxxx",
     user_id: "user_xxxxxxxxxxxxx",
     scoped_actions: [
       "chat:message:create",
       "chat:read",
       "dms:read",
       "dms:message:manage",
       "dms:channel:manage",
       "support_chat:read",
       "support_chat:message:create",
     ],
   });

   console.log(token);
   ```

   As a Next.js route (`app/api/chat/token/route.ts`), with the user from your own session:

   ```ts
   import { NextResponse } from "next/server";
   import { WhopClient } from "@whop/sdk";
   import { getSession } from "@/lib/session";

   const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

   export async function POST() {
     const session = await getSession();
     if (!session) return new NextResponse("Unauthorized", { status: 401 });

     const { token } = await whop.accessTokens.create({
       account_id: process.env.WHOP_ACCOUNT_ID!,
       user_id: session.whopUserId,
       scoped_actions: ["chat:message:create", "chat:read"],
     });

     return NextResponse.json({ token });
   }
   ```

   Request only the scope groups you render: `chat:message:create`, `chat:read` for channels; `dms:read`, `dms:message:manage`, `dms:channel:manage` for DMs; `support_chat:read`, `support_chat:message:create` for support chats.
3. Render the element (`components/Chat.tsx`):

   ```tsx
   "use client";

   import { ChatElement, ChatSession, Elements } from "@whop/embedded-components-react-js";
   import { loadWhopElements } from "@whop/embedded-components-vanilla-js";

   const elements = loadWhopElements();

   async function getToken() {
     const res = await fetch("/api/chat/token", { method: "POST" });
     const data = await res.json();
     return data.token;
   }

   export function Chat({ channelId }: { channelId: string }) {
     return (
       <Elements elements={elements}>
         <ChatSession token={getToken}>
           <ChatElement options={{ channelId }} style={{ height: "100dvh", width: "100%" }} />
         </ChatSession>
       </Elements>
     );
   }
   ```

   The chat element connects to a channel, DM or support chat by `channelId`. Options, events (`profileClick`, `linkClick`, `messageSent`, `experienceClick`), deep links, the DMs list, search, theming, vanilla JS and Swift are in [references/embed-chat.md](references/embed-chat.md).

## Sync your users

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const account = await whop.accounts.create({
  email: "user@example.com",
  title: "Jane Doe",
  metadata: { internal_user_id: "user_12345" },
});

console.log(account.owner.id);
```

Store `account.owner.id` against your user and pass it as `user_id` when minting. To show an account-specific name and avatar in chat, call `users.update({ id, account_id, name, profile_picture: { id: "file_..." } })`; without `account_id` it changes the user's global profile. That needs `user:profile:update` on the key. Details in [references/chat-auth.md](references/chat-auth.md).

## Create a conversation

| Type | Create | Render |
|---|---|---|
| Channel | Create a Chat experience (`experiences.create`), attach it to a product (`experiences.attach`), give users the product | `ChatElement` with the `chat_feed_` ID (`chatChannels.retrieve` accepts the `exp_` ID) |
| DM | `dmChannels.create({ with_user_ids, account_id })`; add or remove people with `dmMembers` | `ChatElement`, or `DmsListElement` with `companyId` |
| Support chat | `supportChannels.create({ account_id, user_id })`; returns the existing one if the customer already has one | `ChatElement` for the customer; build the team inbox with `supportChannels.list` |

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const support = await whop.supportChannels.create({
  account_id: "biz_xxxxxxxxxxxxx",
  user_id: "user_xxxxxxxxxxxxx",
});

const dm = await whop.dmChannels.create({
  account_id: "biz_xxxxxxxxxxxxx",
  with_user_ids: ["user_xxxxxxxxxxxxx", "user_yyyyyyyyyyyyy"],
});

console.log(support.id, dm.id);
```

Server-side messaging, moderation, reactions and inbox filters are in [references/chat-api.md](references/chat-api.md).

## Forums and courses

Each forum or course in a community sidebar is its own experience, so `experience_id` scopes everything.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const post = await whop.forumPosts.create({
  experience_id: "exp_xxxxxxxxxxxxx",
  title: "Premium breakdown",
  content: "Full notes in **Markdown**.",
  paywall_amount: 5.0,
  paywall_currency: "usd",
});

await whop.forumPosts.create({
  experience_id: "exp_xxxxxxxxxxxxx",
  parent_id: post.id,
  content: "First comment",
});

const course = await whop.courses.create({ experience_id: "exp_xxxxxxxxxxxxx", title: "Onboarding" });
const chapter = await whop.courseChapters.create({ course_id: course.id, title: "Week 1" });
await whop.courseLessons.create({ chapter_id: chapter.id, lesson_type: "text", title: "Welcome", content: "Start here." });
```

`paywall_amount` is in major units of `paywall_currency` (`5.0` = $5.00). Students, progress and the rest are in [references/forums-and-courses.md](references/forums-and-courses.md).

## Verify

1. Call your token endpoint signed in and signed out: it returns `{ token }` only for a signed-in user, minted for that user's own Whop ID.
2. Render a channel the test user's product grants and send a message; listen for `messageSent`.
3. Create a support chat for the test user, open it as that user, and reply from the dashboard's support inbox.
4. Create a DM with your `account_id` and confirm it appears in `DmsListElement` with the same `companyId`.
5. For a test environment, set the WhopElements `environment` option to `"sandbox"` and use sandbox keys; production is the default.

## Errors

| Symptom | Cause | Fix |
|---|---|---|
| Chat never authenticates | Token endpoint fails, returns another shape, or the user isn't on Whop | Return `{ token }`; sync the user first |
| Chat works, then stops after about an hour | `token` passed as a string | Pass the fetch function to `ChatSession` |
| Can read but not send | Missing `chat:message:create` (or the DM / support scope) in `scoped_actions` | Add the scope group for that chat type |
| Channel shows no access | User has no product containing the Chat experience | Grant the product; channels follow membership |
| DM missing from the DMs list | DM created without `account_id`, or list has a different `companyId` | Create with your `account_id`; pass the same `companyId` |
| Support chat not in the admin DMs list | By design | Build the team inbox with `supportChannels.list` |
| TypeScript error on `company_id` in `accessTokens.create` | Docs snippet uses the old name | Use `account_id` |
| "Must provide both paywall amount and currency" | `paywall_amount` without `paywall_currency`, or the reverse | Send both |
| Forum post costs 100x too much | Amount sent in cents | `paywall_amount` is dollars, with `paywall_currency` |

## References

- [references/embed-chat.md](references/embed-chat.md): read when configuring the chat, DMs list or search elements, events, deep links, theming, vanilla JS or Swift.
- [references/chat-auth.md](references/chat-auth.md): read when choosing account-scoped tokens or OAuth, syncing users, or scoping tokens.
- [references/chat-api.md](references/chat-api.md): read when posting, reading or moderating chat from your backend, managing DMs and support inboxes, or reacting.
- [references/forums-and-courses.md](references/forums-and-courses.md): read when working with forums, forum posts, courses, chapters, lessons, students or lesson completions.
