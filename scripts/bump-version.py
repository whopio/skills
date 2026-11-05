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
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    ".kimi-plugin/plugin.json",
    ".antigravity-plugin/plugin.json",
    "gemini-extension.json",
]
# Where each host reads the whop MCP server, and the X-Whop-Plugin suffix that
# names the host (keep in sync with MCP_HOST_SUFFIX in validate.py).
MCP_FILES = {
    ".mcp.json": "",
    "mcp.json": " (agent-plugins)",
    "gemini-extension.json": " (gemini)",
    ".kimi-plugin/plugin.json": " (kimi)",
    "mcp_config.json": " (antigravity)",
}


def update_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def set_mcp_header(data: dict, value: str) -> None:
    data["mcpServers"]["whop"]["headers"]["X-Whop-Plugin"] = value


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
    for name, suffix in MCP_FILES.items():
        update_json(ROOT / name, lambda d: set_mcp_header(d, f"skills/{version}{suffix}"))
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill_md.read_text()
        skill_md.write_text(re.sub(r'(\n  version: )"[^"]*"', rf'\1"{version}"', text, count=1))

    print(f"Set version {version}. Run scripts/validate.py to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
