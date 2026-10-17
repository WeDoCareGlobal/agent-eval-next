"""Step 8: AgentEval statistical comparison with Welch's t-test (alpha 0.05)."""

import unittest
from agent_eval import AgentEval
from agent_eval.statistics import (
    mean,
    variance,
    welch_ttest,
    StatisticalError,
)


class TestStatistics(unittest.TestCase):
    def test_mean(self):
        self.assertAlmostEqual(mean([1, 2, 3, 4, 5]), 3.0)
        with self.assertRaises(StatisticalError):
            mean([])

    def test_variance(self):
        # Sample variance of [2,4,4,4,5,5,7,9] with ddof=1: mean=5, sum_sq_dev=32, var=32/7≈4.571
        self.assertAlmostEqual(variance([2, 4, 4, 4, 5, 5, 7, 9]), 32 / 7, places=5)
        with self.assertRaises(StatisticalError):
            variance([1])

    def test_welch_ttest_basic(self):
        # Two groups with clearly different means
        g1 = [100, 102, 98, 101, 99]  # mean=100
        g2 = [160, 163, 158, 161, 159]  # mean=160
        res = welch_ttest(g1, g2, alpha=0.05)
        # |t| is large, p is very small
        self.assertGreater(abs(res["t_statistic"]), 10)
        self.assertLess(res["p_value"], 0.05)
        self.assertTrue(res["significant"])

    def test_welch_ttest_identical_means(self):
        g1 = [10, 12, 11, 13, 10]
        g2 = [10, 12, 11, 13, 10]
        res = welch_ttest(g1, g2, alpha=0.05)
        self.assertGreater(res["p_value"], 0.05)
        self.assertFalse(res["significant"])

    def test_welch_ttest_small_variance(self):
        g1 = [10, 10, 10, 10, 10]
        g2 = [12, 12, 12, 12, 12]
        res = welch_ttest(g1, g2, alpha=0.05)
        self.assertTrue(res["significant"])

    def test_welch_ttest_small_sample(self):
        g1 = [10, 12]
        g2 = [11, 13]
        res = welch_ttest(g1, g2, alpha=0.05)
        self.assertGreater(res["n1"], 0)
        self.assertGreater(res["n2"], 0)

    def test_welch_ttest_equal_means(self):
        g1 = [1, 2, 3, 4, 5]
        g2 = [2, 3, 4, 5, 6]
        res = welch_ttest(g1, g2, alpha=0.05)
        # Should not be significant at 0.05 (mostly)
        self.assertGreater(res["p_value"], 0.05)

    def test_welch_ttest_single_element_raises(self):
        with self.assertRaises(StatisticalError):
            welch_ttest([1], [2, 3])
        with self.assertRaises(StatisticalError):
            welch_ttest([], [2, 3])


class TestAgentEvalCompareAgents(unittest.TestCase):
    def setUp(self):
        self.ev = AgentEval()

    def test_compare_agents_significant(self):
        # Agent A: fast calls
        for i in range(10):
            self.ev.record_tool_call("tool", "agent-a", duration_ms=10.0 + i * 0.1)
        # Agent B: slow calls
        for i in range(10):
            self.ev.record_tool_call("tool", "agent-b", duration_ms=20.0 + i * 0.1)

        res = self.ev.compare_agents("agent-a", "agent-b")
        self.assertEqual(res["agent_a"], "agent-a")
        self.assertEqual(res["agent_b"], "agent-b")
        self.assertEqual(res["metric"], "duration_ms")
        self.assertEqual(res["verdict"], "significant")
        self.assertGreater(abs(res["t_statistic"]), 0)

    def test_compare_agents_not_significant(self):
        for i in range(10):
            self.ev.record_tool_call("tool", "agent-a", duration_ms=50.0)
            self.ev.record_tool_call("tool", "agent-b", duration_ms=50.0)

        res = self.ev.compare_agents("agent-a", "agent-b")
        self.assertEqual(res["verdict"], "not_significant")
        self.assertFalse(res["significant"])

    def test_compare_agents_missing_agent_raises(self):
        self.ev.record_tool_call("tool", "agent-a", duration_ms=10.0)
        with self.assertRaises(ValueError):
            self.ev.compare_agents("agent-a", "nonexistent")

    def test_compare_agents_unsupported_metric_raises(self):
        self.ev.record_tool_call("tool", "agent-a", duration_ms=10.0)
        with self.assertRaises(ValueError):
            self.ev.compare_agents("agent-a", "agent-b", metric="invalid_metric")

    def test_show_statistics_mean_function(self):
        from agent_eval.statistics import mean
        self.assertAlmostEqual(mean([1, 2, 3, 4, 5]), 3.0)


if __name__ == "__main__":
    unittest.main()
