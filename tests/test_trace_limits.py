import unittest

from agent_eval import AgentEval


class TraceLimitTests(unittest.TestCase):
    def test_zero_negative_and_boolean_limits_rejected(self):
        ev = AgentEval()
        ev.record_tool_call("read", "agent")
        for limit in (0, -1, True, False, 1.5, "2"):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    ev.get_traces(limit=limit)

    def test_limit_is_respected(self):
        ev = AgentEval()
        for index in range(4):
            ev.record_tool_call("tool" + str(index), "agent")
        self.assertEqual([x["tool_name"] for x in ev.get_traces(limit=2)],
                         ["tool2", "tool3"])
