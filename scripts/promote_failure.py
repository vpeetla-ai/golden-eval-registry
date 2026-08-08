#!/usr/bin/env python3
"""Promote a failed multi-agent trajectory into a GER collaboration candidate case.

Usage:
  python scripts/promote_failure.py --run path/to/mission.json
  python scripts/promote_failure.py --trajectory path/to/trajectory.json \\
      --expect-hard-gate unresolved_contradiction

Writes a redacted JSONL candidate under:
  suites/multi_agent_collaboration_v1/candidates/

Does NOT auto-lock or mutate locked cases — review + move into cases.jsonl
via PR. This is the Stage-4 "production failure → regression memory" loop.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "suites" / "multi_agent_collaboration_v1" / "candidates"

REDACT_KEYS = {
    "api_key",
    "token",
    "authorization",
    "password",
    "secret",
    "email",
    "phone",
}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            lower = str(key).lower()
            if any(part in lower for part in REDACT_KEYS):
                out[key] = "[REDACTED]"
            else:
                out[key] = _redact(item)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str) and re.search(r"(sk-|Bearer |api[_-]?key)", value, re.I):
        return "[REDACTED]"
    return value


def extract_trajectory(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload.get("artifacts") or {}
    if isinstance(artifacts.get("collaboration_trajectory"), dict):
        return dict(artifacts["collaboration_trajectory"])
    if isinstance(payload.get("trajectory"), dict):
        return dict(payload["trajectory"])
    if isinstance(payload.get("collaboration_trajectory"), dict):
        return dict(payload["collaboration_trajectory"])
    raise ValueError("payload missing collaboration_trajectory / trajectory")


def extract_hard_gates(payload: dict[str, Any], trajectory: dict[str, Any]) -> list[str]:
    artifacts = payload.get("artifacts") or {}
    scorecard = artifacts.get("scorecard") if isinstance(artifacts, dict) else None
    if isinstance(scorecard, dict) and scorecard.get("hard_gate_failures"):
        return [str(x) for x in scorecard["hard_gate_failures"]]
    try:
        from golden_eval_registry.scorecard import score_trajectory

        return list(score_trajectory(trajectory).hard_gate_failures)
    except Exception:
        return []


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned[:48] or "failure"


def build_candidate(
    payload: dict[str, Any],
    *,
    expect_hard_gate: str | None,
    note: str | None,
) -> dict[str, Any]:
    trajectory = _redact(extract_trajectory(payload))
    gates = extract_hard_gates(payload, trajectory)
    if expect_hard_gate and expect_hard_gate not in gates:
        gates = [*gates, expect_hard_gate]

    run_id = str(payload.get("run_id") or trajectory.get("workflow_id") or "unknown")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    case_id = f"collab-promoted-{slugify(run_id)}-{stamp}"

    expect: dict[str, Any] = {"release_ok": False}
    if gates:
        expect["require_hard_gates"] = gates
        expect["max_quality_score"] = 40

    return {
        "id": case_id,
        "kind": "collaboration_scorecard",
        "input": {
            "note": note
            or f"Promoted failure from run {run_id}. Review before moving into locked cases.jsonl.",
            "source_run_id": run_id,
            "promoted_at": stamp,
            "candidate": True,
        },
        "expect": expect,
        "trajectory": trajectory,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, help="Mission response JSON (AegisLoop persist shape)")
    parser.add_argument("--trajectory", type=Path, help="Raw trajectory JSON")
    parser.add_argument("--expect-hard-gate", help="Force-require this hard gate in expect")
    parser.add_argument("--note", help="Human note for reviewers")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print candidate JSON instead of writing candidates/",
    )
    args = parser.parse_args()

    if bool(args.run) == bool(args.trajectory):
        parser.error("provide exactly one of --run or --trajectory")

    if args.run:
        payload = json.loads(args.run.read_text(encoding="utf-8"))
    else:
        payload = {"trajectory": json.loads(args.trajectory.read_text(encoding="utf-8"))}

    candidate = build_candidate(
        payload,
        expect_hard_gate=args.expect_hard_gate,
        note=args.note,
    )
    line = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))

    if args.stdout:
        print(line)
        return 0

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    out = CANDIDATE_DIR / f"{candidate['id']}.jsonl"
    out.write_text(line + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print("Next: review redaction, then append into cases.jsonl via PR (keep locked suite honest).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
