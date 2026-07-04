from __future__ import annotations

from pathlib import Path

from golden_eval_registry.runner import score_case, score_suite
from golden_eval_registry.schema import parse_manifest
from golden_eval_registry.validate import iter_manifests, load_jsonl

ROOT = Path(__file__).resolve().parents[1]


def _suite(suite_id: str):
    for path in iter_manifests(ROOT):
        manifest = parse_manifest(path)
        if manifest.suite_id == suite_id:
            return manifest, load_jsonl(manifest.cases_path)
    raise AssertionError(f"suite not found: {suite_id}")


def test_manifest_captures_corpus_path_when_present() -> None:
    manifest, _ = _suite("enterprise_rag.golden_v1")
    assert manifest.corpus_path is not None
    assert manifest.corpus_path.name == "policy-001.json"


def test_manifest_corpus_path_none_when_absent() -> None:
    manifest, _ = _suite("aegisloop.mission_gates_v1")
    assert manifest.corpus_path is None


def test_rag_answer_scorer_passes_on_matching_output() -> None:
    manifest, cases = _suite("enterprise_rag.golden_v1")
    case = next(c for c in cases if c["id"] == "rag-001")
    actual = {
        "grounded": True,
        "citations": [{"document_id": "policy-001"}],
        "risk_flags": [],
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_rag_answer_scorer_fails_on_missing_citation() -> None:
    manifest, cases = _suite("enterprise_rag.golden_v1")
    case = next(c for c in cases if c["id"] == "rag-001")
    actual = {"grounded": True, "citations": [], "risk_flags": []}
    result = score_case(manifest.kind, case, actual)
    assert not result.passed
    assert "document_ids" in result.detail


def test_rag_answer_scorer_fails_on_missing_risk_flag() -> None:
    manifest, cases = _suite("enterprise_rag.golden_v1")
    case = next(c for c in cases if c["id"] == "rag-003")
    actual = {"grounded": True, "citations": [{"document_id": "policy-001"}], "risk_flags": []}
    result = score_case(manifest.kind, case, actual)
    assert not result.passed
    assert "risk_flags" in result.detail


def test_mission_gate_scorer_passes_on_matching_output() -> None:
    manifest, cases = _suite("aegisloop.mission_gates_v1")
    case = next(c for c in cases if c["id"] == "aegisloop-mission-001")
    actual = {
        "checks": {"Stop condition": "pass", "Policy compliance": "pass"},
        "quality_score": 94,
        "decision": "Ship: quality gate passed",
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_mission_gate_scorer_fails_on_low_quality_score() -> None:
    manifest, cases = _suite("aegisloop.mission_gates_v1")
    case = next(c for c in cases if c["id"] == "aegisloop-mission-001")
    actual = {
        "checks": {"Stop condition": "pass", "Policy compliance": "pass"},
        "quality_score": 50,
        "decision": "Ship: quality gate passed",
    }
    result = score_case(manifest.kind, case, actual)
    assert not result.passed
    assert "quality_score" in result.detail


def test_score_suite_reports_missing_actual_as_failure() -> None:
    manifest, cases = _suite("aegisloop.mission_gates_v1")
    result = score_suite(manifest, cases, actual_by_id={})
    assert not result.passed
    assert len(result.failures) == len(cases)


def test_score_case_raises_for_unimplemented_kind() -> None:
    manifest, cases = _suite("loopforge.benchmark_v1")
    try:
        score_case(manifest.kind, cases[0], actual={})
        raise AssertionError("expected ValueError for an unimplemented scorer kind")
    except ValueError as exc:
        assert "harness_qa" in str(exc)
