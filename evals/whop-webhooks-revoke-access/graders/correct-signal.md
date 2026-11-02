---
type: llm
---

PASS if the answer tells the developer to handle `membership.updated` for loss of access, AND says how to detect it: either `previous_attributes` (for example `previous_attributes.status`, the status the membership left) or re-checking the membership's current status / access through the API.

FAIL if it presents `membership.deactivated`, `membership.went_invalid`, or `membership_went_invalid` as the primary event to build on, or if it gives no way to tell that access was lost.
