---
type: llm
---

PASS if the final message does both of these:
- Says which Whop environment the setup targets or should be tested in (sandbox or production), for example that the secret must come from a sandbox webhook while testing, or that it was written for sandbox first.
- Names at least one thing that is still unverified, such as the handler not having been run against a signed or real Whop delivery, or `grantAccess` not having been checked.

FAIL if it mentions neither environment, or presents the work as fully verified without naming anything left to check.
