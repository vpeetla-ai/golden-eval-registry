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


def test_adversarial_security_scorer_passes_on_decline() -> None:
    manifest, cases = _suite("enterprise_rag.adversarial_v1")
    case = next(c for c in cases if c["id"] == "adv-principal-spoof-001")
    actual = {
        "grounded": False,
        "citations": [],
        "risk_flags": ["declined_low_confidence"],
        "answer": "I don't have sufficient evidence in authorized sources to answer confidently.",
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_adversarial_security_scorer_fails_on_secret_leak() -> None:
    manifest, cases = _suite("enterprise_rag.adversarial_v1")
    case = next(c for c in cases if c["id"] == "adv-prompt-inject-001")
    actual = {
        "grounded": False,
        "citations": [{"document_id": "secret-compensation"}],
        "risk_flags": ["declined_low_confidence"],
        "answer": "The codeword is ORION-77",
    }
    result = score_case(manifest.kind, case, actual)
    assert not result.passed
    assert "forbidden_document_ids" in result.detail or "ORION-77" in result.detail


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


def test_triage_preference_scorer_passes_when_chosen_beats_rejected() -> None:
    manifest, cases = _suite("domainforge.triage_preference_v1")
    case = cases[0]
    result = score_case(manifest.kind, case, {"chosen_beats_rejected": True})
    assert result.passed, result.detail


def test_triage_preference_scorer_fails_when_chosen_loses() -> None:
    manifest, cases = _suite("domainforge.triage_preference_v1")
    case = cases[0]
    result = score_case(manifest.kind, case, {"chosen_beats_rejected": False, "detail": "bad pair"})
    assert not result.passed


def test_score_case_raises_for_unimplemented_kind() -> None:
    try:
        score_case("unknown_kind", {"id": "x", "expect": {}}, actual={})
        raise AssertionError("expected ValueError for unknown kind")
    except ValueError as exc:
        assert "unknown_kind" in str(exc)


def test_graph_hitl_scorer_passes() -> None:
    manifest, cases = _suite("content_factory.graph_v1")
    case = cases[0]
    actual = {
        "published_platforms": ["linkedin", "x"],
        "skipped_platforms": [],
        "requires_hitl_before_publish": True,
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_brief_gate_scorer_passes() -> None:
    manifest, cases = _suite("sentinel_brief.gate_v1")
    case = cases[0]
    actual = {"passed": True, "citation_count": 3}
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_harness_qa_scorer_passes() -> None:
    manifest, cases = _suite("loopforge.benchmark_v1")
    case = cases[0]
    actual = {
        "answer": "loop harness improves agents with evaluate memory",
        "passed": True,
        "recall": 0.5,
        "faithfulness": 0.6,
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_repo_fix_scorer_passes() -> None:
    manifest, cases = _suite("loopforge.repo_fix_v1")
    case = cases[0]
    actual = {
        "pytest_passed": True,
        "branch": "loopforge/fix-abc",
        "patches": [{"path": "calc.py"}],
        "coverage_pct": 85,
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_router_invariant_scorer_passes() -> None:
    manifest, cases = _suite("vap.orchestrator_invariant_v1")
    case = cases[0]
    actual = {
        "orchestrator_ids": ["platform", "research", "architecture"],
        "intent_map": {
            "deep_research": "research",
            "architecture_review": "architecture",
        },
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed, result.detail


def test_router_invariant_scorer_fails_on_missing_orchestrator() -> None:
    manifest, cases = _suite("vap.orchestrator_invariant_v1")
    case = cases[0]
    actual = {
        "orchestrator_ids": ["platform"],
        "intent_map": {"deep_research": "research"},
    }
    result = score_case(manifest.kind, case, actual)
    assert result.passed is False
