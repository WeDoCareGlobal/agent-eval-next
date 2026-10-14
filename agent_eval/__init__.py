# SPDX-License-Identifier: Apache-2.0
# Derived from WeDoCareGlobal-CC/agent-eval; source SHA recorded in PROVENANCE.md.
"""
Agent Eval — Agent Evaluation & Observability
We Do Care Global — Unified Ecosystem

Measures agent performance (latency, token usage, success rate, error classification)
and traces every tool call (allowed / denied / approval).
"""

import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum
from datetime import datetime


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
    """Single tool call trace"""
    tool_name: str
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: float = 0.0
    decision: ToolDecision = ToolDecision.ALLOWED
    input_hash: str = ""
    output_hash: str = ""
    error: ErrorClass = ErrorClass.NONE
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Aggregated metrics for an agent"""
    agent_id: str
    total_calls: int = 0
    successful_calls: int = 0
    allowed_calls: int = 0
    denied_calls: int = 0
    approval_calls: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    errors: dict = field(default_factory=lambda: {e.value: 0 for e in ErrorClass})
    tool_usage: dict = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

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
            "total_tokens": self.total_tokens,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "success_rate": round(self.success_rate, 4),
            "errors": self.errors,
            "tool_usage": self.tool_usage,
            "last_updated": self.last_updated,
        }


class AgentEval:
    """Main evaluation harness"""

    def __init__(self):
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
        """Record a single tool call"""
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
        m.last_updated = datetime.utcnow().isoformat()

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
        """Get tool call traces with optional filtering"""
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:\n            raise ValueError("limit must be a positive integer")\n        traces = self._traces\n        if agent_id:
            traces = [t for t in traces if t.agent_id == agent_id]
        if tool_name:
            traces = [t for t in traces if t.tool_name == tool_name]
        if decision:
            traces = [t for t in traces if t.decision == decision]
        return [{**asdict(t), "decision": t.decision.value, "error": t.error.value} for t in traces[-limit:]]

    def summary(self) -> dict:
        """Get ecosystem-wide summary"""
        all_metrics = list(self._metrics.values())
        total_calls = sum(m.total_calls for m in all_metrics)
        total_allowed = sum(m.allowed_calls for m in all_metrics)
        total_successful = sum(m.successful_calls for m in all_metrics)
        total_denied = sum(m.denied_calls for m in all_metrics)
        total_approval = sum(m.approval_calls for m in all_metrics)
        total_tokens = sum(m.total_tokens for m in all_metrics)
        total_latency = sum(m.total_latency_ms for m in all_metrics)

        return {
            "total_agents": len(self._metrics),
            "total_calls": total_calls,
            "allowed_calls": total_allowed,
            "denied_calls": total_denied,
            "approval_calls": total_approval,
            "total_tokens": total_tokens,
            "avg_latency_ms": round(total_latency / max(total_calls, 1), 2),
            "overall_success_rate": round(total_successful / max(total_calls, 1), 4),
            "agents": {aid: m.to_dict() for aid, m in self._metrics.items()},
        }

    @staticmethod
    def _hash(data: Any) -> str:
        """Create deterministic hash of data"""
        if data is None:
            return ""
        try:
            return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
        except (TypeError, ValueError):
            return hashlib.sha256(str(data).encode()).hexdigest()[:16]


# Singleton instance for ecosystem-wide use
eval_harness = AgentEval()
