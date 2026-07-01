from __future__ import annotations

import json
from pathlib import Path

from golden_eval_registry.schema import SUPPORTED_KINDS, parse_manifest
from golden_eval_registry.validate import iter_manifests, load_jsonl, validate_registry

ROOT = Path(__file__).resolve().parents[1]


def test_registry_validates() -> None:
    result = validate_registry(ROOT)
    assert result["suites"] == 6
    assert result["cases"] == 14
    assert "enterprise_rag_platform" in result["consumer_repos"]
    assert "loop-engine-agent-platform" in result["consumer_repos"]
    assert "sentinel-brief" in result["consumer_repos"]


def test_every_manifest_is_locked_and_supported() -> None:
    manifests = iter_manifests(ROOT)
    assert len(manifests) == 6
    for path in manifests:
        manifest = parse_manifest(path)
        assert manifest.locked is True
        assert manifest.kind in SUPPORTED_KINDS
        assert manifest.cases_path.exists()


def test_case_ids_are_globally_unique() -> None:
    ids: list[str] = []
    for manifest_path in iter_manifests(ROOT):
        manifest = parse_manifest(manifest_path)
        ids.extend(str(case["id"]) for case in load_jsonl(manifest.cases_path))
    assert len(ids) == len(set(ids))


def test_repo_fix_fixture_is_intentionally_failing() -> None:
    calc = ROOT / "suites" / "loopforge_repo_fix_v1" / "repos" / "buggy_calc" / "calc.py"
    test_calc = ROOT / "suites" / "loopforge_repo_fix_v1" / "repos" / "buggy_calc" / "test_calc.py"
    assert "BUG" in calc.read_text(encoding="utf-8")
    assert "assert add(1, 2) == 3" in test_calc.read_text(encoding="utf-8")


def test_enterprise_rag_corpus_matches_expected_document() -> None:
    corpus = ROOT / "suites" / "enterprise_rag_golden_v1" / "corpus" / "policy-001.json"
    doc = json.loads(corpus.read_text(encoding="utf-8"))
    assert doc["document_id"] == "policy-001"
    assert "human approval" in doc["body"].lower()
