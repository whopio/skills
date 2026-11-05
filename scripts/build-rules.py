#!/usr/bin/env python3
"""Generate the Cursor and Antigravity rule files from one template.

Cursor reads rules/whop.mdc (named in .cursor-plugin/plugin.json); Antigravity
reads rules/*.md. Both carry the same guardrails as the Claude Code hooks, for
hosts that don't run hooks; only the frontmatter differs. Run after editing
scripts/rules.template.md; with --check, exit 1 if a rule file is out of date
(CI runs this through scripts/validate.py).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "rules.template.md"
RULES = ROOT / "rules"
DESCRIPTION = (
    "Building on Whop: @whop/sdk, Whop checkout and payments, webhooks, memberships and access checks, "
    "payouts, connected accounts, Whop apps and chat"
)
HEADER = "<!-- Generated from scripts/rules.template.md by scripts/build-rules.py. Edit the template, not this file. -->\n\n"

FRONTMATTER = {
    # Cursor: applied when the agent judges the description relevant.
    "whop.mdc": f"---\ndescription: {json.dumps(DESCRIPTION)}\nalwaysApply: false\n---\n\n",
    # Antigravity: model_decision loads the rule when the description matches the task.
    "whop.md": f"---\ntrigger: model_decision\ndescription: {json.dumps(DESCRIPTION)}\n---\n\n",
}


def expected() -> dict[Path, str]:
    body = TEMPLATE.read_text()
    return {RULES / name: frontmatter + HEADER + body for name, frontmatter in FRONTMATTER.items()}


def main() -> int:
    files = expected()
    if "--check" in sys.argv:
        stale = [p for p, content in files.items() if not p.is_file() or p.read_text() != content]
        extra = [p for p in RULES.iterdir() if p not in files] if RULES.is_dir() else []
        for path in stale + extra:
            print(f"{path.relative_to(ROOT)} is out of date; run scripts/build-rules.py")
        return 1 if stale or extra else 0
    RULES.mkdir(exist_ok=True)
    for path, content in files.items():
        path.write_text(content)
    print(f"Wrote {len(files)} rule files to {RULES.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
