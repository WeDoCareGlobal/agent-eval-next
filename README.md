# Agent Eval — Agent Evaluation & Observability

Agent evaluation harness and observability dashboard. Measures agent performance
(latency, token usage, success rate, error classification per agent) and traces
every tool call (allowed / denied / approval). Includes a continuous evaluation
suite for RAG and workflow outputs.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0009--8515--2727-green.svg)](https://orcid.org/0009-0009-8515-2727)
[![DataCite ORCID](https://img.shields.io/badge/DataCite%20ORCID-0009--0009--8515--2727-blue.svg)](https://commons.datacite.org/orcid.org/0009-0009-8515-2727)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22945804.svg)](https://doi.org/10.5281/zenodo.22945804)
[![We Do Care Global](https://img.shields.io/badge/We%20Do%20Care%20Global-Enterprise%20AI%20Governance-purple.svg)](https://wedocare-global.com/)

Part of the [We Do Care Global](https://wedocare-global.com/) ecosystem — 6 published systems, Apache-2.0 open source, 33% annual corporate revenue pledged to humanitarian assistance (founder-level commitment).

## Features

- Agent Metrics — latency, token usage, success rate, error classification
- Tool Observability — trace every call with input/output and decision
- Continuous Eval — benchmark scenarios tracking RAG quality over time
- Audit Integration — audit log format shared with AgentGuard

## Quickstart

```bash
git clone https://github.com/WeDoCareGlobal/agent-eval-next.git
cd agent-eval-next
pip install -e .
pytest
```

## Architecture

- Python package (installable with `pip install -e .`)
- Web dashboard deployed via `docs/` on GitHub Pages
- Integration point: audit log format aligned with AgentGuard

## Metadata

- License: Apache 2.0
- ORCID: 0009-0009-8515-2727
- Citation: see `citation.cff`
- Zenodo archive: `.zenodo.json`
- Version: v0.1.2

