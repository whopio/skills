#!/usr/bin/env python3
"""Structural checks for the skills repo. Exits non-zero on any error."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

ALLOWED_FRONTMATTER_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SOFT_LINE_LIMIT = 300
HARD_LINE_LIMIT = 500

BANNED_PATTERNS = [
    "btoa(",
    "webhookKey",
    "hosted_kyc",
    "hosted_payouts",
    "plans.create",
    "companies.create",
    "companies.list",
    "companies.update",
    "parent_company_id",
    "withdrawals.create",
    "topups.",
    "chargeUser",
    "mcp.whop.com/sse",
    "new Whop(",
    "plan_type",
    "@whop/embedded-components",
    "@whop/checkout",
    "WhopCheckoutEmbed",
    "membership.went_valid",
    'from "@whop/api"',
]
BANNED_EXEMPT_FILES = {SKILLS_DIR / "whop-migrate" / "references" / "legacy-map.md"}
BANNED_EXEMPT_PATTERNS_BY_DIR = {
    SKILLS_DIR / "whop-communities": {"@whop/embedded-components"},
}

PLUGIN_NAME = "whop-developer"
MANIFESTS = [
    ("plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".claude-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".claude-plugin/marketplace.json", lambda d: d["plugins"][0]["version"], lambda d: d["plugins"][0]["name"]),
    (".codex-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".cursor-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".grok-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    ("gemini-extension.json", lambda d: d["version"], lambda d: d["name"]),
]

errors: list[str] = []
warnings: list[str] = []


def error(path: Path | str, message: str) -> None:
    errors.append(f"{relative(path)}: {message}")


def warn(path: Path | str, message: str) -> None:
    warnings.append(f"{relative(path)}: {message}")


def relative(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_frontmatter(path: Path) -> tuple[dict, str] | None:
    try:
        import yaml
    except ImportError:
        print("PyYAML is required: pip install pyyaml", file=sys.stderr)
        sys.exit(2)
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        error(path, "missing YAML frontmatter")
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        error(path, f"frontmatter is not valid YAML: {exc}")
        return None
    return data, match.group(2)


def check_skill(skill_dir: Path, version: str) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        error(skill_dir, "missing SKILL.md")
        return
    parsed = parse_frontmatter(skill_md)
    if parsed is None:
        return
    frontmatter, body = parsed

    unknown = set(frontmatter) - ALLOWED_FRONTMATTER_KEYS
    if unknown:
        error(skill_md, f"frontmatter keys outside the Agent Skills spec: {sorted(unknown)}")

    name = frontmatter.get("name")
    if name != skill_dir.name:
        error(skill_md, f"name {name!r} does not match folder {skill_dir.name!r}")
    if not isinstance(name, str) or not NAME_PATTERN.match(name) or len(name) > 64:
        error(skill_md, f"name {name!r} is not lowercase-hyphenated or exceeds 64 characters")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        error(skill_md, "description is missing")
    else:
        if len(description) > 1024:
            error(skill_md, f"description is {len(description)} characters (max 1024)")
        for marker in ("Use when", "NOT for"):
            if marker not in description:
                error(skill_md, f"description has no '{marker}' section")

    metadata = frontmatter.get("metadata") or {}
    if not isinstance(metadata, dict) or str(metadata.get("version")) != version:
        error(skill_md, f"metadata.version {metadata.get('version') if isinstance(metadata, dict) else None!r} != VERSION {version!r}")
    if isinstance(metadata, dict) and any(not isinstance(v, str) for v in metadata.values()):
        error(skill_md, "metadata values must be strings (quote them)")

    line_count = skill_md.read_text().count("\n") + 1
    if line_count > HARD_LINE_LIMIT:
        error(skill_md, f"{line_count} lines (hard limit {HARD_LINE_LIMIT})")
    elif line_count > SOFT_LINE_LIMIT:
        warn(skill_md, f"{line_count} lines (aim for under {SOFT_LINE_LIMIT})")

    references_dir = skill_dir / "references"
    linked = set(re.findall(r"references/([A-Za-z0-9_.\-/]+\.md)", body))
    for ref in sorted(linked):
        if not (references_dir / ref).is_file():
            error(skill_md, f"links references/{ref}, which does not exist")
    if references_dir.is_dir():
        for ref_file in sorted(references_dir.rglob("*.md")):
            ref = str(ref_file.relative_to(references_dir))
            if ref not in linked:
                error(ref_file, f"not linked from {relative(skill_md)}")
            if "## Sources" not in ref_file.read_text():
                error(ref_file, "has no '## Sources' section")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.is_file():
        error(skill_dir, "missing agents/openai.yaml")
    elif f"${skill_dir.name}" not in openai_yaml.read_text():
        error(openai_yaml, f"default_prompt does not mention ${skill_dir.name}")

    for md_file in [skill_md, *sorted(skill_dir.rglob("references/*.md"))]:
        text = md_file.read_text()
        if re.search(r"(^|[^./])\.\./", text):
            error(md_file, "contains a ../ path; skills must be self-contained")
        if md_file in BANNED_EXEMPT_FILES:
            continue
        exempt = set()
        for directory, patterns in BANNED_EXEMPT_PATTERNS_BY_DIR.items():
            if directory in md_file.parents:
                exempt |= patterns
        for pattern in BANNED_PATTERNS:
            if pattern in exempt:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if pattern in line:
                    error(f"{relative(md_file)}:{line_number}", f"banned stale pattern {pattern!r}")


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        error(path, "missing")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        error(path, f"invalid JSON: {exc}")
        return None


def check_manifests(version: str, skill_names: list[str]) -> None:
    for manifest_path, get_version, get_name in MANIFESTS:
        path = ROOT / manifest_path
        data = load_json(path)
        if data is None:
            continue
        try:
            manifest_version, manifest_name = get_version(data), get_name(data)
        except (KeyError, IndexError):
            error(path, "has no name or version field")
            continue
        if manifest_version != version:
            error(path, f"version {manifest_version!r} != VERSION {version!r}")
        if manifest_name != PLUGIN_NAME:
            error(path, f"name {manifest_name!r} != {PLUGIN_NAME!r}")

    claude_mcp, portable_mcp = load_json(ROOT / ".mcp.json"), load_json(ROOT / "mcp.json")
    if claude_mcp is None or portable_mcp is None:
        return
    if claude_mcp != portable_mcp:
        error(ROOT / "mcp.json", "differs from .mcp.json; every client must get the same servers")
    servers = claude_mcp.get("mcpServers", {})
    if list(servers) != ["whop"]:
        error(ROOT / ".mcp.json", f"must define exactly one server named 'whop', found {list(servers)}")
        return
    server = servers["whop"]
    if server.get("headers", {}).get("X-Whop-Plugin") != f"skills/{version}":
        error(ROOT / ".mcp.json", f"X-Whop-Plugin header must be 'skills/{version}'")
    gemini = load_json(ROOT / "gemini-extension.json") or {}
    gemini_server = gemini.get("mcpServers", {}).get("whop", {})
    if gemini_server.get("httpUrl") != server.get("url") or gemini_server.get("headers") != server.get("headers"):
        error(ROOT / "gemini-extension.json", "mcpServers.whop must match .mcp.json (httpUrl = url, same headers)")

    portable = load_json(ROOT / "plugin.json") or {}
    codex = load_json(ROOT / ".codex-plugin/plugin.json") or {}
    openai_interface = portable.get("extensions", {}).get("com.openai", {}).get("interface")
    if codex.get("interface") != openai_interface:
        error(ROOT / ".codex-plugin/plugin.json", "interface must equal plugin.json extensions.com.openai.interface")
    for key in ("description", "author", "homepage", "repository", "license", "keywords"):
        if codex.get(key) != portable.get(key):
            error(ROOT / ".codex-plugin/plugin.json", f"{key} must match plugin.json")
    for key, target in (("skills", "skills"), ("mcpServers", ".mcp.json")):
        if not (ROOT / str(codex.get(key, ""))).resolve() == (ROOT / target).resolve():
            error(ROOT / ".codex-plugin/plugin.json", f"{key} must point to ./{target}")

    readme = (ROOT / "README.md").read_text() if (ROOT / "README.md").is_file() else ""
    for name in skill_names:
        if f"skills/{name}" not in readme:
            error("README.md", f"skills table does not link skills/{name}")


def check_no_symlinks() -> None:
    ignored = {".git", "node_modules", ".venv", ".snippets"}
    for path in ROOT.rglob("*"):
        if path.is_symlink() and not ignored & set(path.relative_to(ROOT).parts):
            error(path, "is a symlink; installers copy it as an absolute path, so use a regular file")


def main() -> int:
    version = (ROOT / "VERSION").read_text().strip()
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        error(SKILLS_DIR, "no skills found")
    for skill_dir in skill_dirs:
        check_skill(skill_dir, version)
    check_manifests(version, [p.name for p in skill_dirs])
    check_no_symlinks()

    for message in warnings:
        print(f"warning  {message}")
    for message in errors:
        print(f"error    {message}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: {len(skill_dirs)} skills, version {version}, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
