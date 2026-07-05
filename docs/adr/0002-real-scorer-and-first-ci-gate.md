# ADR-0002: Real Scorer + First Consumer CI Gates

## Status

Accepted — 2026-07-04

## Context

[ADR-0001](./0001-versioned-golden-eval-registry.md) explicitly named this as future work: "v1
validates fixtures only; cross-repo execution is future work" and "Add GitHub Action matrix that
runs consumer repo adapters." `validate.py` checks that manifests and JSONL cases are well-formed
— it never executes a case against anything, so no suite had ever actually been run against a real
consumer's real behavior.

Running `enterprise_rag_golden_v1` for real, for the first time, immediately surfaced a genuine
bug in the fixture itself: `corpus/policy-001.json`'s body shared no vocabulary with a
destructive/PII-bearing query ("Delete account for jane@example.com") once the guardrail layer
redacted the email — the redacted query ("Delete account for [REDACTED_EMAIL]") couldn't ground
against a single-document corpus about "hybrid retrieval, grounded citations... human approval for
high-risk actions." The case's `expect` block (`grounded: true`, cites `policy-001`) had apparently
never been checked against real retrieval behavior before.

## Decision

1. Add `src/golden_eval_registry/runner.py`: `score_case`/`score_suite` compare a consumer's real
   output against a case's `expect` block, per `kind`. Deliberately **dependency-light and
   provider-agnostic** — this registry doesn't gain an `httpx` dependency or provider-specific
   client code; each consumer already knows how to reach itself and hands the real output here
   for scoring.
2. `SuiteManifest` gains an optional `corpus_path` (the manifest's `"corpus"` key existed in the
   JSON but was silently dropped by `parse_manifest`).
3. Fixed the `enterprise_rag_golden_v1` fixture bug found above: `corpus/policy-001.json`'s body
   now also covers destructive-action handling ("Requests to delete a user account or perform
   other destructive actions must be routed through human approval before execution"), and the
   suite version bumped `1.0.0` → `1.0.1` to signal the fixture content changed. This is a
   deliberate, disclosed correction of a fixture that had never been executed for real — not the
   kind of silent self-mutation `locked: true` exists to prevent (that guards against
   *autonomous agents* gaming their own eval loop, not a one-time human-directed bug fix on first
   real execution).
4. Wired two real consumer CI gates: `enterprise_rag_platform`'s CI checks out this repo and runs
   `enterprise_rag_golden_v1` against a real, isolated `RagPipeline`; `aegisloop-agentops-
   workbench`'s CI checks out this repo and runs `aegisloop_mission_gates_v1` against the real
   `evaluate()` gate function. Both fail their build on regression.

## Consequences

### Positive
- Closes the exact gap ADR-0001 named as future work.
- Found and fixed a real bug the very first time a suite was actually executed — direct proof
  that "fixtures exist" and "fixtures are correct" are different claims, and only execution
  proves the second one.
- Still only 2 of 6 kinds (`rag_answer`, `mission_gate`) have a real scorer and a real consumer
  gate — the other 4 (`harness_qa`, `repo_fix`, `graph_hitl`, `brief_gate`) remain fixture-only,
  and `score_case` raises a clear error for them rather than silently no-op'ing.

### Negative
- `enterprise_rag_platform`'s gate tests an isolated `RagPipeline`, not the deployed FastAPI
  singleton — the singleton also seeds unrelated demo content that would otherwise pollute
  retrieval ranking against the suite's own corpus. Real pipeline/guardrail logic either way,
  just not an HTTP round-trip against the exact production process.
- No cross-repo CI matrix yet (ADR-0001's other follow-up) — each consumer's own workflow checks
  out this repo individually; there's no single dashboard aggregating pass/fail across all
  consumers.

## Follow-ups
- Implement scorers + wire consumer CI for the remaining 4 kinds.
- A GitHub Action matrix / status badge aggregating results across all consumer repos.
