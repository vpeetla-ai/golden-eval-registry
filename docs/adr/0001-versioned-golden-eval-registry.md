# ADR-0001: Versioned Golden Eval Registry

## Status

Accepted — 2026-07-01

## Context

The org already has evals, but they are split across platform repos:

- Enterprise RAG golden queries
- LoopForge benchmark QA and repo-fix fixtures
- AegisLoop mission gate tests
- Content Factory HITL and gateway tests

This makes portfolio-level regression discipline hard to inspect.

## Decision

Create a dedicated `golden-eval-registry` repo with versioned suite manifests and JSONL cases. Consumer repos import suites and decide how to execute them locally.

## Consequences

### Positive

- Clear source of truth for golden fixtures
- Easier portfolio proof: demos plus eval contracts
- Safer long-running loops because golden files are locked

### Negative

- Requires sync discipline when consumer schemas evolve
- v1 validates fixtures only; cross-repo execution is future work

## Follow-ups

- Add VAP router and pattern trace suites
- Add GitHub Action matrix that runs consumer repo adapters
- Generate markdown report for portfolio badge
