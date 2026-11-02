# Push notifications and file uploads

## Notifications

Notifications appear in the Whop mobile app and on the web. Sending needs the `notification:create` permission, and the experience must belong to your app or the account must have the app installed.

| | Experience notification | Account notification |
|---|---|---|
| Audience | Users with access to the experience | Team members of the account |
| Best for | Member-facing apps | Dashboard apps |
| Keying field (exactly one) | `experience_id` | `account_id` |
| `user_ids` | Must have experience access | Must be team members |

`notifications.create` fields: `title` and `content` (required), `subtitle`, `experience_id` or `account_id`, `user_ids` (only these users are notified, as a mention), `rest_path`, `icon_user_id`.

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

await whop.notifications.create({
  account_id: "biz_xxxxxxxxxxxxx",
  title: "Action Required",
  content: "Please review and approve the pending invoices.",
  user_ids: ["user_xxxxxxxxxxxxx"],
  rest_path: "/reports/flagged-transactions",
});

await whop.notifications.create({
  experience_id: "exp_xxxxxxxxxxxxx",
  title: "New Comment",
  content: "Sarah replied to your post.",
  icon_user_id: "user_xxxxxxxxxxxxx",
  rest_path: "/posts/my-post-123",
});
```

### Deep links

`rest_path` is appended to your app's view path. Configure the path with `[restPath]` at the end (for example `/experiences/[experienceId]/[restPath]`). With an app at `https://your-app.com` and `rest_path: "/posts/post_123"`, the user opens `https://your-app.com/experiences/exp_xxx/posts/post_123`; handle it at `app/experiences/[experienceId]/posts/[postId]/page.tsx` in Next.js. Query strings work too: `rest_path: "?action=review&id=123"`.

### Icons

The default icon is the experience avatar, the account avatar, or both. `icon_user_id` uses that user's profile picture, which suits social events (who commented or followed).

Trigger notifications from server events: `payment.succeeded`, `membership.activated`, `chat.message.created` (see `whop-webhooks`).

## File uploads

Uploads are direct to storage, in two steps the SDK only half-handles:

1. `files.create({ filename })` returns the file `id`, a presigned `upload_url`, and `upload_headers`.
2. `PUT` the bytes to `upload_url` with every header in `upload_headers`. No Whop `Authorization` header; the presigned URL carries the credentials.

```ts
import { readFile } from "node:fs/promises";
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const file = await whop.files.create({ filename: "photo.jpg" });

await fetch(file.upload_url!, {
  method: "PUT",
  headers: file.upload_headers as Record<string, string>,
  body: await readFile("./photo.jpg"),
});

let uploaded = await whop.files.retrieve({ id: file.id });
while (uploaded.upload_status === "pending" || uploaded.upload_status === "processing") {
  await new Promise((resolve) => setTimeout(resolve, 1000));
  uploaded = await whop.files.retrieve({ id: file.id });
}
if (uploaded.upload_status !== "ready") throw new Error(`Upload failed: ${uploaded.upload_status}`);

console.log(uploaded.url);
```

- The `id` can be attached right away (for example `courses.update({ id, thumbnail: { id: file.id } })` or a message's `attachments: [{ id }]`); poll `files.retrieve` for the final `url`.
- `upload_status` goes `pending` → `processing` → `ready` or `failed`. `url`, `size` and `content_type` stay `null` until then.
- The presigned URL expires one hour after it's issued; a `PUT` that fails with `403` after a delay needs a fresh file. Multipart part URLs expire after 15 minutes.
- From a browser, create the file on your server and hand the browser only `upload_url` and `upload_headers`, so the bytes skip your server and the key stays private.
- `/files` needs API version `2026-08-21-1` or later when calling without an SDK (`Api-Version-Date` header).

### Visibility

Set at create time; it can't change later.

| `visibility` | `url` | Use for |
|---|---|---|
| `private` (default) | Signed URL that expires; retrieve the file again for a fresh one | Attachments, user documents, dispute evidence |
| `public` | Permanent CDN URL, can't be revoked | Product images, thumbnails, branding |

Attaching a file to a resource moves it to the storage matching that resource's visibility.

### Multipart (large files)

Required above 5 GB, sensible above ~100 MB; the file must be larger than 5 MB. At most 10,000 parts of 5 MB each (about 50 GB).

1. `files.create({ filename, multipart: true, byte_size })` returns `multipart_upload_id`, `multipart_upload_urls` (`{ part_number, url }`) and `multipart_chunk_size`.
2. `PUT` each `multipart_chunk_size` slice (last may be smaller) to its URL and keep the returned `ETag` header as-is, quotes included.
3. `files.complete({ id, multipart_upload_id, multipart_parts: [{ part_number, etag }] })` with every part in order. A wrong `ETag` or unknown upload ID returns `400`.
4. Poll `files.retrieve` until `ready`.

## Sources

- https://docs.whop.com/developer/guides/notifications.md
- https://docs.whop.com/developer/guides/upload-files.md
- https://docs.whop.com/developer/guides/direct-file-uploads.md
- https://docs.whop.com/developer/guides/chat.md
