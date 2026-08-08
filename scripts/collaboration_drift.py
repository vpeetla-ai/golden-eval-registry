#!/usr/bin/env python3
"""Weekly collaboration drift check over persisted mission trajectories.

Usage:
  python scripts/collaboration_drift.py --runs path/to/runs.jsonl
  python scripts/collaboration_drift.py --runs-dir path/to/runs/ --baseline path/to/baseline.json

Fails (exit 1) when:
  - hard_gate_failure_rate exceeds --max-hard-gate-rate
  - mean coordination drops more than --max-coord-drop vs baseline
  - orphan_rate exceeds --max-orphan-rate

Writes a JSON report to --report (default /tmp/collab-drift-report.json).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

from golden_eval_registry.scorecard import aggregate_trials, score_trajectory


def load_runs(path: Path | None, runs_dir: Path | None) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if path:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                runs.append(json.loads(line))
    if runs_dir:
        for file in sorted(runs_dir.glob("*.json")):
            runs.append(json.loads(file.read_text(encoding="utf-8")))
        jsonl = runs_dir / "runs.jsonl"
        if jsonl.exists():
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    runs.append(json.loads(line))
    return runs


def trajectory_from_run(run: dict[str, Any]) -> dict[str, Any] | None:
    artifacts = run.get("artifacts") or {}
    traj = artifacts.get("collaboration_trajectory")
    if isinstance(traj, dict):
        return traj
    if isinstance(run.get("trajectory"), dict):
        return run["trajectory"]
    return None


def analyze(runs: list[dict[str, Any]]) -> dict[str, Any]:
    scored = []
    orphan_rates: list[float] = []
    for run in runs:
        traj = trajectory_from_run(run)
        if not traj:
            continue
        result = score_trajectory(traj)
        scored.append(result)
        css = result.components.get("css") or {}
        produced = max(1, int(css.get("orphan_count", 0)) + int(round(css.get("artifact_consumption_rate", 0) * 10)))
        # Prefer explicit artifact count when present.
        arts = traj.get("artifacts") or []
        if arts:
            orphan_rates.append(css.get("orphan_count", 0) / max(len(arts), 1))
        else:
            orphan_rates.append(0.0)

    summary = aggregate_trials(scored)
    summary["orphan_rate"] = mean(orphan_rates) if orphan_rates else 0.0
    summary["scored_runs"] = len(scored)
    summary["input_runs"] = len(runs)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, help="runs.jsonl from AegisLoop")
    parser.add_argument("--runs-dir", type=Path, help="Directory of run JSON / runs.jsonl")
    parser.add_argument("--baseline", type=Path, help="Prior drift report JSON")
    parser.add_argument("--report", type=Path, default=Path("/tmp/collab-drift-report.json"))
    parser.add_argument("--max-hard-gate-rate", type=float, default=0.25)
    parser.add_argument("--max-orphan-rate", type=float, default=0.40)
    parser.add_argument("--max-coord-drop", type=float, default=0.15)
    args = parser.parse_args()

    if not args.runs and not args.runs_dir:
        parser.error("provide --runs and/or --runs-dir")

    runs = load_runs(args.runs, args.runs_dir)
    report = analyze(runs)
    report["thresholds"] = {
        "max_hard_gate_rate": args.max_hard_gate_rate,
        "max_orphan_rate": args.max_orphan_rate,
        "max_coord_drop": args.max_coord_drop,
    }

    failures: list[str] = []
    if report["scored_runs"] == 0:
        failures.append("no scoreable trajectories found")
    else:
        if report["hard_gate_failure_rate"] > args.max_hard_gate_rate:
            failures.append(
                f"hard_gate_failure_rate {report['hard_gate_failure_rate']:.3f} > {args.max_hard_gate_rate}"
            )
        if report["orphan_rate"] > args.max_orphan_rate:
            failures.append(f"orphan_rate {report['orphan_rate']:.3f} > {args.max_orphan_rate}")

        if args.baseline and args.baseline.exists():
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
            base_coord = float((baseline.get("mean_vector") or {}).get("coordination") or 0)
            now_coord = float((report.get("mean_vector") or {}).get("coordination") or 0)
            drop = base_coord - now_coord
            report["coordination_drop_vs_baseline"] = drop
            if drop > args.max_coord_drop:
                failures.append(f"coordination drop {drop:.3f} > {args.max_coord_drop}")

    report["failures"] = failures
    report["ok"] = not failures
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        print("collaboration drift check FAILED", file=sys.stderr)
        return 1
    print("collaboration drift check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
