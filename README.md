# Golden Eval Registry


<!-- vpeetla-tech-stack:start -->
[![YAML](https://img.shields.io/badge/YAML-CB171E?style=flat-square)]() [![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square)]() [![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat-square)]() [![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-181717?style=flat-square)]()
<!-- vpeetla-tech-stack:end -->
[![CI](https://github.com/vpeetla-ai/golden-eval-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/vpeetla-ai/golden-eval-registry/actions/workflows/ci.yml)
[![Org](https://img.shields.io/badge/GitHub-vpeetla--ai-blue)](https://github.com/vpeetla-ai)

**Job of the system:** hold versioned golden fixtures the stack's repos import and score in CI — live demos prove the systems run; these suites prove they don't quietly regress.

[Case study](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/case-studies/golden-eval-registry.md) · [Architecture](docs/ARCHITECTURE.md) · [Repo index](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/REPO_INDEX.md)

## What this is

Demos show green paths. Goldens catch the scar: a fixture that never ran, a guardrail that redacts the only grounding token, a mission gate that drifted.

Each platform already had local tests. This repo makes those contracts portable, reviewable, and versioned — and `runner.py` scores real consumer output, not just YAML shape ([ADR-0002](docs/adr/0002-real-scorer-and-first-ci-gate.md)).

## Who this serves

| Persona | Job-to-be-done |
|---------|----------------|
| AI platform architect | Prove agent systems regress safely across repos |
| Hiring panel / reviewer | Inspect objective eval fixtures, not just demos |
| Repo maintainer | Import stable fixtures without copying ad hoc test data |

## Registry layout

```text
suites/
  enterprise_rag_golden_v1/
  enterprise_rag_adversarial_v1/
  loopforge_benchmark_v1/
  loopforge_repo_fix_v1/
  aegisloop_mission_gates_v1/
  content_factory_graph_v1/
  domainforge_triage_preference_v1/
src/golden_eval_registry/
  schema.py
  validate.py
  runner.py
```

## Implementation status

| Component | Status | Notes |
|-----------|--------|-------|
| Versioned golden suites | ✅ | `suites/` + `registry.json` |
| Schema validate + score_case | ✅ | `python -m golden_eval_registry.validate` · `runner.score_*` |
| Consumer CI gates | ✅ | Spine + AgentOps consumers wire critical suites as merge gates — see Suite kinds table |
| Status table scraper | ✅ | `scripts/scrape_status_tables.py` (+ `--json` overnight artifact) |
| Observability status gate | ✅ | Spine/AgentOps READMEs must mention `observability/status` (GER library exempt) |

## Status table scraper (M5)

Sibling READMEs should keep an honest Implementation status section. From a machine with local clones:

```bash
python scripts/scrape_status_tables.py
python scripts/scrape_status_tables.py --json /tmp/ger-status-scrape.json
```

Covers ACF, AegisAI, VAP, ERAG, LoopForge, AegisLoop, Sentinel, Agent FinOps, LLM gateway, semantic cache, and this registry.

Fails if AegisAI still claims ACF publish is Planned, ACF still claims native R2 attach is missing, if a tracked README lacks a status section, or if a spine/AgentOps README omits `observability/status`.

## Stage-4 continuous eval

| Tool | Purpose |
|------|---------|
| `scripts/promote_failure.py` | Turn a failed mission JSON into a redacted GER candidate under `suites/multi_agent_collaboration_v1/candidates/` |
| `scripts/collaboration_drift.py` | Score persisted trajectories; fail on hard-gate / orphan / coordination drift |
| `.github/workflows/collaboration-drift.yml` | Weekly drift check (suite trajectories + optional AegisLoop run log) |

```bash
python scripts/promote_failure.py --run path/to/mission.json
python scripts/collaboration_drift.py --runs path/to/runs.jsonl --report /tmp/drift.json
```

`validate.py` checks manifests and JSONL cases are well-formed. `runner.py`'s `score_case`/
`score_suite` go further — they compare a consumer repo's *real* output against a case's
`expect` block, per kind. This registry stays dependency-light and provider-agnostic on
purpose: each consumer already knows how to reach itself (an HTTP client, a direct function
import, ...) and hands the real output here for scoring, rather than this repo embedding
provider-specific client code.

## Suite kinds

| Kind | Consumer | Real CI gate? |
|------|----------|----------------|
| `rag_answer` | `enterprise_rag_platform`, AegisLoop import | ✅ `enterprise_rag_platform`'s CI checks this repo out and runs the suite against a real, isolated `RagPipeline`, failing the build on regression |
| `adversarial_security` | `enterprise_rag_platform` | ✅ CI runs `enterprise_rag_adversarial_v1` — principal spoof + prompt-injection / jailbreak retrieval must not cite or leak restricted docs |
| `harness_qa` | `loop-engine-agent-platform` | ✅ CI runs `loopforge_benchmark_v1` against real `AgentHarness` + MockLLM |
| `repo_fix` | LoopForge repo-fix loop | ✅ CI runs `loopforge_repo_fix_v1` against real `run_repo_fix` |
| `mission_gate` | `aegisloop-agentops-workbench` | ✅ `aegisloop-agentops-workbench`'s CI checks this repo out and runs the suite against the real `runtime.evaluate()` gate, failing the build on regression |
| `graph_hitl` | `ai-content-factory` | ✅ CI runs `content_factory_graph_v1` against publish node behavior |
| `brief_gate` | `sentinel-brief` | ✅ CI runs `sentinel_brief_gate_v1` against `evaluate_brief()` |
| `triage_preference` | `domainforge-rag-peft` | ✅ CI runs `domainforge_triage_preference_v1` against alignment scorer |
| `router_invariant` | `venkat-ai-platform`, `aegisai-enterprise-agent-platform`, `agent-finops`, `react-agent-pattern`, `swarm-agent-pattern` | ✅ VAP orchestrator map · AegisAI gateway vocab/passport · FinOps outcome KPI vocab · **Acme embed panel break tests** (`acme.embed_invariant_v1`) · **ReAct bounded-loop safety** (`react_agent_pattern.bounded_loop_v1` — bounded vs unbounded `max_steps`, real trials against `ReActAgent`) · **Swarm fan-out vs serial** (`swarm_agent_pattern.fanout_v1` — coverage-per-round vs invocation-efficiency, real trials against `SwarmRuntime`) |
| `collaboration_scorecard` | `aegisloop-agentops-workbench`, this registry | ✅ CSS / TUE vector + hard gates (contradiction, escalation bypass); suite self-scores in GER CI; AegisLoop builds live trajectories |

See [ADR-0002](docs/adr/0002-real-scorer-and-first-ci-gate.md) — the first suite ever actually
executed (`enterprise_rag_golden_v1`) immediately surfaced a real bug in its own fixture,
now fixed.

## Trade-offs

| Choice | Why | Cost |
|--------|-----|------|
| JSON + JSONL | No runtime dependencies | Less expressive than YAML |
| Fixture registry first, then real scorers | Safe, portable, reviewable — suite kinds gate real CI across platform repos (ADR-014+) | Registry stays dependency-light; consumers own execution adapters |
| Locked eval files | Prevent metric cheating (by autonomous agents gaming their own loop, not one-time human review) | Updates require a disclosed, versioned review — see ADR-0002 |

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Interview map

**Business function:** Versioned golden eval fixtures and scorers — portable CI gates across the stack.

Staff+ prep crosswalk — [playbook](https://github.com/vpeetla-ai/ai-architect-interview-playbook) · [study UI](https://ai-architect-interview-playbook.vercel.app) · [Practice Arena](https://ai-architect-practice-arena.vercel.app) · [org matrix](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/REPO_INTERVIEW_MAP.md). Only entries this repo honestly exercises.

| Category | Entry | Fit |
|----------|-------|-----|
| System design | [LLM eval & observability](https://ai-architect-interview-playbook.vercel.app/q/ai-system-design/07-llm-evaluation-observability-platform/) ([md](https://github.com/vpeetla-ai/ai-architect-interview-playbook/blob/main/ai-system-design/07-llm-evaluation-observability-platform.md)) | Primary — fixtures as release artifacts |
| Trade-offs | [Build vs buy shared services](https://ai-architect-interview-playbook.vercel.app/q/scalability-governance-tradeoffs/02-build-vs-buy-shared-services/) ([md](https://github.com/vpeetla-ai/ai-architect-interview-playbook/blob/main/scalability-governance-tradeoffs/02-build-vs-buy-shared-services.md)) | Shared registry vs per-repo ad hoc tests |

## Related

- [ORG_REVIEW_2026](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/ORG_REVIEW_2026.md)
- [ADR-007 Agent Protocol Stack](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-007-2026-agent-protocol-stack.md)
- [Enterprise RAG ADR-0003](https://github.com/vpeetla-ai/enterprise_rag_platform/blob/main/docs/adr/0003-versioned-evaluation-gates.md)
