#!/usr/bin/env python3
"""Fetch every docs.whop.com link in skills/ and fail on any that is not reachable."""

import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_PATTERN = re.compile(r"https://docs\.whop\.com/[A-Za-z0-9_./\-#]*[A-Za-z0-9_/\-]")


def collect_links() -> dict[str, set[str]]:
    links: dict[str, set[str]] = {}
    for path in sorted((ROOT / "skills").rglob("*.md")):
        for url in LINK_PATTERN.findall(path.read_text()):
            links.setdefault(url.split("#")[0], set()).add(str(path.relative_to(ROOT)))
    return links


def status(url: str) -> tuple[str, int | str]:
    request = urllib.request.Request(url, headers={"User-Agent": "whop-skills-link-check"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return url, response.status
    except urllib.error.HTTPError as exc:
        return url, exc.code
    except (urllib.error.URLError, TimeoutError) as exc:
        return url, str(exc)


def main() -> int:
    links = collect_links()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(status, sorted(links)))
    broken = [(url, code) for url, code in results if code != 200]
    for url, code in broken:
        print(f"{code}  {url}  (in {', '.join(sorted(links[url]))})")
    if broken:
        print(f"\n{len(broken)} of {len(links)} links are broken")
        return 1
    print(f"OK: {len(links)} docs links reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
