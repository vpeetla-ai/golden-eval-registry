"""Score real outputs against golden-eval-registry expectations.

This registry stays dependency-light and provider-agnostic on purpose (see
pyproject.toml's empty `dependencies`) — this module defines *what a pass
means* per suite kind, not *how to call* the service under test. Each
consumer repo already knows how to reach itself (an HTTP client, a direct
function import, ...); it gets `actual` however makes sense for its own
runtime, then calls `score_suite` here for the comparison and merge-gate
decision. This is the missing link between "fixtures exist" (validate.py)
and "fixtures gate a merge."

Only kinds with a real, wired consumer have a scorer implemented — see the
README status table for which suites actually gate a CI build today.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from golden_eval_registry.schema import SuiteManifest


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class SuiteResult:
    suite_id: str
    results: tuple[CaseResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def failures(self) -> tuple[CaseResult, ...]:
        return tuple(result for result in self.results if not result.passed)


def score_case(kind: str, case: dict[str, Any], actual: dict[str, Any]) -> CaseResult:
    scorer = _SCORERS.get(kind)
    if scorer is None:
        raise ValueError(
            f"no scorer implemented for kind '{kind}' yet — see golden_eval_registry.runner._SCORERS"
        )
    return scorer(case, actual)


def score_suite(
    manifest: SuiteManifest,
    cases: list[dict[str, Any]],
    actual_by_id: dict[str, dict[str, Any]],
) -> SuiteResult:
    """`actual_by_id` maps case id -> the real output a consumer repo produced
    for that case (an HTTP response body, a function's return value, ...)."""
    results = []
    for case in cases:
        case_id = str(case["id"])
        actual = actual_by_id.get(case_id)
        if actual is None:
            results.append(CaseResult(case_id, False, "no actual output provided for this case"))
            continue
        results.append(score_case(manifest.kind, case, actual))
    return SuiteResult(suite_id=manifest.suite_id, results=tuple(results))


def _score_rag_answer(case: dict[str, Any], actual: dict[str, Any]) -> CaseResult:
    expect = case["expect"]
    case_id = str(case["id"])
    problems: list[str] = []

    if "grounded" in expect and bool(actual.get("grounded")) != bool(expect["grounded"]):
        problems.append(f"grounded: expected {expect['grounded']}, got {actual.get('grounded')}")

    expected_docs = set(expect.get("document_ids") or [])
    actual_docs = {citation.get("document_id") for citation in actual.get("citations", [])}
    if expected_docs and not expected_docs.issubset(actual_docs):
        problems.append(f"document_ids: expected {sorted(expected_docs)} cited, got {sorted(d for d in actual_docs if d)}")

    expected_flags = set(expect.get("risk_flags") or [])
    actual_flags = set(actual.get("risk_flags") or [])
    if expected_flags != actual_flags:
        problems.append(f"risk_flags: expected {sorted(expected_flags)}, got {sorted(actual_flags)}")

    return CaseResult(case_id, not problems, "; ".join(problems) or "ok")


def _score_mission_gate(case: dict[str, Any], actual: dict[str, Any]) -> CaseResult:
    expect = case["expect"]
    case_id = str(case["id"])
    problems: list[str] = []

    for check_name, expected_status in (expect.get("checks") or {}).items():
        actual_status = (actual.get("checks") or {}).get(check_name)
        if actual_status != expected_status:
            problems.append(f"check '{check_name}': expected {expected_status}, got {actual_status}")

    min_score = expect.get("quality_score_min")
    if min_score is not None and actual.get("quality_score", 0) < min_score:
        problems.append(f"quality_score: expected >= {min_score}, got {actual.get('quality_score')}")

    contains = expect.get("decision_contains")
    if contains and contains not in str(actual.get("decision", "")):
        problems.append(f"decision: expected to contain '{contains}', got '{actual.get('decision')}'")

    return CaseResult(case_id, not problems, "; ".join(problems) or "ok")


def _score_triage_preference(case: dict[str, Any], actual: dict[str, Any]) -> CaseResult:
    expect = case.get("expect", {})
    case_id = str(case["id"])
    if not expect.get("chosen_beats_rejected", True):
        return CaseResult(case_id, True, "ok")
    if not actual.get("chosen_beats_rejected"):
        return CaseResult(
            case_id,
            False,
            actual.get("detail") or "chosen did not beat rejected on alignment score",
        )
    return CaseResult(case_id, True, "ok")


_SCORERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], CaseResult]] = {
    "rag_answer": _score_rag_answer,
    "mission_gate": _score_mission_gate,
    "triage_preference": _score_triage_preference,
}
