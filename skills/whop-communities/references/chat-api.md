# Server-side chat API

Call these from your backend with an API key (or from a Whop app with its App API key). Identify a channel by its ID or by the Chat experience ID (`exp_...`).

## Messages

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const message = await whop.messages.create({
  channel_id: "chat_feed_xxxxxxxxxxxxx",
  content: "Hello! **Markdown** is supported.",
  attachments: [{ id: "file_xxxxxxxxxxxxx" }],
});

const history = await whop.messages.list({ channel_id: "chat_feed_xxxxxxxxxxxxx", direction: "desc", first: 20 });
for await (const item of history) {
  console.log(item.id, item.content);
}

await whop.reactions.create({ resource_id: message.id, emoji: ":heart:" });
```

- `channel_id` accepts a channel, DM or support chat ID, or an experience ID. `content` is Markdown. Optional `replying_to_message_id`, `poll: { options: [{ id: "1", text }] }` (sequential IDs from `"1"`), `auto_detect_links`.
- Upload attachments first with `files.create` (see the Files API).
- To send a DM from the server: `dmChannels.create({ with_user_ids })`, then `messages.create` with that channel's ID.
- New messages arrive as the `chat.message.created` webhook and reactions as `chat.reaction.created`; subscribe instead of polling `messages.list`.

## Channels

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.chatChannels.update({
  id: "chat_feed_xxxxxxxxxxxxx",
  ban_media: false,
  ban_urls: true,
  banned_words: ["spam", "scam"],
  user_posts_cooldown_seconds: 10,
  who_can_post: "admins",
  who_can_react: "everyone",
});

const channels = await whop.chatChannels.list({ account_id: "biz_xxxxxxxxxxxxx", first: 10 });
for await (const channel of channels) {
  console.log(channel.id);
}
```

- `who_can_post`: `everyone` or `admins` (an announcements channel). `who_can_react`: `everyone` or `no_one`. `user_posts_cooldown_seconds: 0` or `null` removes the cooldown.
- There's no create method for channels: create a Chat experience (`experiences.create`), attach it to a product (`experiences.attach`), and the channel exists. `chatChannels.retrieve` accepts the `exp_` ID. `chatChannels.list` can filter by `product_id`.
- Access follows product membership; give access through checkout or a membership invite.

## Direct messages

- `dmChannels.create({ with_user_ids, account_id, custom_name, notifications_enabled })`. Each entry in `with_user_ids` can be a user ID, username or email. Up to 50 members.
- `dmMembers.create({ channel_id, user_id })` adds someone; `dmMembers.delete` removes them; `dmMembers.list` lists them.
- `dmChannels.list({ account_id })`, `dmChannels.update`, `dmChannels.delete`.
- DMs don't follow product membership and have no room moderation; manage members yourself.

## Support chats

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const support = await whop.supportChannels.create({
  account_id: "biz_xxxxxxxxxxxxx",
  user_id: "user_xxxxxxxxxxxxx",
  custom_name: "Billing question",
});

const open = await whop.supportChannels.list({
  account_id: "biz_xxxxxxxxxxxxx",
  open: true,
  order: "last_post_sent_at",
  direction: "desc",
  include_last_message: true,
  first: 10,
});
for await (const channel of open) {
  console.log(channel.id, channel.customer_user?.username, channel.needs_reply);
}
```

- `create` returns the customer's existing support chat if there is one. `user_id` takes a user ID or username.
- `list` filters: `open` (`true` awaiting a response, `false` resolved), `customer_user_id` / `customer_user_ids` (up to 100), `participated`, `view`, `order`, `direction`. `include_last_message` adds `last_message` and `unread`; leave it off for large lists.
- Team members with the moderator role can answer support chats without full admin access.

## Permissions (for Whop apps)

| Permission | Needed for |
|---|---|
| `chat:read` | Reading messages, channels, reactions |
| `chat:message:create` | Posting messages |
| `chat:moderate` | Updating channel settings |
| `support_chat:create` | Opening support channels |
| `support_chat:read` | Reading support channels |

Federated (OIDC) access tokens can't create DM channels for the account or reply to support chats as the account; use an account API key for those.

## Sources

- https://docs.whop.com/developer/guides/chat.md
- https://docs.whop.com/developer/guides/chat/channels.md
- https://docs.whop.com/developer/guides/chat/direct-messages.md
- https://docs.whop.com/developer/guides/chat/support-chats.md
- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/developer/guides/oidc-federation.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
- https://docs.whop.com/api-reference/messages/message.md
- https://docs.whop.com/api-reference/chat-channels/chat-channel.md
- https://docs.whop.com/api-reference/dm-channels/dm-channel.md
- https://docs.whop.com/api-reference/dm-members/dm-member.md
- https://docs.whop.com/api-reference/support-channels/support-channel.md
- https://docs.whop.com/api-reference/reactions/reaction.md
