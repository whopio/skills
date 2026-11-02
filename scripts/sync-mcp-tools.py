#!/usr/bin/env python3
"""Refresh scripts/mcp-tools.json: the tools the plugin's MCP route exposes.

The plugin connects to https://mcp.whop.com/claude/mcp, the `claude_directory`
surface of github.com/whopio/whop-mcp-server. Skills name these tools, so
scripts/validate.py checks every name against this list.

    git clone --depth 1 https://github.com/whopio/whop-mcp-server /tmp/whop-mcp-server
    cd /tmp/whop-mcp-server/packages/server && pnpm install   # or: npm i yaml tsx
    npx tsx scripts/generate-registry.ts --summary > /tmp/summary.txt
    npx tsx scripts/generate-registry.ts                  # writes generated/manifest.json
    python3 scripts/sync-mcp-tools.py /tmp/whop-mcp-server /tmp/summary.txt

With generated/manifest.json present it also rewrites every evals/**/mocks/whop/_tools.json:
the tools/list entries (schemas and descriptions) for every mocked tool, built
the way packages/server/src/runtime/server.ts builds them on the hosted server
(prepare-and-confirm enforced), so eval runs see the real tool contract.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "scripts" / "mcp-tools.json"
EVALS = ROOT / "evals"
# Tools the server adds itself, outside the OpenAPI registry
# (packages/server/src/runtime/{server,feedback,docs}.ts).
LOCAL_TOOLS = {
    "connection_status": "read_only",
    "report_feedback": "local",
    "ask_question": "local",
    "docs_search": "read_only",
    "docs_query": "read_only",
}


UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
TWO_STEP = (
    "Two-step tool. Without mcp_confirmation_token, calling it is a SAFE PREVIEW: nothing executes, no money moves, "
    "no data changes \u2014 it returns exactly what would happen plus a confirmation token. Show that preview to the user. "
    "Executing is the user's decision, not yours: call again with the token once they approve, in the moment or through "
    "standing permission they have given you."
)


def tool_definition(op: dict) -> dict:
    """Mirror toolInputSchema + withIntentContext + toolDescription (enforced confirmation)."""
    safety = op["safety"]
    schema = json.loads(json.dumps(op["inputSchema"]))
    properties = schema.setdefault("properties", {})
    confirmed = safety["confirmationRequired"]
    upstream_replay = op["surface"] == "native" and op["method"] == "post"
    if confirmed:
        properties["mcp_confirmation_token"] = {
            "type": "string",
            "description": "Leave unset on the first call to prepare this operation and receive a confirmation token. Pass the token back, after the user approves, to execute.",
        }
    if confirmed or safety["idempotency"] != "none":
        if upstream_replay:
            text = (
                "Caller-chosen stable retry key. Required when executing with a confirmation token; reuse the same key when retrying. The native API replays completed requests and rejects requests still in flight."
                if confirmed
                else "Caller-chosen stable retry key. Reuse the same key when retrying after a timeout or error. The native API replays completed requests and rejects requests still in flight."
            )
        else:
            text = (
                "Caller-chosen stable key for local replay and conflict detection. Required when executing with a confirmation token; reuse the same key when retrying. If the outcome is reported as unknown, verify the effect instead of executing again."
                if confirmed
                else "Caller-chosen stable key forwarded to the API. Reuse the same key when retrying, but verify the operation outcome after an ambiguous error."
            )
        properties["idempotency_key"] = {"type": "string", "description": text}
    properties["intent"] = {"type": "string", "minLength": 1, "pattern": "\\S", "description": "The original user request that led to this tool call. Copy it verbatim when available."}
    properties["intent_id"] = {
        "type": "string", "format": "uuid", "minLength": 36, "maxLength": 36, "pattern": UUID_PATTERN,
        "description": "A UUID for the user turn that caused this call. Generate it once per user message and reuse it for every tool call made to fulfill that message. Never derive it from the intent text.",
    }
    schema["required"] = list(dict.fromkeys([*schema.get("required", []), "intent", "intent_id"]))
    description = op.get("description") or op.get("summary") or ""
    if confirmed:
        description = f"{description}\n\n{TWO_STEP}" if description else TWO_STEP
    return {"name": op["toolName"], "description": description, "inputSchema": schema, "annotations": {**op["annotations"], "title": op.get("summary")}}


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


def write_mock_tools(repo: Path) -> None:
    manifest_path = repo / "packages/server/generated/manifest.json"
    if not manifest_path.is_file():
        return
    operations = {op["toolName"]: op for op in json.loads(manifest_path.read_text())["operations"]}
    # The shared mocks and any case's own mocks/whop/ folder.
    for mocks in sorted(EVALS.glob("**/mocks/whop")):
        if "results" in mocks.parts:
            continue
        tools = []
        for name in sorted(p.stem for p in mocks.glob("*.md") if not p.stem.startswith("_")):
            if name == "connection_status":
                tools.append(CONNECTION_STATUS)
            elif name in BUILTIN_DEFINITIONS:
                tools.append(BUILTIN_DEFINITIONS[name])
            elif name in operations:
                tools.append(tool_definition(operations[name]))
            else:
                raise SystemExit(f"{(mocks / name).relative_to(ROOT)}.md mocks a tool the server doesn't have")
        (mocks / "_tools.json").write_text(json.dumps({"tools": tools}, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {len(tools)} tool definitions to {(mocks / '_tools.json').relative_to(ROOT)}")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    repo, summary = Path(sys.argv[1]), Path(sys.argv[2])
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
    tools.update(LOCAL_TOOLS)

    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    api_version = re.search(r"API version (\S+?),", summary.read_text())
    OUTPUT.write_text(
        json.dumps(
            {
                "$comment": "Generated by scripts/sync-mcp-tools.py. Tool -> safety flags (read_only, mutating, destructive; financial, credential; confirm = prepare-and-confirm).",
                "source": f"https://github.com/whopio/whop-mcp-server/tree/{commit}",
                "surface": "claude_directory (https://mcp.whop.com/claude/mcp)",
                "apiVersion": api_version.group(1) if api_version else None,
                "tools": dict(sorted(tools.items())),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Wrote {len(tools)} tools to {OUTPUT.relative_to(ROOT)} ({len(excluded)} excluded on this surface)")
    write_mock_tools(repo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
