# ADR-0002: Real Scorer + First Consumer CI Gates

## Status

Accepted — 2026-07-04

## In one breath (panel)

I'd score a consumer's *real* output against `expect` in CI — validating JSON shape is not the same as proving retrieval or mission gates still work.

## Context

ADR-0001 left "cross-repo execution" as future work. `validate.py` checked manifests were well-formed and never ran a case. First real run of `enterprise_rag_golden_v1` immediately found a fixture bug: after PII redaction, a destructive-action query shared no vocabulary with `policy-001.json`, so `grounded: true` + cite expectations were fantasy. The case had never been executed for real.

What I refused: a green "eval registry" badge that only linted YAML.

## Decision

1. `runner.py`: `score_case` / `score_suite` compare real consumer output to `expect`, per `kind`. Dependency-light — consumers hand us output; we don't embed their HTTP clients.
2. Honor `corpus_path` on manifests (was silently dropped).
3. Fix the fixture; bump suite `1.0.0` → `1.0.1`. Human-directed bugfix on first execution — not the silent self-mutation `locked` exists to stop.
4. Wire consumer CI: Enterprise RAG against an isolated `RagPipeline`; AegisLoop against real `evaluate()`. Fail the build on regression.

**Honesty:** other kinds gained gates over time in consumer workflows — see README table. This ADR's scar is the first two; don't invent pass-rate SLOs.

## Consequences

### Positive

- Closes the gap ADR-0001 named
- First execution found a real fixture bug — proof that "fixtures exist" ≠ "fixtures are correct"
- Unsupported kinds raise clearly instead of silent no-op

### Negative

- RAG gate uses an isolated pipeline (not the deployed FastAPI singleton with demo seed pollution) — real logic, not an HTTP round-trip to prod
- No single org-wide matrix dashboard yet — each consumer checks this repo out itself

## Follow-ups

- Scorers + CI for remaining kinds as consumers land
- Optional aggregated status badge
