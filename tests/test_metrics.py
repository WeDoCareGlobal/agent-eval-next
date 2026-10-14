import json
import unittest
from agent_eval import AgentEval, ToolDecision, ErrorClass

class EvaluationTests(unittest.TestCase):
    def test_error_is_not_success(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a", error=ErrorClass.TIMEOUT)
        self.assertEqual(ev.get_metrics("a")["success_rate"], 0)
        self.assertEqual(ev.summary()["overall_success_rate"], 0)
        self.assertEqual(ev.get_metrics("a")["allowed_calls"], 1)

    def test_mixed_metrics(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a")
        ev.record_tool_call("read", "a", error=ErrorClass.UNKNOWN)
        ev.record_tool_call("read", "a", decision=ToolDecision.DENIED)
        self.assertEqual(ev.summary()["overall_success_rate"], round(1 / 3, 4))

    def test_trace_is_json_serializable(self):
        ev = AgentEval()
        ev.record_tool_call("read", "a", decision=ToolDecision.APPROVAL)
        self.assertEqual(json.loads(json.dumps(ev.get_traces()))[0]["decision"], "approval")

    def test_non_json_input_does_not_crash(self):
        ev = AgentEval()
        self.assertEqual(len(ev.record_tool_call("read", "a", input_data={1, 2}).input_hash), 16)

    def test_empty_summary(self):
        self.assertEqual(AgentEval().summary()["overall_success_rate"], 0)
