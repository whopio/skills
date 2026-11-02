#!/usr/bin/env python3
"""Generate Gemini CLI commands (TOML) from commands/*.md.

Claude Code, Cursor and Kimi read the Markdown commands. Gemini CLI reads only
TOML, so each commands/<name>.md becomes commands/whop-developer/<name>.toml
(`/whop-developer:<name>` in Gemini). Run after editing a command; with
--check, exit 1 if the generated files are out of date (CI runs this through
scripts/validate.py).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "commands"
TARGET = SOURCE / "whop-developer"
# Gemini installs extensions to ~/.gemini/extensions/<name>/ and doesn't expand
# variables inside command prompts.
GEMINI_ROOT = "$HOME/.gemini/extensions/whop-developer"
HEADER = "# Generated from commands/{name}.md by scripts/build-gemini-commands.py. Edit the Markdown, not this file.\n"


def toml_string(value: str) -> str:
    # JSON string escaping is valid TOML basic-string escaping.
    return json.dumps(value, ensure_ascii=False)


def convert(md: Path) -> str:
    text = md.read_text()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise SystemExit(f"{md}: missing frontmatter")
    frontmatter, body = match.groups()
    description = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if not description:
        raise SystemExit(f"{md}: missing description")
    body = body.strip() + "\n"
    if "{{" in body or "!{" in body or "@{" in body:
        raise SystemExit(f"{md}: contains Gemini template syntax ({{{{, !{{ or @{{)")
    body = body.replace("$ARGUMENTS", "{{args}}")
    body = body.replace("${CLAUDE_PLUGIN_ROOT}", GEMINI_ROOT)
    body = re.sub(r" If `\$HOME/\.gemini/extensions/whop-developer` doesn't expand in this environment, [^\n]*", "", body)
    return (
        HEADER.format(name=md.stem)
        + f"description = {toml_string(description.group(1).strip())}\n"
        + f"prompt = {toml_string(body)}\n"
    )


def expected() -> dict[Path, str]:
    return {TARGET / f"{md.stem}.toml": convert(md) for md in sorted(SOURCE.glob("*.md"))}


def main() -> int:
    files = expected()
    if "--check" in sys.argv:
        stale = [p for p, content in files.items() if not p.is_file() or p.read_text() != content]
        extra = [p for p in TARGET.glob("*.toml") if p not in files] if TARGET.is_dir() else []
        for path in stale + extra:
            print(f"{path.relative_to(ROOT)} is out of date; run scripts/build-gemini-commands.py")
        return 1 if stale or extra else 0
    TARGET.mkdir(exist_ok=True)
    for path in TARGET.glob("*.toml"):
        if path not in files:
            path.unlink()
    for path, content in files.items():
        path.write_text(content)
    print(f"Wrote {len(files)} Gemini commands to {TARGET.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
