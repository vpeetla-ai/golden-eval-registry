# Golden Eval Registry


<!-- vpeetla-tech-stack:start -->
[![YAML](https://img.shields.io/badge/YAML-CB171E?style=flat-square)]() [![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square)]() [![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat-square)]() [![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-181717?style=flat-square)]()
<!-- vpeetla-tech-stack:end -->
[![CI](https://github.com/vpeetla-ai/golden-eval-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/vpeetla-ai/golden-eval-registry/actions/workflows/ci.yml)
[![Org](https://img.shields.io/badge/GitHub-vpeetla--ai-blue)](https://github.com/vpeetla-ai)

Versioned golden fixtures for the **vpeetla-ai governed agent stack**.

[Case study](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/case-studies/golden-eval-registry.md) · [Architecture](docs/ARCHITECTURE.md) · [Repo index](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/REPO_INDEX.md)

## What this is

Live demos prove the systems run. Golden evals prove they do not regress.

Each platform already had local tests:

- Enterprise RAG had golden retrieval queries.
- LoopForge had benchmark questions and a repo-fix fixture.
- AegisLoop had mission quality gates.
- Content Factory had HITL and gateway graph tests.

This repo makes those evaluation contracts portable, reviewable, and versioned.

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
  loopforge_benchmark_v1/
  loopforge_repo_fix_v1/
  aegisloop_mission_gates_v1/
  content_factory_graph_v1/
src/golden_eval_registry/
  schema.py
  validate.py
```

## Validate

```bash
python -m golden_eval_registry.validate
pytest -q
```

## Suite kinds

| Kind | Consumer |
|------|----------|
| `rag_answer` | `enterprise_rag_platform`, AegisLoop import |
| `harness_qa` | `loop-engine-agent-platform` |
| `repo_fix` | LoopForge repo-fix loop |
| `mission_gate` | `aegisloop-agentops-workbench` |
| `graph_hitl` | `ai-content-factory` |
| `brief_gate` | `sentinel-brief` |

## Trade-offs

| Choice | Why | Cost |
|--------|-----|------|
| JSON + JSONL | No runtime dependencies | Less expressive than YAML |
| Fixture registry first | Safe, portable, reviewable | Cross-repo runners come next |
| Locked eval files | Prevent metric cheating | Updates require review |

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Related

- [ORG_REVIEW_2026](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/docs/ORG_REVIEW_2026.md)
- [ADR-007 Agent Protocol Stack](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-007-2026-agent-protocol-stack.md)
- [Enterprise RAG ADR-0003](https://github.com/vpeetla-ai/enterprise_rag_platform/blob/main/docs/adr/0003-versioned-evaluation-gates.md)
