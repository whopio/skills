#!/usr/bin/env python3
"""Write references/skill-feedback.md into every skill from one template.

Each skill installs on its own, so each needs its own copy of the feedback
steps. They come from scripts/skill-feedback.template.md with `{skill}` filled
in. Run after editing the template; with --check, exit 1 if a copy is missing
or out of date (CI runs this through scripts/validate.py).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "skill-feedback.template.md"
SKILLS_DIR = ROOT / "skills"
FILE = Path("references") / "skill-feedback.md"


def expected() -> dict[Path, str]:
    template = TEMPLATE.read_text()
    return {
        skill_dir / FILE: template.replace("{skill}", skill_dir.name)
        for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())
    }


def main() -> int:
    files = expected()
    if "--check" in sys.argv:
        stale = [p for p, content in files.items() if not p.is_file() or p.read_text() != content]
        for path in stale:
            print(f"{path.relative_to(ROOT)} is out of date; run scripts/build-skill-feedback.py")
        return 1 if stale else 0
    for path, content in files.items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(content)
    print(f"Wrote {len(files)} skill-feedback.md files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
