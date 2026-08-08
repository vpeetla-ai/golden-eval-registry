"""Tests for failure promotion and collaboration drift scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _healthy() -> dict:
    return {
        "workflow_id": "wf",
        "outcome": {"task_success": True, "state_verified": True},
        "artifacts": [{"id": "a", "produced_by": "x", "consumed_by": ["y"]}],
        "handoffs": [],
        "contradictions": [{"agents": ["a", "b"], "topic": "x", "resolved": False}],
        "duplicate_work": [],
        "escalations": [],
        "tool_calls": [],
        "economics": {"latency_ok": True},
        "governance": {"policy_ok": True, "approval_ok": True},
    }


def test_promote_failure_stdout(tmp_path: Path) -> None:
    run = {
        "run_id": "run-abc",
        "artifacts": {
            "collaboration_trajectory": _healthy(),
            "scorecard": {"hard_gate_failures": ["unresolved_contradiction"], "release_ok": False},
            "api_key": "sk-secret-should-redact",
        },
    }
    run_path = tmp_path / "run.json"
    run_path.write_text(json.dumps(run), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/promote_failure.py"), "--run", str(run_path), "--stdout"],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    candidate = json.loads(proc.stdout.strip())
    assert candidate["kind"] == "collaboration_scorecard"
    assert candidate["expect"]["release_ok"] is False
    assert "unresolved_contradiction" in candidate["expect"]["require_hard_gates"]
    assert candidate["trajectory"]["contradictions"]


def test_collaboration_drift_flags_high_hard_gate_rate(tmp_path: Path) -> None:
    runs = tmp_path / "runs.jsonl"
    lines = []
    for _ in range(4):
        lines.append(json.dumps({"artifacts": {"collaboration_trajectory": _healthy()}}))
    runs.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = tmp_path / "report.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/collaboration_drift.py"),
            "--runs",
            str(runs),
            "--report",
            str(report),
            "--max-hard-gate-rate",
            "0.10",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["ok"] is False
    assert data["hard_gate_failure_rate"] == 1.0
