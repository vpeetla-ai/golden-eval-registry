"""Registry schema helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_KINDS = {
    "rag_answer",
    "harness_qa",
    "repo_fix",
    "mission_gate",
    "graph_hitl",
    "brief_gate",
}


@dataclass(frozen=True)
class SuiteManifest:
    suite_id: str
    version: str
    kind: str
    locked: bool
    consumer_repos: list[str]
    cases_path: Path
    thresholds: dict[str, Any]


def parse_manifest(path: Path) -> SuiteManifest:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"suite_id", "version", "kind", "locked", "consumer_repos", "cases"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path}: missing keys {sorted(missing)}")

    kind = str(data["kind"])
    if kind not in SUPPORTED_KINDS:
        raise ValueError(f"{path}: unsupported kind {kind}")

    consumer_repos = data["consumer_repos"]
    if not isinstance(consumer_repos, list) or not all(isinstance(x, str) for x in consumer_repos):
        raise ValueError(f"{path}: consumer_repos must be a list of strings")

    cases_path = (path.parent / str(data["cases"])).resolve()
    return SuiteManifest(
        suite_id=str(data["suite_id"]),
        version=str(data["version"]),
        kind=kind,
        locked=bool(data["locked"]),
        consumer_repos=consumer_repos,
        cases_path=cases_path,
        thresholds=dict(data.get("thresholds") or {}),
    )
