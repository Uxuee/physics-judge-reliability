import unittest

from physics_judge.metrics import accuracy, flip_rate, joint_reliability, jss


class MetricTests(unittest.TestCase):
    def test_perfectly_stable_and_correct(self):
        rows = [{"decision_a": "CORRECT", "decision_b": "CORRECT", "expert_label": "CORRECT"}]
        self.assertEqual(jss(rows), 1.0)
        self.assertEqual(accuracy(rows, "a"), 1.0)
        self.assertEqual(joint_reliability(rows), {"stable_correct": 1, "stable_wrong": 0, "unstable": 0})

    def test_stable_does_not_mean_correct(self):
        rows = [{"decision_a": "CORRECT", "decision_b": "CORRECT", "expert_label": "INCORRECT"}]
        self.assertEqual(jss(rows), 1.0)
        self.assertEqual(accuracy(rows, "a"), 0.0)
        self.assertEqual(joint_reliability(rows)["stable_wrong"], 1)

    def test_flip_rate(self):
        rows = [
            {"decision_a": "CORRECT", "decision_b": "INCORRECT", "expert_label": "CORRECT"},
            {"decision_a": "INCORRECT", "decision_b": "INCORRECT", "expert_label": "INCORRECT"},
        ]
        self.assertEqual(jss(rows), 0.5)
        self.assertEqual(flip_rate(rows), 0.5)

    def test_rejects_unknown_labels(self):
        rows = [{"decision_a": "YES", "decision_b": "CORRECT", "expert_label": "CORRECT"}]
        with self.assertRaises(ValueError):
            jss(rows)
