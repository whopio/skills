#!/usr/bin/env python3
"""Refresh scripts/mcp-tools.json: the tools the plugin's MCP route exposes.

The plugin connects to https://mcp.whop.com/claude/mcp, the `claude_directory`
surface of github.com/whopio/whop-mcp-server. Skills name these tools, so
scripts/validate.py checks every name against this list.

The Sync MCP tools workflow runs this daily. By hand:

    git clone --depth 1 https://github.com/whopio/whop-mcp-server /tmp/whop-mcp-server
    cd /tmp/whop-mcp-server && corepack enable && pnpm install --frozen-lockfile
    cd packages/server
    pnpm exec tsx scripts/generate-registry.ts --summary > /tmp/summary.txt
    pnpm exec tsx scripts/generate-registry.ts            # writes generated/manifest.json
    python3 scripts/sync-mcp-tools.py /tmp/whop-mcp-server /tmp/summary.txt --report /tmp/report.md

The tool list is rewritten only when the tools changed, so a new server commit
with the same tools leaves the repo untouched.

With generated/manifest.json present it also rewrites every evals/**/mocks/whop/_tools.json:
the tools/list entries (schemas and descriptions) for every mocked tool, built
the way packages/server/src/runtime/server.ts builds them on the hosted server, so
eval runs see the real tool contract.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# WHOP_SKILLS_ROOT points the script at another copy of this repo (the tests use it).
ROOT = Path(os.environ.get("WHOP_SKILLS_ROOT") or Path(__file__).resolve().parent.parent)
OUTPUT = ROOT / "scripts" / "mcp-tools.json"
EVALS = ROOT / "evals"
# Tools the server adds itself, outside the OpenAPI registry: each comes from a
# runtime module and is switched on by an option the hosted worker passes
# (apps/worker/src/mcp-handler.ts). connection_status is always on.
BUILTIN_MODULES = {
    "server.ts": None,
    "feedback.ts": "feedbackSink",
    "docs.ts": "docs",
    "chatgpt-compat.ts": "chatGptCompat",
}
BUILTIN_FLAGS = {"report_feedback": "local", "ask_question": "local"}


def builtin_tools(repo: Path) -> dict[str, str]:
    runtime = repo / "packages/server/src/runtime"
    handler = (repo / "apps/worker/src/mcp-handler.ts").read_text()
    tools: dict[str, str] = {}
    for module, option in BUILTIN_MODULES.items():
        path = runtime / module
        if not path.is_file():
            continue
        if option and not re.search(rf"\b{option}\s*:", handler):
            continue
        if option in ("docs", "chatGptCompat") and not re.search(rf"\b{option}\s*:\s*true\b", handler):
            continue
        text = path.read_text()
        if module == "server.ts":
            names = ["connection_status"] if '"connection_status"' in text else []
        else:
            names = re.findall(r'^\s*name:\s*"([a-z_]+)",', text, re.MULTILINE)
        for name in names:
            tools[name] = BUILTIN_FLAGS.get(name, "read_only")
    if "connection_status" not in tools:
        raise SystemExit("connection_status not found in runtime/server.ts; the server changed shape")
    return tools


UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"


def tool_definition(op: dict) -> dict:
    """Mirror toolInputSchema + withIntentContext + toolDescription in runtime/server.ts."""
    safety = op["safety"]
    schema = json.loads(json.dumps(op["inputSchema"]))
    properties = schema.setdefault("properties", {})
    if safety["confirmationRequired"] or safety["idempotency"] != "none":
        properties["idempotency_key"] = {
            "type": "string",
            "description": (
                "Caller-chosen stable retry key. Reuse the same key when retrying after a timeout or error. The native API replays completed requests and rejects requests still in flight."
                if op["surface"] == "native" and op["method"] == "post"
                else "Caller-chosen stable key forwarded to the API. Reuse the same key when retrying, but verify the operation outcome after an ambiguous error."
            ),
        }
    properties["intent"] = {"type": "string", "minLength": 1, "pattern": "\\S", "description": "The original user request that led to this tool call. Copy it verbatim when available."}
    properties["intent_id"] = {
        "type": "string", "format": "uuid", "minLength": 36, "maxLength": 36, "pattern": UUID_PATTERN,
        "description": "A UUID for the user turn that caused this call. Generate it once per user message and reuse it for every tool call made to fulfill that message. Never derive it from the intent text.",
    }
    schema["required"] = list(dict.fromkeys([*schema.get("required", []), "intent", "intent_id"]))
    annotations = {key: op["annotations"].get(key) for key in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")}
    return {
        "name": op["toolName"],
        "description": op.get("description") or op.get("summary") or "",
        "inputSchema": schema,
        "annotations": {**annotations, "title": op.get("summary")},
    }


CONNECTION_STATUS = {
    "name": "connection_status",
    "description": "Returns safe diagnostics for this connection: authenticated identity, selected account, permission profile, scopes, tool coverage, and build metadata. Never returns credentials.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    "annotations": {"readOnlyHint": True},
}


# Built-in docs tools, copied from packages/server/src/runtime/docs.ts.
DOCS_ANNOTATIONS = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
DOCS_SEARCH = {
    "name": "docs_search",
    "description": "Search the Whop documentation at docs.whop.com: guides, API reference, webhooks, SDKs, and product help. Returns matching excerpts with page paths and links. Use it for how-to and concept questions, or to learn a field or endpoint before calling an operation tool. Read a full page with docs_query.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 1, "maxLength": 1000, "pattern": "\\S", "description": "What to look for, in plain words."},
            "version": {"type": "string", "minLength": 1, "maxLength": 50, "pattern": "\\S", "description": "Restrict results to one documentation version. Omit to search the current docs."},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "annotations": {**DOCS_ANNOTATIONS, "title": "Search Whop docs"},
}
DOCS_QUERY = {
    "name": "docs_query",
    "description": "Run a read-only, shell-style command against a virtual filesystem that holds only the Whop documentation pages. It is not a shell on any real machine. Use ls or tree to explore, rg for exact matches, and head or cat to read a page that docs_search returned (append .mdx to its path). Example: head -100 /developer/guides/ai_and_mcp.mdx. Cite pages at https://docs.whop.com without the .mdx extension.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "minLength": 1, "maxLength": 1000, "pattern": "\\S", "description": 'The command to run, for example `tree / -L 2`, `rg -il "webhook" /developer`, or `head -80 /payments/overview.mdx`.'},
        },
        "required": ["command"],
        "additionalProperties": False,
    },
    "annotations": {**DOCS_ANNOTATIONS, "title": "Read Whop docs"},
}
BUILTIN_DEFINITIONS = {"connection_status": None, "docs_search": DOCS_SEARCH, "docs_query": DOCS_QUERY}


def write_mock_tools(repo: Path) -> tuple[list[str], list[str]]:
    """Rewrite each mocks/whop/_tools.json. Return (files that changed, mocks of tools the server no longer has)."""
    manifest_path = repo / "packages/server/generated/manifest.json"
    if not manifest_path.is_file():
        return [], []
    changed: list[str] = []
    orphaned: list[str] = []
    operations = {op["toolName"]: op for op in json.loads(manifest_path.read_text())["operations"]}
    # The shared mocks and any case's own mocks/whop/ folder.
    for mocks in sorted(EVALS.glob("**/mocks/whop")):
        if "results" in mocks.parts:
            continue
        tools = []
        available = builtin_tools(repo)
        for name in sorted(p.stem for p in mocks.glob("*.md") if not p.stem.startswith("_")):
            if name == "connection_status":
                tools.append(CONNECTION_STATUS)
            elif name in BUILTIN_DEFINITIONS and name in available:
                tools.append(BUILTIN_DEFINITIONS[name])
            elif name in operations:
                tools.append(tool_definition(operations[name]))
            else:
                orphaned.append(f"{(mocks / name).relative_to(ROOT)}.md")
        target = mocks / "_tools.json"
        content = json.dumps({"tools": tools}, indent=2, ensure_ascii=False) + "\n"
        if not target.is_file() or target.read_text() != content:
            target.write_text(content)
            changed.append(str(target.relative_to(ROOT)))
            print(f"Wrote {len(tools)} tool definitions to {target.relative_to(ROOT)}")
    return changed, orphaned


def group(name: str) -> str:
    return name.split("_", 1)[0]


def report(previous: dict, tools: dict, source: str, api_version: str | None, mocks_changed: list[str], orphaned: list[str]) -> str:
    added = sorted(set(tools) - set(previous))
    removed = sorted(set(previous) - set(tools))
    reflagged = sorted(name for name in set(tools) & set(previous) if tools[name] != previous[name])
    lines = [f"Source: {source} (API version {api_version or 'unknown'}), surface `claude_directory` (`https://mcp.whop.com/claude/mcp`).", ""]
    if not (added or removed or reflagged or mocks_changed or orphaned):
        return "\n".join(lines + ["No tool or schema changes."]) + "\n"
    lines.append(f"**{len(tools)} tools** ({len(added)} added, {len(removed)} removed, {len(reflagged)} with new safety flags).")
    for title, names, describe in (
        ("Added", added, lambda n: tools[n]),
        ("Removed", removed, lambda n: previous[n]),
        ("Safety flags changed", reflagged, lambda n: f"{previous[n]} -> {tools[n]}"),
    ):
        if names:
            lines += ["", f"### {title}", ""] + [f"- `{n}` ({describe(n)})" for n in names]
    if mocks_changed:
        lines += ["", "### Eval mock schemas updated", ""] + [f"- `{path}`" for path in mocks_changed]
    if orphaned:
        lines += ["", "### Eval mocks for tools the server no longer has", ""] + [f"- `{path}`" for path in orphaned]
        lines += ["", "Those eval cases can't run as written: move them to the replacement tool or delete them."]
    if removed:
        lines += ["", "A removed tool that a skill, command or subagent still names fails `validate.py` on this PR. Replace or drop the mention."]
    if added:
        lines += ["", "Check whether a skill should mention any added tool; `validate.py` can't tell."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", type=Path, help="a whop-mcp-server checkout")
    parser.add_argument("summary", type=Path, help="output of generate-registry.ts --summary")
    parser.add_argument("--report", type=Path, help="write a Markdown summary of the changes here")
    args = parser.parse_args()
    repo, summary = args.repo, args.summary
    surfaces = (repo / "packages/server/src/policy/surfaces.ts").read_text()
    block = surfaces[surfaces.index("CLAUDE_DIRECTORY_EXCLUSIONS") :]
    excluded = set(re.findall(r'\[\s*"((?:GET|POST|PATCH|PUT|DELETE) [^"]+)"', block))
    if not excluded:
        raise SystemExit("found no claude_directory exclusions; surfaces.ts changed shape")

    tools = {}
    for line in summary.read_text().splitlines():
        match = re.match(r"^(\S+)\s+(GET|POST|PATCH|PUT|DELETE) (\S+)\s+\[\w+\]\s+(\S+)$", line)
        if not match:
            continue
        name, method, path, flags = match.groups()
        if f"{method} {path}" in excluded:
            continue
        tools[name] = flags
    if len(tools) < 100:
        raise SystemExit(f"only {len(tools)} tools parsed; is {summary} a --summary output?")
    tools.update(builtin_tools(repo))
    tools = dict(sorted(tools.items()))

    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    source = f"https://github.com/whopio/whop-mcp-server/tree/{commit}"
    api_version = re.search(r"API version (\S+?),", summary.read_text())
    api_version = api_version.group(1) if api_version else None
    previous_file = json.loads(OUTPUT.read_text()) if OUTPUT.is_file() else {}
    previous = previous_file.get("tools", {})
    # Groups seen in any sync so far. validate.py checks names in these groups,
    # so a skill still naming a tool from a group the server dropped entirely
    # (all of docs_*, say) fails instead of slipping through.
    known_groups = sorted(
        set(previous_file.get("knownGroups", [])) | {group(n) for n in [*previous, *tools] if "_" in n}
    )

    # Rewrite only when the tool list changed, so a new server commit with the
    # same tools doesn't produce a diff (or a sync PR). `source` is the last
    # commit whose tool list changed.
    if tools != previous or known_groups != previous_file.get("knownGroups"):
        OUTPUT.write_text(
            json.dumps(
                {
                    "$comment": "Generated by scripts/sync-mcp-tools.py. Tool -> safety flags (read_only, mutating, destructive; financial, credential; confirm = the server flags it as needing the user's approval; hooks/confirm-whop-execution.mjs asks before it runs).",
                    "source": source,
                    "surface": "claude_directory (https://mcp.whop.com/claude/mcp)",
                    "apiVersion": api_version,
                    "knownGroups": known_groups,
                    "tools": tools,
                },
                indent=2,
            )
            + "\n"
        )
        print(f"Wrote {len(tools)} tools to {OUTPUT.relative_to(ROOT)} ({len(excluded)} excluded on this surface)")
    else:
        print(f"{len(tools)} tools, unchanged")
    mocks_changed, orphaned = write_mock_tools(repo)
    for path in orphaned:
        print(f"warning: {path} mocks a tool the server doesn't have", file=sys.stderr)
    if args.report:
        args.report.write_text(report(previous, tools, source, api_version, mocks_changed, orphaned))
    return 0


if __name__ == "__main__":
    sys.exit(main())
