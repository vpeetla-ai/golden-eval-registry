"""Validate golden eval suite manifests and JSONL cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from golden_eval_registry.schema import SuiteManifest, parse_manifest


def registry_root() -> Path:
    return Path(__file__).resolve().parents[2]


def iter_manifests(root: Path) -> list[Path]:
    return sorted((root / "suites").glob("*/manifest.json"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"missing cases file: {path}")
    cases: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"{path}:{line_no}: case must be an object")
        cases.append(data)
    if not cases:
        raise ValueError(f"{path}: no cases found")
    return cases


def validate_case(manifest: SuiteManifest, case: dict[str, Any], suite_dir: Path) -> None:
    required = {"id", "kind", "input", "expect"}
    missing = required - case.keys()
    if missing:
        raise ValueError(f"{manifest.suite_id}/{case.get('id', '<missing>')}: missing {sorted(missing)}")

    if case["kind"] != manifest.kind:
        raise ValueError(f"{case['id']}: kind {case['kind']} does not match manifest {manifest.kind}")

    if "thresholds" in case and not isinstance(case["thresholds"], dict):
        raise ValueError(f"{case['id']}: thresholds must be an object")

    fixture_ref = case.get("fixture_ref")
    if fixture_ref:
        target = (suite_dir / str(fixture_ref)).resolve()
        if not str(target).startswith(str(suite_dir.resolve())):
            raise ValueError(f"{case['id']}: fixture_ref escapes suite dir")
        if not target.exists():
            raise ValueError(f"{case['id']}: fixture_ref does not exist: {fixture_ref}")

    if manifest.kind == "repo_fix":
        fixture = case.get("fixture_ref")
        if not fixture:
            raise ValueError(f"{case['id']}: repo_fix requires fixture_ref")
        fixture_dir = suite_dir / str(fixture)
        if not (fixture_dir / "test_calc.py").exists():
            raise ValueError(f"{case['id']}: repo_fix fixture missing test file")


def validate_registry(root: Path) -> dict[str, Any]:
    manifests = iter_manifests(root)
    if not manifests:
        raise ValueError(f"no suite manifests under {root / 'suites'}")

    seen_ids: set[str] = set()
    suite_count = 0
    case_count = 0
    consumers: set[str] = set()

    for manifest_path in manifests:
        manifest = parse_manifest(manifest_path)
        if not manifest.locked:
            raise ValueError(f"{manifest.suite_id}: manifest must be locked")
        cases = load_jsonl(manifest.cases_path)
        suite_dir = manifest_path.parent
        suite_count += 1
        consumers.update(manifest.consumer_repos)
        for case in cases:
            case_id = str(case.get("id", ""))
            if case_id in seen_ids:
                raise ValueError(f"duplicate case id: {case_id}")
            seen_ids.add(case_id)
            validate_case(manifest, case, suite_dir)
            case_count += 1

    return {
        "suites": suite_count,
        "cases": case_count,
        "consumer_repos": sorted(consumers),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate golden eval registry")
    parser.add_argument("--root", type=Path, default=registry_root())
    args = parser.parse_args(argv)

    try:
        result = validate_registry(args.root.resolve())
    except Exception as exc:  # noqa: BLE001 - CLI should return readable error
        print(f"golden-eval-registry: FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        "golden-eval-registry: ok "
        f"{result['suites']} suites, {result['cases']} cases, "
        f"{len(result['consumer_repos'])} consumers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
