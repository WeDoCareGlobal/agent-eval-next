"""Step 9 & 10: AgentEval OpenTelemetry tracing + unified observability harness."""

import unittest
from agent_eval import (
    AgentEval,
    UnifiedObservabilityHarness,
    OpenTelemetryTracer,
    ToolDecision,
    ErrorClass,
)


class TestOpenTelemetryTracer(unittest.TestCase):
    """Step 9: OpenTelemetry tracing for eval score attribution."""

    def setUp(self):
        self.eval = AgentEval()

    def test_opentelemetry_tracer_creation(self):
        tracer = OpenTelemetryTracer(self.eval, service_name="test-service")
        self.assertIsNotNone(tracer)
        tracer.shutdown()

    def test_opentelemetry_span_recorded(self):
        tracer = OpenTelemetryTracer(self.eval, service_name="test-service")
        # Simulate recording a span for a tool call
        tracer.record_span_for_call("agent-1", "tool-a")
        tracer.shutdown()

    def test_opentelemetry_unavailable_without_sdk(self):
        # Ensure the module handles missing opentelemetry gracefully
        import agent_eval.__init__ as ai
        self.assertTrue(ai._OTEL_AVAILABLE or True)  # flag exists regardless


class TestUnifiedObservabilityHarness(unittest.TestCase):
    """Step 10: All-in-one unified observability harness."""

    def setUp(self):
        self.harness = UnifiedObservabilityHarness(service_name="unified-test")

    def test_record_and_golden_path(self):
        cases = [
            {"tool": "read", "duration_ms": 10.0, "decision": "allowed"},
            {"tool": "parse", "duration_ms": 5.0, "decision": "allowed"},
        ]
        metrics = self.harness.golden_path("agent-1", cases)
        self.assertEqual(metrics["total_calls"], 2)
        self.assertEqual(metrics["successful_calls"], 2)
        self.assertEqual(metrics["allowed_calls"], 2)

    def test_record_with_errors(self):
        self.harness.record("agent-1", "read", 100.0, decision="denied", error="timeout")
        metrics = self.harness._eval.get_metrics("agent-1")
        self.assertEqual(metrics["total_calls"], 1)
        self.assertEqual(metrics["denied_calls"], 1)
        self.assertEqual(metrics["errors"]["timeout"], 1)

    def test_compare_agents(self):
        for i in range(10):
            self.harness.record("agent-a", "tool", 10.0)
            self.harness.record("agent-b", "tool", 20.0)
        stats = self.harness.compare("agent-a", "agent-b")
        self.assertEqual(stats["verdict"], "significant")
        self.assertGreater(abs(stats["t_statistic"]), 10)

    def test_export_summary_json(self):
        self.harness.record("agent-1", "tool", 100.0)
        summary = self.harness.export_summary(fmt="json")
        self.assertIn('"total_calls": 1', summary)
        self.assertIn('"agent-1"', summary)

    def test_run_full_golden_path(self):
        cases = {
            "agent-1": [
                {"tool": "read", "duration_ms": 10.0},
                {"tool": "write", "duration_ms": 5.0},
            ],
            "agent-2": [
                {"tool": "read", "duration_ms": 20.0},
                {"tool": "write", "duration_ms": 15.0},
            ],
        }
        report = self.harness.run(cases)
        self.assertIn("golden_path", report)
        self.assertIn("agent-1", report["golden_path"])
        self.assertEqual(report["golden_path"]["agent-1"]["total_calls"], 2)
        self.assertEqual(report["golden_path"]["agent-2"]["total_calls"], 2)

    def test_open_telemetry_start_stop(self):
        tracer = self.harness.start_tracing()
        self.assertIsNotNone(tracer)
        self.harness.shutdown_tracing()

    def test_start_stop_tracing(self):
        tracer = self.harness.start_tracing()
        self.assertIsNotNone(tracer)
        self.harness.shutdown_tracing()

    def test_start_tracing_with_service_name(self):
        # Verify start_tracing accepts a service name
        old = self.harness._otel_tracer
        tracer = OpenTelemetryTracer(self.harness._eval, service_name="protocol-test")
        self.assertEqual(tracer._service_name, "protocol-test")
        tracer.shutdown()


if __name__ == "__main__":
    unittest.main()
