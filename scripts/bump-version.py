#!/usr/bin/env python3
"""Set one version across VERSION, every SKILL.md, every plugin manifest, and the MCP header."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
JSON_FILES = [
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    "gemini-extension.json",
]
MCP_FILES = [".mcp.json", "mcp.json", "gemini-extension.json"]


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def set_mcp_header(data: dict, version: str) -> None:
    data["mcpServers"]["whop"]["headers"]["X-Whop-Plugin"] = f"skills/{version}"


def main() -> int:
    if len(sys.argv) != 2 or not SEMVER.match(sys.argv[1]):
        print("usage: scripts/bump-version.py <major.minor.patch>", file=sys.stderr)
        return 2
    version = sys.argv[1]

    (ROOT / "VERSION").write_text(version + "\n")
    for name in JSON_FILES:
        update_json(ROOT / name, lambda d: d.update(version=version))
    update_json(
        ROOT / ".claude-plugin/marketplace.json",
        lambda d: [plugin.update(version=version) for plugin in d["plugins"]],
    )
    for name in MCP_FILES:
        update_json(ROOT / name, lambda d: set_mcp_header(d, version))
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill_md.read_text()
        skill_md.write_text(re.sub(r'(\n  version: )"[^"]*"', rf'\1"{version}"', text, count=1))

    print(f"Set version {version}. Run scripts/validate.py to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
