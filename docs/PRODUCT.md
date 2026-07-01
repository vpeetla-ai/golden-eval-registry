# Product Framing — Golden Eval Registry

## Who we serve

| Persona | Pain today | What this repo provides |
|---------|------------|-------------------------|
| Platform maintainer | Golden fixtures are scattered across repos | One versioned registry |
| Principal AI architect | Hard to show regression discipline across stack | Inspectable suite manifests |
| Hiring panel | Demos may look impressive but hide quality gaps | Objective eval contracts |

## Job-to-be-done

> "Before I change an agent system, show me the golden cases it must still satisfy."

## Customer problem

The vpeetla-ai org has live systems for orchestration, governance, RAG, AgentOps, content, loops, and inference. Each system had useful tests, but the evaluation contracts were local. That makes the stack harder to audit as one product.

Golden Eval Registry turns local test wisdom into a reusable artifact.

## Success metrics

| Metric | Target |
|--------|--------|
| Registry validation | `python -m golden_eval_registry.validate` passes |
| Suite coverage | At least one suite for RAG, loops, mission gates, HITL |
| Consumer clarity | Every case declares `consumer_repos` and `kind` |
| Safety | `locked: true` on all suite manifests |

## Trade-offs

| Decision | Why | Cost |
|----------|-----|------|
| Fixture registry first | Lowest-risk cross-repo value | Runners still live in consumer repos |
| JSONL cases | Append-friendly and diffable | Less ergonomic than YAML |
| No live URL checks | Keeps evals deterministic | Portfolio CI handles URL health |

## Future

- GitHub Action matrix that checks each consumer repo against the registry
- Markdown report artifact for portfolio badge
- VAP routing evals and pattern trace fixtures
