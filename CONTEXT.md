# golden-eval-registry Context

## Purpose

Versioned golden eval fixtures for the vpeetla-ai governed agent stack.

## Consumer repos

| Suite | Consumer |
|-------|----------|
| `enterprise_rag.golden_v1` | enterprise_rag_platform, AegisLoop |
| `loopforge.benchmark_v1` | loop-engine-agent-platform |
| `loopforge.repo_fix_v1` | loop-engine-agent-platform |
| `aegisloop.mission_gates_v1` | aegisloop-agentops-workbench |
| `content_factory.graph_v1` | ai-content-factory |

## Core terms

- **Golden eval**: locked fixture + expectation + threshold.
- **Consumer repo**: product repo that imports and executes a suite.
- **Locked eval**: fixture that agents must not change to make themselves pass.

## Boundary

This repo validates fixture quality. It does not call live demos, live LLMs, or customer APIs.
