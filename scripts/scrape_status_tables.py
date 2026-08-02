#!/usr/bin/env python3
"""Scrape honest Implementation status tables from sibling vpeetla-ai repos.

Exit 1 if a README is missing the status section or contains known stale claims
(e.g. AegisAI still saying ACF publish is Planned).

Optional: --json writes a machine-readable summary for overnight CI artifacts.
"""

from __future__ import annotations

import argparse
import json
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
    "agent-finops": HOME / "agent-finops" / "README.md",
    "aegis-llm-gateway": HOME / "aegis-llm-gateway" / "README.md",
    "aegis-semantic-cache": HOME / "aegis-semantic-cache" / "README.md",
    "golden-eval-registry": HOME / "golden-eval-registry" / "README.md",
}

# Stale phrases that should not appear after M1 honesty pass
FORBIDDEN = [
    (re.compile(r"ai-content-factory publish\s*\|\s*🟡\s*Planned", re.I), "AegisAI ACF publish still Planned"),
    (
        re.compile(r"Cloudflare R2 media\s*\|\s*.*native binary attach not yet", re.I),
        "ACF R2 still claims native attach not yet",
    ),
]

# HTTP spine / AgentOps surfaces must document the public observability status path.
# Library-only GER is exempt (no live /observability/status service).
OBSERVABILITY_STATUS_REQUIRED = {
    "ai-content-factory",
    "aegisai-enterprise-agent-platform",
    "venkat-ai-platform",
    "enterprise_rag_platform",
    "loop-engine-agent-platform",
    "aegisloop-agentops-workbench",
    "sentinel-brief",
    "agent-finops",
    "aegis-llm-gateway",
    "aegis-semantic-cache",
}
OBSERVABILITY_STATUS_MARKER = re.compile(r"observability/status", re.I)


def scrape(repos: dict[str, Path] | None = None) -> dict:
    repos = repos or REPOS
    results: list[dict] = []
    failures: list[str] = []
    for name, path in repos.items():
        entry: dict = {"repo": name, "path": str(path), "status": "ok", "yellow_rows": 0}
        if not path.exists():
            entry["status"] = "skip"
            entry["detail"] = "README not found"
            results.append(entry)
            print(f"SKIP {name}: README not found at {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if (
            "Implementation status" not in text
            and "Implementation Status" not in text
            and "## Status" not in text
        ):
            entry["status"] = "fail"
            entry["detail"] = "missing Implementation status section"
            failures.append(f"{name}: missing Implementation status section")
            results.append(entry)
            print(f"FAIL {name}: no status section")
            continue
        bad = False
        for pattern, label in FORBIDDEN:
            if pattern.search(text):
                failures.append(f"{name}: {label}")
                entry["status"] = "fail"
                entry["detail"] = label
                print(f"FAIL {name}: {label}")
                bad = True
        if (
            not bad
            and name in OBSERVABILITY_STATUS_REQUIRED
            and not OBSERVABILITY_STATUS_MARKER.search(text)
        ):
            label = "missing observability/status honesty surface in README"
            failures.append(f"{name}: {label}")
            entry["status"] = "fail"
            entry["detail"] = label
            print(f"FAIL {name}: {label}")
            bad = True
        if not bad:
            yellow = len(re.findall(r"🟡", text))
            entry["yellow_rows"] = yellow
            print(f"OK   {name}: status section present ({yellow} yellow rows)")
        results.append(entry)
    return {
        "ok": not failures,
        "failures": failures,
        "results": results,
        "checked": len([r for r in results if r["status"] != "skip"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="Write JSON summary to this path")
    args = parser.parse_args(argv)
    summary = scrape()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.json}")
    if summary["failures"]:
        print("\n".join(summary["failures"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
