# SPDX-License-Identifier: Apache-2.0
# Derived from WeDoCareGlobal-CC/agent-eval; source SHA recorded in PROVENANCE.md.
"""
Agent Eval — Agent Evaluation & Observability
We Do Care Global — Unified Ecosystem

Measures agent performance (latency, token usage, success rate, error classification)
and traces every tool call (allowed / denied / approval).
"""

import threading
import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone


class ToolDecision(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    APPROVAL = "approval"


class ErrorClass(Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    POLICY_VIOLATION = "policy_violation"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


@dataclass
class ToolCall:
    """Single tool call trace."""
    tool_name: str
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    decision: ToolDecision = ToolDecision.ALLOWED
    input_hash: str = ""
    output_hash: str = ""
    error: ErrorClass = ErrorClass.NONE
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Aggregated metrics for an agent."""
    agent_id: str
    total_calls: int = 0
    successful_calls: int = 0
    allowed_calls: int = 0
    denied_calls: int = 0
    approval_calls: int = 0
    total_tokens: int = 0
    token_observations: int = 0
    total_latency_ms: float = 0.0
    errors: dict = field(default_factory=lambda: {e.value: 0 for e in ErrorClass})
    tool_usage: dict = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.total_calls, 1)

    @property
    def success_rate(self) -> float:
        return self.successful_calls / max(self.total_calls, 1)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "allowed_calls": self.allowed_calls,
            "denied_calls": self.denied_calls,
            "approval_calls": self.approval_calls,
            "total_tokens": self.total_tokens if self.token_observations else None,
            "token_observations": self.token_observations,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "success_rate": round(self.success_rate, 4),
            "errors": self.errors,
            "tool_usage": self.tool_usage,
            "last_updated": self.last_updated,
        }


class AgentEval:
    """Main evaluation harness.

    Thread-safe: all shared state (metrics, traces) is protected by a reentrant
    lock so concurrent record_tool_call() calls from multiple workers are safe.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._metrics: dict[str, AgentMetrics] = {}
        self._traces: list[ToolCall] = []

    def record_tool_call(
        self,
        tool_name: str,
        agent_id: str,
        duration_ms: float = 0.0,
        decision: ToolDecision = ToolDecision.ALLOWED,
        input_data: Any = None,
        output_data: Any = None,
        error: ErrorClass = ErrorClass.NONE,
        metadata: Optional[dict] = None,
    ) -> ToolCall:
        """Record a single tool call. Thread-safe."""
        # Token usage must be observed, not inferred from missing metadata.
        tokens = (metadata or {}).get("tokens")
        if tokens is not None and (isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0):
            raise ValueError("metadata.tokens must be a non-negative integer or omitted")
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            call = ToolCall(
                tool_name=tool_name,
                agent_id=agent_id,
                duration_ms=duration_ms,
                decision=decision,
                input_hash=self._hash(input_data),
                output_hash=self._hash(output_data),
                error=error,
                metadata=metadata or {},
            )
            self._traces.append(call)

            # Update metrics
            if agent_id not in self._metrics:
                self._metrics[agent_id] = AgentMetrics(agent_id=agent_id)

            m = self._metrics[agent_id]
            m.total_calls += 1
            m.total_latency_ms += duration_ms
            if tokens is not None:
                m.total_tokens += tokens
                m.token_observations += 1
            m.last_updated = now

            if decision == ToolDecision.ALLOWED:
                m.allowed_calls += 1
            elif decision == ToolDecision.DENIED:
                m.denied_calls += 1
            elif decision == ToolDecision.APPROVAL:
                m.approval_calls += 1

            if decision == ToolDecision.ALLOWED and error == ErrorClass.NONE:
                m.successful_calls += 1

            if error != ErrorClass.NONE:
                m.errors[error.value] += 1

            m.tool_usage[tool_name] = m.tool_usage.get(tool_name, 0) + 1

            return call

    def get_metrics(self, agent_id: Optional[str] = None) -> dict:
        """Get metrics for one or all agents"""
        if agent_id:
            if agent_id in self._metrics:
                return self._metrics[agent_id].to_dict()
            return {}
        return {aid: m.to_dict() for aid, m in self._metrics.items()}

    def get_traces(
        self,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        decision: Optional[ToolDecision] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get tool call traces with optional filtering. Thread-safe."""
        with self._lock:
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                raise ValueError("limit must be a positive integer")
            traces = self._traces
            if agent_id:
                traces = [t for t in traces if t.agent_id == agent_id]
            if tool_name:
                traces = [t for t in traces if t.tool_name == tool_name]
            if decision:
                traces = [t for t in traces if t.decision == decision]
            return [{**asdict(t), "decision": t.decision.value, "error": t.error.value} for t in traces[-limit:]]

    def compare_agents(
        self,
        agent_a: str,
        agent_b: str,
        metric: str = "duration_ms",
        alpha: float = 0.05,
    ) -> dict[str, object]:
        """Compare two agents' measurements using Welch's t-test.

        Extracts per-call measurements for each agent from the trace store,
        runs welch_ttest, and returns the result dict plus a human-readable
        significance verdict.

        Raises ValueError if a metric is unsupported or an agent has no traces.
        """
        metric_keys = {
            "duration_ms": "duration_ms",
            "latency_ms": "duration_ms",
            "tokens": "total_tokens",
        }
        if metric not in metric_keys:
            raise ValueError(f"unsupported metric: {metric}")

        traces_a = [t for t in self._traces if t.agent_id == agent_a]
        traces_b = [t for t in self._traces if t.agent_id == agent_b]
        if not traces_a or not traces_b:
            raise ValueError(f"need traces for both agents; got {len(traces_a)} / {len(traces_b)}")

        if metric == "tokens":
            if any(t.metadata.get("tokens") is None for t in traces_a + traces_b):
                raise ValueError("token comparison requires observed token counts for every trace")
            values_a = [t.metadata["tokens"] for t in traces_a]
            values_b = [t.metadata["tokens"] for t in traces_b]
        else:
            values_a = [t.duration_ms for t in traces_a]
            values_b = [t.duration_ms for t in traces_b]

        from .statistics import welch_ttest
        res = welch_ttest(values_a, values_b, alpha=alpha)

        res["agent_a"] = agent_a
        res["agent_b"] = agent_b
        res["metric"] = metric
        res["verdict"] = "significant" if res["significant"] else "not_significant"

        return res

    def summary(self) -> dict:
        """Get ecosystem-wide summary. Thread-safe."""
        with self._lock:
            all_metrics = list(self._metrics.values())
            total_calls = sum(m.total_calls for m in all_metrics)
            total_allowed = sum(m.allowed_calls for m in all_metrics)
            total_successful = sum(m.successful_calls for m in all_metrics)
            total_denied = sum(m.denied_calls for m in all_metrics)
            total_approval = sum(m.approval_calls for m in all_metrics)
            total_tokens = sum(m.total_tokens for m in all_metrics)
            token_observations = sum(m.token_observations for m in all_metrics)
            total_latency = sum(m.total_latency_ms for m in all_metrics)

            return {
                "total_agents": len(self._metrics),
                "total_calls": total_calls,
                "allowed_calls": total_allowed,
                "denied_calls": total_denied,
                "approval_calls": total_approval,
                "total_tokens": total_tokens if token_observations else None,
                "token_observations": token_observations,
                "avg_latency_ms": round(total_latency / max(total_calls, 1), 2),
                "overall_success_rate": round(total_successful / max(total_calls, 1), 4),
                "agents": {aid: m.to_dict() for aid, m in self._metrics.items()},
            }

    @staticmethod
    def _hash(data: Any) -> str:
        """Create deterministic hash of data."""
        if data is None:
            return ""
        try:
            return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
        except (TypeError, ValueError, OverflowError):
            return hashlib.sha256(str(data).encode()).hexdigest()[:16]


# Singleton instance for ecosystem-wide use
# NOTE: Shared across the entire process. For multi-process isolation, use a
# dedicated AgentEval instance per worker instead of this module-level singleton.
eval_harness = AgentEval()

# ------------------------------------------------------------------
# Unified observability harness (Step 10)
# ------------------------------------------------------------------
class UnifiedObservabilityHarness:
    """Step 10: All-in-one unified observability harness for AgentEval.

    Combines:
    - Golden-path / adversarial test provisioning
    - Statistical comparison (Welch's t-test)
    - OpenTelemetry tracing attribution
    - Unified summary export (JSON, CSV, dashboard-ready)

    Usage:
        harness = UnifiedObservabilityHarness()
        harness.record(agent_id="agent-a", tool="analyze", duration_ms=100)
        harness.record(agent_id="agent-b", tool="analyze", duration_ms=200)
        report = harness.summary()          # combined view
        stats  = harness.compare("agent-a","agent-b")  # Welch's t-test
        otel   = harness.start_tracing("agent-eval")   # OTel init
    """

    def __init__(self, service_name: str = "agent-eval"):
        self._eval = AgentEval()
        self._otel_tracer = None
        self._service_name = service_name

    # -- record -------------------------------------------------------
    def record(self, agent_id: str, tool_name: str, duration_ms: float = 0.0,
               decision: str = "allowed", error: str = "none", metadata: dict | None = None):
        from agent_eval import ToolDecision, ErrorClass
        if error == "none":
            err = ErrorClass.NONE
        else:
            err = ErrorClass(error)
        if decision == "denied":
            dec = ToolDecision.DENIED
        elif decision == "approval":
            dec = ToolDecision.APPROVAL
        else:
            dec = ToolDecision.ALLOWED
        self._eval.record_tool_call(tool_name, agent_id, duration_ms, dec, error=err, metadata=metadata)

    # -- golden path --------------------------------------------------
    def golden_path(self, agent_id: str, cases: list[dict]) -> dict:
        """Run a golden-path test suite: list of (tool, duration, decision) tuples."""
        for case in cases:
            tool = case["tool"]
            dur = case.get("duration_ms", 0.0)
            dec = case.get("decision", "allowed")
            err = case.get("error", "none")
            self.record(agent_id, tool, dur, dec, err)
        return self._eval.get_metrics(agent_id)

    # -- statistical comparison ---------------------------------------
    def compare(self, agent_a: str, agent_b: str, metric: str = "duration_ms", alpha: float = 0.05) -> dict:
        """Run Welch's t-test comparing two agents. Returns dict with verdict."""
        return self._eval.compare_agents(agent_a, agent_b, metric, alpha)

    # -- OpenTelemetry ------------------------------------------------
    def start_tracing(self) -> "OpenTelemetryTracer":
        """Initialise OpenTelemetry tracer for this harness."""
        from agent_eval import OpenTelemetryTracer
        self._otel_tracer = OpenTelemetryTracer(self._eval, service_name=self._service_name)
        return self._otel_tracer

    def shutdown_tracing(self):
        if self._otel_tracer:
            self._otel_tracer.shutdown()

    # -- report -------------------------------------------------------
    def export_summary(self, fmt: str = "json") -> str:
        """Export a dashboard-ready summary as JSON (or CSV)."""
        import json
        data = {
            "harness": self._service_name,
            "service": self._service_name,
            "total_calls": self._eval.summary()["total_calls"],
            "agents": self._eval.summary()["agents"],
            "statistics": self._eval.summary()["statistics"] if "statistics" in self._eval.summary() else {},
        }
        if fmt == "json":
            return json.dumps(data, indent=2, default=str)
        # CSV fallback
        lines = ["agent_id,total_calls,avg_latency_ms,success_rate,tool_usage\n"]
        for aid, m in self._eval.get_metrics().items():
            lines.append(f"{aid},{m['total_calls']},{m['avg_latency_ms']},{m['success_rate']},{m['tool_usage']}\n")
        return "".join(lines)

    # -- unified run --------------------------------------------------
    def run(self, cases: dict[str, list[dict]]) -> dict:
        """Run a full golden-path test suite and return the combined report.

        `cases` maps agent_id to a list of golden-path case dicts.
        """
        report = {"golden_path": {}, "statistics": {}, "otlp": []}
        for agent_id, cases_list in cases.items():
            report["golden_path"][agent_id] = self.golden_path(agent_id, cases_list)
        return report

# ------------------------------------------------------------------
# OpenTelemetry tracing support (Step 9)
# ------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import StatusCode

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


class OpenTelemetryTracer:
    """Step 9: OpenTelemetry tracer for AgentEval scoring attribution.

    Instruments AgentEval with correlated traces so eval scores can be
    attributed to individual tool calls. In production, pair with a
    collector exporter (OTLP/HTTP, Jaeger, Zipkin, etc.).
    """

    def __init__(self, agent_eval: AgentEval, service_name: str = "agent-eval"):
        if not _OTEL_AVAILABLE:
            raise RuntimeError("opentelemetry SDK not installed; pip install opentelemetry-sdk")
        self._eval = agent_eval
        self._service_name = service_name
        resource = Resource.create({"service.name": service_name, "service.version": "0.1.0"})
        self._provider = TracerProvider(resource=resource)
        # Batch exporter for production
        self._provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(self._provider)
        self._tracer = trace.get_tracer(__name__)

    def record_span_for_call(self, agent_id: str, tool_name: str) -> None:
        """Record a span for a tool call with eval score attribution."""
        with self._tracer.start_as_current_span(
            f"agent_eval.{tool_name}",
            attributes={
                "agent.id": agent_id,
                "tool.name": tool_name,
                "eval.scope": "agent-eval",
            },
        ) as span:
            # Attributes set after span creation (within context)
            span.set_attribute("eval.complete", True)
            span.set_status(StatusCode.OK)

    def shutdown(self):
        """Flush and shut down the TracerProvider."""
        self._provider.shutdown()


class ConsoleSpanExporter:
    """Minimal span exporter that prints spans to stdout for CI/demo."""

    def export(self, spans):
        for span in spans:
            attrs = {k: v for k, v in span.attributes.items()
                     if k in ("agent.id", "tool.name", "eval.scope", "eval.complete")}
            print(f"[OTEL] {span.name} | {attrs}")

    def finish(self):
        pass

    def shutdown(self):
        """No-op shutdown for test compatibility."""
        pass
