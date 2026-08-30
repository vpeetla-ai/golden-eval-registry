# ADR-0003: PII Flag Granularity — Fixture Drift on `enterprise_rag_golden_v1` / `enterprise_rag_adversarial_v1`

## Status

Accepted — 2026-08-30

## In one breath (panel)

The gate did its job — a real guardrail improvement (per-PII-type flags, not just a generic
"redacted" flag) made two locked fixtures wrong on purpose-correct output. Fixture updated to match
reality, not the other way around.

## Context

`enterprise_rag_platform`'s `redact_pii()` emits `pii_{kind}_redacted` per detected PII span (see
`src/enterprise_rag/core/guardrails.py`) in addition to the coarse `sensitive_input_redacted` flag.
Both `rag-003` (query: "Delete account for jane@example.com") and `adv-jailbreak-hitl-001` (query
contains "evil@example.com") legitimately trigger `pii_email_redacted` now. The locked fixtures in
`enterprise_rag_golden_v1` (v1.0.1) and `enterprise_rag_adversarial_v1` (v1.0.0) still expected the
narrower flag set from before that granularity landed, so CI has been red on `enterprise_rag_platform`
main since the flag-granularity change shipped.

What I refused: leaving a real, correctly-firing CI gate red rather than triaging it, which is exactly
the failure mode ADR-0002 exists to catch — the gate caught a real drift; someone still has to look.

## Decision

1. Add `pii_email_redacted` to `expect.risk_flags` on `rag-003` and `adv-jailbreak-hitl-001`. The
   scorer compares risk flags as a set (`runner.py`), so this is additive, not a reordering.
2. Bump `enterprise_rag_golden_v1` `1.0.1` → `1.0.2`, `enterprise_rag_adversarial_v1` `1.0.0` → `1.0.1`
   — human-directed bugfix on locked suites, the same category ADR-0002 already established as the
   correct way to touch a locked fixture (not silent self-mutation).
3. Verified locally against the real consumer before pushing: `enterprise_rag_platform`'s full
   suite (`pytest tests/ -q` with `GOLDEN_EVAL_REGISTRY_PATH` pointed at this repo) — 63 passed,
   2 skipped, 0 failed, including both previously-red gate tests.

## Consequences

### Positive
- `enterprise_rag_platform` CI returns to green without weakening either suite — the fixture now
  asserts the *more* precise behavior, not a coarser one.
- Reconfirms the gate is doing real work: this is the second time a locked RAG fixture has needed a
  human-directed correction after a real behavior change (see ADR-0002's original fixture bug).

### Negative
- No automated drift-detection caught this before it sat red across several pushes — the status-table
  scraper (`scripts/scrape_status_tables.py`) checks README honesty, not CI badge freshness. That gap
  is the direct motivation for the org-wide CI sweep this ADR is part of.

## Follow-ups
- Consider a lightweight org-wide "any repo currently red" check as a `golden-eval-registry` scheduled
  job, so a fixture drift like this doesn't sit unresolved across multiple pushes again.
