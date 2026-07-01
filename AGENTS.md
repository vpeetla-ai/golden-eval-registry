# Agent Instructions — golden-eval-registry

This repo stores **locked golden eval fixtures**, not product runtime code.

## Rules

- Keep suite manifests versioned and `locked: true`.
- Do not add live LLM/API calls to validation.
- Prefer stdlib Python; registry validation must stay dependency-light.
- Any new suite must include:
  - `manifest.json`
  - `cases.jsonl`
  - at least one pytest assertion
  - consumer repo listed explicitly

## Test

```bash
python -m golden_eval_registry.validate
pytest -q
```

## Safety

Agents may propose new cases, but humans own threshold and fixture updates. Treat suite data like `prepare.py` in Karpathy-style autoresearch: the agent should not silently edit the metric it is trying to pass.
