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

PATTERNS_FILE = ROOT / "hooks" / "patterns.json"
# The banned-in-docs list is every `literal` in hooks/patterns.json, which the
# edit hook also uses, so docs and agent-written code are held to the same names.
BANNED_PATTERNS = [
    literal
    for entry in json.loads(PATTERNS_FILE.read_text())["patterns"]
    for literal in entry.get("literal", [])
]
BANNED_EXEMPT_FILES = {SKILLS_DIR / "whop-migrate" / "references" / "legacy-map.md"}
BANNED_EXEMPT_PATTERNS_BY_DIR = {
    SKILLS_DIR / "whop-communities": {"@whop/embedded-components"},
}

COMMANDS_DIR = ROOT / "commands"
# Not agents/: Gemini CLI and Antigravity always load that folder and reject
# Claude-format agent files, so the manifests point here explicitly.
AGENTS_DIR = ROOT / "subagents"
CLAUDE_HOOKS = ROOT / "hooks" / "claude-hooks.json"
AGENT_TOOLS = {"Read", "Grep", "Glob", "Bash", "Edit", "Write", "MultiEdit", "Skill", "WebFetch", "WebSearch", "Agent"}

PLUGIN_NAME = "whop-developer"
MANIFESTS = [
    ("plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".claude-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".claude-plugin/marketplace.json", lambda d: d["plugins"][0]["version"], lambda d: d["plugins"][0]["name"]),
    (".codex-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".cursor-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".grok-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".kimi-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
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

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        for script in sorted(p for p in scripts_dir.rglob("*") if p.is_file()):
            rel = str(script.relative_to(skill_dir))
            if rel not in body:
                error(script, f"not mentioned in {relative(skill_md)}")

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


AGENT_PLUGINS_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
AGENT_PLUGINS_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
# Agent Plugins 1.0 manifests are closed (spec section 5.2): only these keys.
AGENT_PLUGINS_KEYS = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions"}
# The one MCP entry each host reads, and the X-Whop-Plugin suffix that tells
# Whop which host a connection came from.
MCP_HOST_SUFFIX = {
    ".mcp.json": "",  # Claude Code, Codex, Cursor, Grok
    "mcp.json": " (agent-plugins)",  # Copilot CLI, VS Code and other Agent Plugins hosts
    "gemini-extension.json": " (gemini)",
    ".kimi-plugin/plugin.json": " (kimi)",
}


def plugin_header(version: str, path: str) -> str:
    return f"skills/{version}{MCP_HOST_SUFFIX[path]}"


def check_mcp_configs(version: str) -> None:
    claude = load_json(ROOT / ".mcp.json")
    if claude is None:
        return
    servers = claude.get("mcpServers", {})
    if list(servers) != ["whop"]:
        error(ROOT / ".mcp.json", f"must define exactly one server named 'whop', found {list(servers)}")
        return
    url = servers["whop"].get("url")
    if servers["whop"].get("type") != "http" or not isinstance(url, str) or not url.startswith("https://"):
        error(ROOT / ".mcp.json", "whop must be {type: http, url: https://...}")

    def expect_server(path: str, server: dict, url_key: str, extra: dict) -> None:
        if server.get(url_key) != url:
            error(ROOT / path, f"whop.{url_key} must equal .mcp.json's url {url!r}")
        if server.get("headers") != {"X-Whop-Plugin": plugin_header(version, path)}:
            error(ROOT / path, f"whop.headers must be exactly {{'X-Whop-Plugin': {plugin_header(version, path)!r}}}")
        for key, value in extra.items():
            if server.get(key) != value:
                error(ROOT / path, f"whop.{key} must be {value!r}")
        allowed = {url_key, "headers", *extra}
        if set(server) - allowed:
            error(ROOT / path, f"whop has unexpected keys {sorted(set(server) - allowed)}")

    expect_server(".mcp.json", servers["whop"], "url", {"type": "http"})

    # Agent Plugins 1.0 (Copilot CLI, VS Code): closed schema, streamable-http.
    portable = load_json(ROOT / "mcp.json")
    if portable is not None:
        if set(portable) != {"$schema", "mcpServers"} or portable.get("$schema") != AGENT_PLUGINS_MCP_SCHEMA:
            error(ROOT / "mcp.json", f"must be exactly {{$schema: {AGENT_PLUGINS_MCP_SCHEMA}, mcpServers}} (Agent Plugins 1.0)")
        portable_servers = portable.get("mcpServers", {})
        if list(portable_servers) != ["whop"]:
            error(ROOT / "mcp.json", f"must define exactly one server named 'whop', found {list(portable_servers)}")
        else:
            expect_server("mcp.json", portable_servers["whop"], "url", {"type": "streamable-http"})

    gemini = (load_json(ROOT / "gemini-extension.json") or {}).get("mcpServers", {})
    if list(gemini) != ["whop"]:
        error(ROOT / "gemini-extension.json", "must define exactly one MCP server named 'whop'")
    else:
        expect_server("gemini-extension.json", gemini["whop"], "httpUrl", {})

    kimi = load_json(ROOT / ".kimi-plugin/plugin.json") or {}
    kimi_servers = kimi.get("mcpServers", {})
    if not isinstance(kimi_servers, dict) or list(kimi_servers) != ["whop"]:
        error(ROOT / ".kimi-plugin/plugin.json", "mcpServers must be inline (Kimi doesn't resolve file paths) with one server named 'whop'")
    else:
        # Kimi's documented remote form: a url with no `transport` is HTTP.
        expect_server(".kimi-plugin/plugin.json", kimi_servers["whop"], "url", {})
    if not re.match(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$", str(kimi.get("name", ""))):
        error(ROOT / ".kimi-plugin/plugin.json", "name must match Kimi's plugin id pattern")
    for key in ("skills", "commands", "agents"):
        value = kimi.get(key)
        if not isinstance(value, str) or not value.startswith("./") or not (ROOT / value).is_dir():
            error(ROOT / ".kimi-plugin/plugin.json", f"{key} must be a ./ path to an existing directory")

    root_manifest = load_json(ROOT / "plugin.json") or {}
    if root_manifest.get("$schema") != AGENT_PLUGINS_PLUGIN_SCHEMA:
        error(ROOT / "plugin.json", f"$schema must be {AGENT_PLUGINS_PLUGIN_SCHEMA}, matching mcp.json's version")
    if set(root_manifest) - AGENT_PLUGINS_KEYS:
        error(ROOT / "plugin.json", f"Agent Plugins 1.0 manifests are closed; remove {sorted(set(root_manifest) - AGENT_PLUGINS_KEYS)}")
    name = str(root_manifest.get("name", ""))
    if not re.match(r"^[a-z0-9]([a-z0-9.-]{0,62}[a-z0-9])?$", name) or "--" in name or ".." in name:
        error(ROOT / "plugin.json", "name breaks the Agent Plugins name rules")

    cursor = load_json(ROOT / ".cursor-plugin/plugin.json") or {}
    if cursor.get("mcpServers") != "./.mcp.json":
        error(ROOT / ".cursor-plugin/plugin.json", "mcpServers must be ./.mcp.json (Cursor's format; mcp.json is the Agent Plugins format)")

    # Every host listing shows the same pitch (Gemini's manifest keeps its own shorter one).
    for path in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json", ".grok-plugin/plugin.json", ".kimi-plugin/plugin.json"):
        data = load_json(ROOT / path) or {}
        if data.get("description") != root_manifest.get("description"):
            error(ROOT / path, "description must match plugin.json")


MCP_TOOLS_FILE = ROOT / "scripts" / "mcp-tools.json"
# API enum values that look like tool names.
NOT_MCP_TOOLS = {"payouts_portal", "members_only"}


def check_mcp_tool_names() -> None:
    """Every MCP tool a skill, command or subagent names must exist on the plugin's route."""
    data = load_json(MCP_TOOLS_FILE)
    if data is None:
        return
    tools = set(data.get("tools", {}))
    # A token counts as a tool name when its first segment is a tool group,
    # including groups the server has since dropped (knownGroups).
    groups = {name.split("_", 1)[0] for name in tools if "_" in name} | set(data.get("knownGroups", []))
    for mock in sorted((ROOT / "evals").glob("**/mocks/whop/*.md")):
        if "results" not in mock.parts and mock.stem not in tools:
            error(mock, f"mocks MCP tool {mock.stem!r}, which isn't on the plugin's MCP route (scripts/mcp-tools.json)")
    files = [*SKILLS_DIR.rglob("*.md"), *COMMANDS_DIR.glob("*.md"), *AGENTS_DIR.glob("*.md"), ROOT / "hooks" / "session-start.mjs"]

    for path in files:
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            for token in re.findall(r"`([a-z][a-z-]*_[a-z][a-z_-]*)`", line):
                if token.split("_", 1)[0] in groups and token not in tools and token not in NOT_MCP_TOOLS:
                    error(f"{relative(path)}:{line_number}", f"MCP tool {token!r} isn't on the plugin's MCP route (scripts/mcp-tools.json)")


def check_gemini_commands() -> None:
    import subprocess

    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build-gemini-commands.py"), "--check"], capture_output=True, text=True)
    if result.returncode != 0:
        for line in result.stdout.strip().splitlines() or ["Gemini commands are out of date"]:
            error(ROOT / "commands" / "whop-developer", line)


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

    check_mcp_configs(version)

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


def check_patterns(skill_names: list[str]) -> None:
    data = load_json(PATTERNS_FILE)
    if data is None:
        return
    seen: set[str] = set()
    for entry in data.get("patterns", []):
        entry_id = entry.get("id")
        where = f"{relative(PATTERNS_FILE)} ({entry_id})"
        if not entry_id or entry_id in seen:
            error(where, "every pattern needs a unique id")
        seen.add(entry_id)
        for key in ("regex", "fix", "skill"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                error(where, f"missing {key}")
        if entry.get("skill") not in skill_names:
            error(where, f"skill {entry.get('skill')!r} is not a skill in this repo")
        if not isinstance(entry.get("literal", []), list):
            error(where, "literal must be a list of strings")
        if entry.get("severity") not in (None, "security"):
            error(where, "severity must be omitted or 'security'")


def check_plugin_extras(skill_names: list[str]) -> None:
    commands = sorted(COMMANDS_DIR.glob("*.md")) if COMMANDS_DIR.is_dir() else []
    agents = sorted(AGENTS_DIR.glob("*.md")) if AGENTS_DIR.is_dir() else []
    readme = (ROOT / "README.md").read_text() if (ROOT / "README.md").is_file() else ""

    for command in commands:
        parsed = parse_frontmatter(command)
        if parsed is None:
            continue
        frontmatter, body = parsed
        if not isinstance(frontmatter.get("description"), str) or not frontmatter["description"].strip():
            error(command, "description is missing")
        if "name" in frontmatter:
            error(command, "commands take their name from the file name; remove `name`")
        if f"/{PLUGIN_NAME}:{command.stem}" not in readme:
            error("README.md", f"does not document /{PLUGIN_NAME}:{command.stem}")
        for skill in re.findall(r"`(whop-[a-z-]+)` skill", body):
            if skill not in skill_names:
                error(command, f"names skill {skill!r}, which does not exist")

    for agent in agents:
        parsed = parse_frontmatter(agent)
        if parsed is None:
            continue
        frontmatter, _ = parsed
        if frontmatter.get("name") != agent.stem:
            error(agent, f"name {frontmatter.get('name')!r} must equal the file name {agent.stem!r}")
        if not isinstance(frontmatter.get("description"), str) or not frontmatter["description"].strip():
            error(agent, "description is missing")
        tools = [t.strip() for t in str(frontmatter.get("tools", "")).split(",") if t.strip()]
        unknown_tools = set(tools) - AGENT_TOOLS
        if unknown_tools:
            error(agent, f"unknown tools {sorted(unknown_tools)}")
        for skill in frontmatter.get("skills") or []:
            if skill not in skill_names:
                error(agent, f"preloads skill {skill!r}, which does not exist")
        if f"`{agent.stem}`" not in readme:
            error("README.md", f"does not document the {agent.stem} subagent")

    hooks = load_json(CLAUDE_HOOKS)
    if hooks is not None:
        for event, groups in hooks.get("hooks", {}).items():
            for group in groups:
                for hook in group.get("hooks", []):
                    for script in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"' ]+)", hook.get("command", "")):
                        if not (ROOT / script).is_file():
                            error(CLAUDE_HOOKS, f"{event} hook runs {script}, which does not exist")
                    if not isinstance(hook.get("timeout"), (int, float)):
                        error(CLAUDE_HOOKS, f"{event} hook needs a timeout (seconds)")
    claude_manifest = load_json(ROOT / ".claude-plugin/plugin.json") or {}
    if claude_manifest.get("hooks") != "./hooks/claude-hooks.json":
        error(ROOT / ".claude-plugin/plugin.json", "hooks must point to ./hooks/claude-hooks.json")
    agent_paths = [f"./subagents/{agent.name}" for agent in agents]
    for manifest in (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"):
        if (load_json(ROOT / manifest) or {}).get("agents") != agent_paths:
            error(ROOT / manifest, f"agents must list every subagent file: {agent_paths}")
    if (ROOT / "agents").exists():
        error(ROOT / "agents", "Gemini CLI and Antigravity auto-load agents/ and reject Claude-format agents; keep them in subagents/")
    if (ROOT / "hooks" / "hooks.json").exists():
        error(ROOT / "hooks" / "hooks.json", "Cursor auto-loads this path with its own hook format; keep Claude hooks in claude-hooks.json")



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
    skill_names = [p.name for p in skill_dirs]
    check_manifests(version, skill_names)
    check_patterns(skill_names)
    check_plugin_extras(skill_names)
    check_gemini_commands()
    check_mcp_tool_names()
    check_no_symlinks()

    for message in warnings:
        print(f"warning  {message}")
    for message in errors:
        print(f"error    {message}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    extras = len(list(COMMANDS_DIR.glob("*.md"))), len(list(AGENTS_DIR.glob("*.md")))
    print(f"OK: {len(skill_dirs)} skills, {extras[0]} commands, {extras[1]} agents, version {version}, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
