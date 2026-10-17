"""Step 4: AgentEval golden-path + adversarial + policy + regression test types."""

import json
import unittest
from agent_eval import AgentEval, ToolDecision, ErrorClass, eval_harness


class TestGoldenPath(unittest.TestCase):
    """Golden path: record a successful happy-path run and verify metrics aggregation."""

    def test_golden_path(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a", duration_ms=10.0)
        ev.record_tool_call("parse", "a", duration_ms=5.0)
        m = ev.get_metrics("a")
        self.assertEqual(m["total_calls"], 2)
        self.assertEqual(m["successful_calls"], 2)
        self.assertEqual(m["allowed_calls"], 2)
        self.assertEqual(m["denied_calls"], 0)
        self.assertEqual(m["approval_calls"], 0)
        self.assertAlmostEqual(m["avg_latency_ms"], 7.5, places=2)
        self.assertAlmostEqual(m["success_rate"], 1.0, places=4)

    def test_golden_path_tracks_tool_usage(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a", duration_ms=10.0)
        ev.record_tool_call("write", "a", duration_ms=5.0)
        m = ev.get_metrics("a")
        self.assertEqual(m["tool_usage"], {"read": 1, "write": 1})
        self.assertEqual(m["total_tokens"], 0)

    def test_golden_path_artifact(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a", duration_ms=10.0)
        call = ev.record_tool_call("write", "a", duration_ms=5.0)
        self.assertEqual(call.agent_id, "a")
        self.assertEqual(call.decision, ToolDecision.ALLOWED)
        self.assertEqual(call.error, ErrorClass.NONE)
        # input_data=None -> input_hash is empty string (sha256 of empty)
        self.assertEqual(call.input_hash, "")
        self.assertEqual(call.output_hash, "")
        self.assertIsInstance(call.timestamp, str)
        # ISO 8601 with UTC offset (+00:00)
        self.assertIn("+00:00", call.timestamp)
        self.assertTrue(call.timestamp.endswith("+00:00"))


class TestAdversarial(unittest.TestCase):
    """Adversarial: stress tests, extreme inputs, and boundary conditions."""

    def test_adversarial_many_threads(self):
        ev = AgentEval()
        threads = []
        def worker():
            for _ in range(100):
                ev.record_tool_call("read", "a", duration_ms=1.0)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(worker) for _ in range(10)]
            for f in concurrent.futures.wait(futures):
                pass
        m = ev.get_metrics("a")
        self.assertEqual(m["total_calls"], 1000)
        self.assertEqual(m["successful_calls"], 1000)
        self.assertEqual(m["allowed_calls"], 1000)

    def test_adversarial_extreme_durations(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a", duration_ms=0.0)
        ev.record_tool_call("read", "a", duration_ms=1000000.0)
        m = ev.get_metrics("a")
        self.assertAlmostEqual(m["avg_latency_ms"], 500000.0, places=1)

    def test_adversarial_non_serializable_input(self):
        ev = AgentEval()
        m = ev.record_tool_call("read", "a", input_data=lambda: None, output_data=object())
        self.assertEqual(len(m.input_hash), 16)
        self.assertEqual(len(m.output_hash), 16)

    def test_adversarial_concurrent_metrics(self):
        ev = AgentEval()
        import concurrent.futures
        def worker(agent, n=200):
            for i in range(n):
                ev.record_tool_call(f"tool-{i}", agent, duration_ms=1.0)
        agents = ["agent-1", "agent-2", "agent-3"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futures = [ex.submit(worker, a) for a in agents for _ in range(1)]
        all_metrics = ev.get_metrics()
        for aid, m in all_metrics.items():
            self.assertEqual(m["total_calls"], 200)
            self.assertEqual(m["successful_calls"], 200)
