# Forums and courses through the API

Forums and courses are experiences. Create the Forum or Courses experience in the dashboard (or with `experiences.create`) and use its `exp_` ID. The chat elements don't cover forums or courses; the docs only describe API access to them.

## Forum posts

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const post = await whop.forumPosts.create({
  experience_id: "exp_xxxxxxxxxxxxx",
  title: "Weekly update",
  content: "Hey <@username>, check out this **update**",
  pinned: true,
  visibility: "members_only",
});

const comments = await whop.forumPosts.list({ experience_id: "exp_xxxxxxxxxxxxx", parent_id: post.id });
for await (const comment of comments) {
  console.log(comment.id, comment.content);
}

await whop.reactions.create({ resource_id: post.id, emoji: ":heart:" });
```

| Field | Notes |
|---|---|
| `experience_id` | Forum experience, or `"public"` together with `account_id` for the account's public forum |
| `content` | Markdown. `rich_content` (Tiptap JSON) takes priority when set |
| `title` | Required for paywalled posts; it stays visible to non-buyers |
| `parent_id` | Makes the post a comment on that post |
| `pinned` | Shows the post at the top of the feed |
| `is_mention` | Sends a mention notification to everyone in the experience with mentions on |
| `<@username>` in `content` | Notifies that user |
| `paywall_amount` + `paywall_currency` | Price in the currency's major unit (`5.0` with `"usd"` is $5.00). Send both or neither |
| `visibility` | `members_only` or `globally_visible` |
| `poll`, `attachments` | Poll options use sequential IDs from `"1"`; attachments are file IDs |

- The forums guide says `paywall_amount` is in cents. The SDK says "5.00 for $5.00" and the backend uses the value as the plan's price with the currency you pass, so send dollars.
- `content` is `null` in responses when the post is paywalled and the viewer hasn't bought it.
- `forumPosts.list` filters: `parent_id`, `pinned`. Also `retrieve` and `update`.
- Forum reactions are always likes: the `emoji` value is ignored.

## Forum settings

`forums.update({ id, ... })` takes the forum or experience ID:

| Field | Values |
|---|---|
| `who_can_post`, `who_can_comment` | `everyone`, `admins` |
| `email_notification_preference` | `all_admin_posts`, `only_weekly_summary`, `none` |
| `banned_words` | List of blocked words |
| `banner_image` | `{ id }` of an uploaded file, or `null` to remove |

`forums.list({ account_id, product_id })` lists forums.

## Courses

```ts
import { WhopClient } from "@whop/sdk";

const whop = new WhopClient({ token: process.env.WHOP_API_KEY! });

const course = await whop.courses.create({
  experience_id: "exp_xxxxxxxxxxxxx",
  title: "Getting started",
  visibility: "hidden",
  require_completing_lessons_in_order: true,
});

const chapter = await whop.courseChapters.create({ course_id: course.id, title: "Basics" });

await whop.courseLessons.create({
  chapter_id: chapter.id,
  lesson_type: "video",
  title: "Welcome",
  embed_type: "youtube",
  embed_id: "dQw4w9WgXcQ",
  days_from_course_start_until_unlock: 0,
});

const progress = await whop.courseLessonInteractions.list({ course_id: course.id, completed: true });
for await (const interaction of progress) {
  console.log(interaction.id);
}
```

- `lesson_type`: `text`, `video`, `pdf`, `multi`, `quiz`, `knowledge_check`. `embed_type`: `youtube`, `loom`. `content` is Markdown.
- `visibility` on a course: `visible` or `hidden`.
- `days_from_course_start_until_unlock` drips a lesson after the student starts the course.
- Thumbnails are uploaded file IDs (`{ id }`).
- `courses`, `courseChapters` and `courseLessons` each have `list`, `retrieve`, `update`, `delete`. `courseLessons` also has `start`, `markAsCompleted({ lesson_id })` and `submitAssessment` for acting as a student.
- `courseStudents.list({ course_id, keyword })` lists enrolled students. `courseLessonInteractions.list` filters by `user_id`, `lesson_id`, `course_id`, `completed`.
- Listen for `course_lesson_interaction.completed` instead of polling progress.

## Permissions (for Whop apps)

| Permission | Needed for |
|---|---|
| `forum:read` | Reading posts and comments |
| `forum:post:create` | Creating posts and comments |
| `chat:read` | Creating and reading reactions |

A federated (OIDC) access token can't post forum posts as the account; use an account API key.

## Sources

- https://docs.whop.com/developer/guides/forums.md
- https://docs.whop.com/developer/guides/webhooks.md
- https://docs.whop.com/developer/guides/oidc-federation.md
- https://docs.whop.com/developer/api/migrate-from-previous-versions.md
- https://docs.whop.com/api-reference/forums/forum.md
- https://docs.whop.com/api-reference/forum-posts/forum-post.md
- https://docs.whop.com/api-reference/courses/course.md
- https://docs.whop.com/api-reference/course-chapters/course-chapter.md
- https://docs.whop.com/api-reference/course-lessons/course-lesson.md
- https://docs.whop.com/api-reference/course-students/course-student.md
- https://docs.whop.com/api-reference/course-lesson-interactions/course-lesson-interaction.md
