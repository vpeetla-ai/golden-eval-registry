"""Tests for multi-agent collaboration scorecard (CSS / TUE / hard gates)."""

from __future__ import annotations

from pathlib import Path

from golden_eval_registry.runner import score_case
from golden_eval_registry.scorecard import aggregate_trials, score_trajectory

ROOT = Path(__file__).resolve().parents[1]


def _healthy_trajectory() -> dict:
    return {
        "workflow_id": "wf-healthy",
        "outcome": {"task_success": True, "state_verified": True},
        "artifacts": [
            {"id": "research", "produced_by": "researcher", "consumed_by": ["writer"]},
            {"id": "draft", "produced_by": "writer", "consumed_by": ["verifier"]},
            {"id": "final", "produced_by": "verifier", "consumed_by": ["ship"]},
        ],
        "handoffs": [
            {
                "from": "researcher",
                "to": "writer",
                "preserved": ["evidence", "constraints", "uncertainty"],
                "lost": [],
            },
            {
                "from": "writer",
                "to": "verifier",
                "preserved": ["evidence", "constraints", "uncertainty"],
                "lost": [],
            },
        ],
        "contradictions": [],
        "duplicate_work": [],
        "escalations": [{"required": False, "raised": False}],
        "tool_calls": [
            {
                "tool": "search",
                "selected_correct": True,
                "args_valid": True,
                "executed": True,
                "outcome_correct": True,
                "necessary": True,
            },
            {
                "tool": "fetch",
                "selected_correct": True,
                "args_valid": True,
                "executed": True,
                "outcome_correct": True,
                "necessary": True,
            },
        ],
        "economics": {"cost_usd": 0.12, "max_cost_usd": 1.0, "latency_ok": True, "expected_max_tool_calls": 5},
        "governance": {"policy_ok": True, "approval_ok": True},
    }


def test_healthy_trajectory_releases() -> None:
    result = score_trajectory(_healthy_trajectory())
    assert result.release_ok
    assert result.outcome == 1.0
    assert result.coordination >= 0.8
    assert result.tool_use >= 0.9
    assert result.quality_score() >= 85


def test_unresolved_contradiction_hard_fails_despite_task_success() -> None:
    traj = _healthy_trajectory()
    traj["contradictions"] = [
        {"agents": ["policy", "resolution"], "topic": "eligibility", "resolved": False}
    ]
    result = score_trajectory(traj)
    assert not result.release_ok
    assert "unresolved_contradiction" in result.hard_gate_failures
    assert result.quality_score() <= 40


def test_escalation_bypass_hard_fails() -> None:
    traj = _healthy_trajectory()
    traj["escalations"] = [{"required": True, "raised": False, "signal": "low_confidence"}]
    result = score_trajectory(traj)
    assert not result.release_ok
    assert "escalation_bypass" in result.hard_gate_failures


def test_orphaned_and_duplicate_work_lowers_coordination() -> None:
    traj = _healthy_trajectory()
    traj["artifacts"].append({"id": "unused_risk", "produced_by": "account", "consumed_by": []})
    traj["duplicate_work"] = [
        {"agents": ["policy", "resolution"], "task": "search same docs"},
        {"agents": ["policy", "account"], "task": "re-fetch account"},
    ]
    result = score_trajectory(traj)
    assert result.release_ok  # not a hard gate
    assert result.coordination < score_trajectory(_healthy_trajectory()).coordination
    assert result.components["css"]["orphan_count"] == 1
    assert result.components["css"]["duplicate_count"] == 2


def test_tue_penalizes_unnecessary_and_wrong_selection() -> None:
    traj = _healthy_trajectory()
    traj["tool_calls"] = [
        {
            "tool": "search",
            "selected_correct": False,
            "args_valid": True,
            "executed": True,
            "outcome_correct": True,
            "necessary": False,
        },
        {
            "tool": "search",
            "selected_correct": True,
            "args_valid": True,
            "executed": True,
            "outcome_correct": True,
            "necessary": True,
        },
    ]
    result = score_trajectory(traj)
    assert result.tool_use < 1.0
    assert result.components["tue"]["unnecessary_count"] == 1


def test_aggregate_trials_reports_pass_every_vs_at_least_one() -> None:
    ok = score_trajectory(_healthy_trajectory())
    bad = score_trajectory(
        {
            **_healthy_trajectory(),
            "outcome": {"task_success": False, "state_verified": False},
        }
    )
    mixed = aggregate_trials([ok, bad, ok])
    assert mixed["n"] == 3
    assert mixed["pass_at_least_one"] == 1.0
    assert mixed["pass_every_trial"] == 0.0


def test_collaboration_scorecard_scorer_suite_case() -> None:
    case = {
        "id": "collab-unit",
        "kind": "collaboration_scorecard",
        "expect": {
            "release_ok": True,
            "min_coordination": 0.7,
            "min_tool_use": 0.7,
            "forbid_hard_gates": ["unresolved_contradiction", "escalation_bypass"],
        },
    }
    actual = {"trajectory": _healthy_trajectory()}
    result = score_case("collaboration_scorecard", case, actual)
    assert result.passed, result.detail


def test_multi_agent_collaboration_suite_self_scores() -> None:
    """Registry-local CI: fixture trajectories score against their own expect blocks."""
    from golden_eval_registry.runner import score_suite
    from golden_eval_registry.schema import parse_manifest
    from golden_eval_registry.validate import load_jsonl

    suite_dir = ROOT / "suites" / "multi_agent_collaboration_v1"
    manifest = parse_manifest(suite_dir / "manifest.json")
    cases = load_jsonl(manifest.cases_path)
    actual_by_id = {str(c["id"]): {"trajectory": c["trajectory"]} for c in cases}
    result = score_suite(manifest, cases, actual_by_id)
    failures = "\n".join(f"{f.case_id}: {f.detail}" for f in result.failures)
    assert result.passed, failures
