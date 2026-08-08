# ADR-0001: Versioned Golden Eval Registry

## Status

Accepted — 2026-07-01

## In one breath (panel)

I'd put golden fixtures in one versioned registry repos can import — demos prove it runs; locked suites prove it didn't regress.

## Context

Evals already existed, scattered:

- Enterprise RAG golden queries
- LoopForge benchmark QA and repo-fix fixtures
- AegisLoop mission gates
- Content Factory HITL / gateway tests

Portfolio-level regression was hard to inspect. Copy-paste JSONL across repos drifts.

What I refused: "we have tests in each repo" as a substitute for a shared, reviewable contract.

## Decision

Create `golden-eval-registry` with versioned suite manifests and JSONL cases. Consumers import suites and decide how to execute them locally.

**v1 honesty:** validate fixtures first; real scoring + consumer CI came in ADR-0002 — don't claim the registry "gates production" until a consumer actually runs `score_suite`.

## Consequences

### Positive

- One source of truth for golden fixtures
- Demos plus eval contracts — both visible to a panel
- `locked: true` suites resist autonomous agents gaming their own loop

### Negative

- Sync discipline when consumer schemas evolve
- v1 was fixture-only until ADR-0002 wired scorers

## Follow-ups

- (Partial done in ADR-0002) scorers + consumer CI gates
- Remaining kinds / matrix badge as consumers wire
