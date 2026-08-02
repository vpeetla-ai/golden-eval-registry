#!/usr/bin/env python3
"""Scrape honest Implementation status tables from sibling vpeetla-ai repos.

Exit 1 if a README is missing the status section or contains known stale claims
(e.g. AegisAI still saying ACF publish is Planned).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HOME = Path.home()
REPOS = {
    "ai-content-factory": HOME / "ai-content-factory" / "README.md",
    "aegisai-enterprise-agent-platform": HOME / "aegisai-enterprise-agent-platform" / "README.md",
    "venkat-ai-platform": HOME / "venkat-ai-platform" / "README.md",
    "enterprise_rag_platform": HOME / "enterprise_rag_platform" / "README.md",
    "loop-engine-agent-platform": HOME / "loop-engine-agent-platform" / "README.md",
    "aegisloop-agentops-workbench": HOME / "aegisloop-agentops-workbench" / "README.md",
    "sentinel-brief": HOME / "sentinel-brief" / "README.md",
}

# Stale phrases that should not appear after M1 honesty pass
FORBIDDEN = [
    (re.compile(r"ai-content-factory publish\s*\|\s*🟡\s*Planned", re.I), "AegisAI ACF publish still Planned"),
]


def main() -> int:
    failures: list[str] = []
    for name, path in REPOS.items():
        if not path.exists():
            print(f"SKIP {name}: README not found at {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if (
            "Implementation status" not in text
            and "Implementation Status" not in text
            and "## Status" not in text
        ):
            failures.append(f"{name}: missing Implementation status section")
            print(f"FAIL {name}: no status section")
            continue
        bad = False
        for pattern, label in FORBIDDEN:
            if pattern.search(text):
                failures.append(f"{name}: {label}")
                print(f"FAIL {name}: {label}")
                bad = True
        if not bad:
            yellow = len(re.findall(r"🟡", text))
            print(f"OK   {name}: status section present ({yellow} yellow rows)")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
