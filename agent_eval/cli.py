"""
Agent Eval CLI — Typer entry point for the evaluation harness.

Exposes:
  agent-eval record --tool <name> --agent <id> --duration-ms <n> --decision <allowed|denied|approval>
  agent-eval summary [--agent <id>]
  agent-eval compare --agent-a <id> --agent-b <id> [--metric duration_ms|tokens] [--alpha 0.05]
  agent-eval golden-path --agent <id> --cases <json>
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import typer

from agent_eval import (
    AgentEval,
    ErrorClass,
    ToolDecision,
    eval_harness,
)

app = typer.Typer(add_completion=False, help="Agent Eval — agent evaluation & observability CLI")
cli = app  # back-compat alias


def _decision(value: str) -> ToolDecision:
    try:
        return ToolDecision[value.upper()]
    except KeyError:
        typer.secho(f"Invalid decision: {value} (use allowed, denied, approval)", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _error(value: str) -> ErrorClass:
    try:
        return ErrorClass[value.upper()]
    except KeyError:
        typer.secho(f"Invalid error class: {value} (use none, timeout, policy_violation, rate_limit, unknown)", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def record(
    tool: str = typer.Option(..., "--tool", help="Tool name"),
    agent: str = typer.Option(..., "--agent", help="Agent ID"),
    duration_ms: float = typer.Option(0.0, "--duration-ms", help="Call duration in ms"),
    decision: str = typer.Option("allowed", "--decision", help="allowed | denied | approval"),
    error: str = typer.Option("none", "--error", help="none | timeout | policy_violation | rate_limit | unknown"),
    metadata: Optional[str] = typer.Option(None, "--metadata", help="JSON metadata string"),
) -> None:
    """Record a single tool call into the harness."""
    meta = json.loads(metadata) if metadata else {}
    call = eval_harness.record_tool_call(
        tool_name=tool,
        agent_id=agent,
        duration_ms=duration_ms,
        decision=_decision(decision),
        error=_error(error),
        metadata=meta,
    )
    typer.secho(f"Recorded {call.tool_name} for {call.agent_id}: {call.decision.value}", fg=typer.colors.GREEN)


@app.command()
def summary(
    agent: Optional[str] = typer.Option(None, "--agent", help="Agent ID (omit for ecosystem summary)"),
) -> None:
    """Print evaluation metrics (JSON)."""
    data = eval_harness.get_metrics(agent) if agent else eval_harness.summary()
    typer.echo(json.dumps(data, indent=2, default=str))


@app.command()
def compare(
    agent_a: str = typer.Option(..., "--agent-a", help="First agent ID"),
    agent_b: str = typer.Option(..., "--agent-b", help="Second agent ID"),
    metric: str = typer.Option("duration_ms", "--metric", help="duration_ms | tokens"),
    alpha: float = typer.Option(0.05, "--alpha", help="Significance threshold"),
) -> None:
    """Compare two agents with Welch's t-test (JSON)."""
    try:
        res = eval_harness.compare_agents(agent_a, agent_b, metric=metric, alpha=alpha)
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(res, indent=2, default=str))


@app.command()
def golden_path(
    agent: str = typer.Option(..., "--agent", help="Agent ID"),
    cases: str = typer.Option(..., "--cases", help="JSON list of {tool, duration_ms, decision, error}"),
) -> None:
    """Run a golden-path test suite for an agent (JSON)."""
    case_list = json.loads(cases)
    # AgentEval has no golden_path; record each case manually, then read metrics.
    for case in case_list:
        eval_harness.record_tool_call(
            tool_name=case["tool"],
            agent_id=agent,
            duration_ms=case.get("duration_ms", 0.0),
            decision=_decision(case.get("decision", "allowed")),
            error=_error(case.get("error", "none")),
        )
    metrics = eval_harness.get_metrics(agent)
    typer.echo(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    app()
