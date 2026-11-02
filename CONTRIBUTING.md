# Contributing

Skills are short, and every line in one is something an agent will act on. A wrong fact here ships into other people's code, so the bar is: every claim comes from the current docs or the published SDK.

## Setup

```bash
npm ci
python3 -m venv .venv && .venv/bin/pip install pyyaml
```

## Making a change

1. Read [`AGENTS.md`](AGENTS.md): skill structure, banned patterns, and versioning.
2. Branch from `main` and edit the skill. Link the docs page you took each fact from in the reference file's `## Sources` list.
3. Run the checks:

   ```bash
   .venv/bin/python scripts/validate.py
   npm run -s check:snippets
   python3 scripts/check-links.py
   ```

4. If you changed a `SKILL.md`, run its evals and compare with `main`:

   ```bash
   claude plugin eval . --case 'whop-webhooks-*' --runs 3
   ```

5. Open a pull request. CI runs the same checks.

## Releasing

```bash
.venv/bin/python scripts/bump-version.py 0.2.0
```

This updates `VERSION`, every `SKILL.md`, every plugin manifest, and the MCP header together.

## Reporting a wrong fact

Open an issue with the skill, the line, and the docs page or SDK version that shows the correct behavior.
