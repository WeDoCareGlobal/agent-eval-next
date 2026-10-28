# Agent Eval — Agent Evaluation & Observability (Next Generation)

> **Engineering focus:** Evaluation, tracing and reproducible agent assessment.
>
> **Evidence boundary:** Local metrics do not establish production performance.
>
> [Project overview](https://www.wedocare-global.com/agent-eval.html) · [Evidence index](https://www.wedocare-global.com/evidence.html) · [Portfolio](https://github.com/WeDoCareGlobal)



[![CI](https://github.com/WeDoCareGlobal/agent-eval-next/actions/workflows/ci.yml/badge.svg)](https://github.com/WeDoCareGlobal/agent-eval-next/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22945804.svg)](https://doi.org/10.5281/zenodo.22945804)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0009--8515--2727-green.svg)](https://orcid.org/0009-0009-8515-2727)
[![We Do Care Global](https://img.shields.io/badge/We%20Do%20Care%20Global-Enterprise%20AI%20Governance-purple.svg)](https://wedocare-global.com/)
[![Pre-release](https://img.shields.io/badge/release-1.0.0--pre.1-blue.svg)](https://github.com/WeDoCareGlobal/agent-eval-next/releases/tag/v1.0.0-pre.1)

**Part of the [We Do Care Global](https://wedocare-global.com/) ecosystem — 6 published systems, Apache-2.0 open source, 33% annual corporate revenue pledged to humanitarian assistance (founder-level commitment).**

---

## Overview

**AgentEval-Next** is a comprehensive **agent evaluation and observability platform** for autonomous AI systems:

- **Real-time token telemetry** — latency, token usage, success rate per agent
- **Tool path tracing** — every tool call traced (allowed / denied / approval) with input/output hashes
- **Error classification** — timeout, policy violation, rate limit, unknown
- **Continuous evaluation suite** — benchmark scenarios tracking RAG/workflow quality over time
- **AgentGuard audit integration** — shared audit log format with `WeDoCareGlobal/agentguard-next`
- **Performance and provider coverage** — must be measured and verified for the configured adapters; no overhead or provider-count guarantee is asserted here

---

## Architecture

```
agent-eval-next/
├── agent_eval/                         # Python package
│   ├── __init__.py                     # Main exports: AgentEval, eval_harness, ToolDecision, ErrorClass, ToolCall, AgentMetrics
│   └── __pycache__/
├── tests/                              # Unit + integration tests
├── docs/                               # Documentation (deployed to GitHub Pages)
├── .zenodo.json                        # Zenodo metadata for DOI minting
├── citation.cff                        # Citation file format
├── CHANGELOG.md
├── CODE_OF_CLAUDE.md
├── LICENSE
├── PROVENANCE.md                       # Source SHA from WeDoCareGlobal-CC/agent-eval
├── pyproject.toml                      # Python package config
└── .github/workflows/                  # CI, Pages, Zenodo, security
```

---

## Quick Start

### Install
```bash
git clone https://github.com/WeDoCareGlobal/agent-eval-next.git
cd agent-eval-next
pip install -e ".[test]"

# Run tests
pytest -v

# Or run the singleton eval harness directly
python -c "
from agent_eval import eval_harness, ToolDecision, ErrorClass
eval_harness.record_tool_call('search', 'agent-1', duration_ms=45.2, decision=ToolDecision.ALLOWED)
eval_harness.record_tool_call('write', 'agent-1', duration_ms=12.1, decision=ToolDecision.DENIED, error=ErrorClass.POLICY_VIOLATION)
print(eval_harness.summary())
"
```

### Use in Your Code
```python
from agent_eval import eval_harness, ToolDecision, ErrorClass

# Record tool calls from your agents
eval_harness.record_tool_call(
    tool_name="web_search",
    agent_id="research-agent-001",
    duration_ms=234.5,
    decision=ToolDecision.ALLOWED,
    input_data={"query": "AI safety"},
    output_data={"results": 10},
)

# Get per-agent metrics
metrics = eval_harness.get_metrics("research-agent-001")
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Avg latency: {metrics['avg_latency_ms']:.1f}ms")

# Get filtered traces
traces = eval_harness.get_traces(agent_id="research-agent-001", decision=ToolDecision.DENIED)

# Ecosystem-wide summary
summary = eval_harness.summary()
print(f"Total agents: {summary['total_agents']}")
print(f"Overall success rate: {summary['overall_success_rate']:.2%}")
```

---

## Core Data Structures

| Class | Purpose |
|-------|---------|
| `ToolDecision` (Enum) | `ALLOWED`, `DENIED`, `APPROVAL` |
| `ErrorClass` (Enum) | `NONE`, `TIMEOUT`, `POLICY_VIOLATION`, `RATE_LIMIT`, `UNKNOWN` |
| `ToolCall` (dataclass) | Single tool call trace: tool, agent, timestamp, duration, decision, input/output hashes, error, metadata |
| `AgentMetrics` (dataclass) | Aggregated metrics: calls, success, tokens, latency, errors, tool usage |
| `AgentEval` | Main harness: records calls, computes metrics, filters traces, ecosystem summary |

---

## Singleton Pattern

The module exports a **singleton** `eval_harness = AgentEval()` for ecosystem-wide use:

```python
from agent_eval import eval_harness
# All agents in your process share the same harness instance
```

---

## AgentGuard Integration

AgentEval uses the **same audit log format** as `WeDoCareGlobal/agentguard-next`:

```python
# AgentGuard records approvals/denials
# AgentEval records the same tool calls with matching decision enum
# → unified audit trail across governance + observability
```

---

## Testing

```bash
# Unit tests
pytest tests/ -v --cov=agent_eval --cov-report=term-missing

# Specific test categories
pytest tests/ -v -m "unit"
pytest tests/ -v -m "integration"
```

---

## CI/CD (`.github/workflows/`)

- **CI** (`ci.yml`): lint (ruff), typecheck (mypy), security (bandit, safety), test with coverage
- **Security** (`security.yml`): Trivy filesystem scan
- **Pages** (`pages.yml`): deploy `docs/` to GitHub Pages
- **Zenodo** (`zenodo.yml`): archive releases to Zenodo, mint DOI, push to ORCID

---

## Release & Archival

Every GitHub release is automatically archived to **Zenodo** (DataCite DOI) and pushed to **ORCID** (0009-0009-8515-2727).

```bash
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 --generate-notes
# → triggers Zenodo workflow → mints DOI → updates ORCID
```

---

## License

Apache-2.0 © 2026 [We Do Care Global](https://wedocare-global.com/) — Emir Perla (ORCID: 0009-0009-8515-2727)

33% of profits → humanitarian aid.

---

## Citation

```bibtex
@software{perla2026agenteval,
  author = {Perla, Emir},
  title = {Agent Eval — Agent Evaluation & Observability Platform},
  version = {1.0.0-pre.1},
  year = {2026},
  doi = {10.5281/zenodo.22945804},
  url = {https://github.com/WeDoCareGlobal/agent-eval-next}
}
```

---

## WDCG Ecosystem

| System | Repo | Purpose |
|--------|------|---------|
| **AgentGuard** | `WeDoCareGlobal/agentguard-next` | Security & governance control plane |
| **FoundationCentar** | `WeDoCareGlobal/FoundationCentar-Next` | One-Click Agent Factory |
| **Enterprise Hybrid-RAG** | `WeDoCareGlobal/enterprise-hybrid-rag-next` | Hybrid retrieval |
| **Agent Eval** | `WeDoCareGlobal/agent-eval-next` | **This repo** — Evaluation & observability |
| **AgentVault** | `WeDoCareGlobal/AgentVault-Next` | Tool registry & assurance |
| **Pharma Intelligence OS** | `WeDoCareGlobal/Pharma-Intelligence-Os-Next` | Regulatory intelligence |