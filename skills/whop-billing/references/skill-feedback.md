# Skill feedback

Read this when the user says the `whop-billing` skill gave wrong or outdated guidance, left something out, or could be clearer. Also read it when the Whop docs or the installed SDK contradicted this skill during the task. This is feedback on the skill's instructions, not on Whop's products or the user's account.

GitHub issues are public. Never post one until the user has seen the exact title and body and said yes.

## Leave out

Draft from the conversation, then remove anything private and describe the problem in general terms:

- API keys, webhook secrets (`ws_...`), access tokens and passwords
- Whop IDs from the user's account (`biz_`, `user_`, `mem_`, `pay_`, `prod_`, `plan_`...). Use placeholders such as `biz_xxxxxxxxxxxxx`
- Customer names, emails, IP addresses and amounts tied to a real customer
- Private code, internal URLs, logs and env files. Quote only the few lines that show the problem, with placeholders

## Steps

1. **Ask once.** Offer to report it to the skill's maintainers. If the user says no, drop it and carry on with the task.
2. **Draft.** Title: `skill-feedback: <skill>: <what went wrong, in a few words>`, where `<skill>` is the skill that gave the guidance (this file belongs to `whop-billing`; when the user names another `whop-*` skill, use that name). Body: the table below, filled from the conversation. Always name the file and section of the skill that caused the problem.
3. **Show it.** Print the exact title and body and ask: "Post this as a public issue on whopio/skills?" Agreeing in step 1 is not approval of the text. If the user asks for changes, make them and ask again.
4. **Post on yes.** Write the body to a temporary file and run `gh issue create --repo whopio/skills --title "<title>" --body-file <file>`.
5. **Share the result.** Give the user the issue URL. If `gh` is missing, not signed in, or fails, give them the title and body and this link to file it by hand: `https://github.com/whopio/skills/issues/new?template=skill-feedback.md`.

## Issue body

| Field | Value |
|---|---|
| Type | `wrong` (incorrect guidance), `outdated`, `missing` or `unclear` |
| Skill | The skill that gave the guidance, with the version from `metadata.version` in its `SKILL.md` |
| Source | File and section, e.g. `SKILL.md` > Rules > 4, or `references/<file>.md` > <section> |
| Agent | The agent and model in use, if known |
| Task | What the user was trying to do |
| Expected | What should have happened, with the docs page or SDK type that shows it, if any |
| Actual | What the skill said, or what happened when it was followed (error message, wrong behavior) |
| Suggested fix | How the skill should change; leave blank if unsure |
