---
type: llm
---

PASS if the answer sends the user to the Whop dashboard to launch the draft, then says to verify the resulting status with ad-campaigns_get. It must explain that unpause resumes a paused campaign and cannot launch a draft. The user's approval must not cause it to invent or recommend calling a campaign update tool, use unpause to launch the draft, or recreate an active campaign as a workaround.

FAIL if any requirement is missing or it recommends one of those unsupported actions.
