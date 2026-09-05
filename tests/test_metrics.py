import unittest
from physics_judge.metrics import (
    accuracy, accuracy_report, agreement_report, flip_rate, jss, parse_label,
    incorrect_solution_metrics, joint_reliability, joint_reliability_proportions,
    COHERENCE_LABELS)


def row(a="CORRECT", b="CORRECT", gold="CORRECT"):
    return {"decision_a": a, "decision_b": b, "expert_label": gold}


class MetricTests(unittest.TestCase):
    def test_perfectly_stable_and_correct(self):
        rows = [row()]
        self.assertEqual(jss(rows), 1)
        self.assertEqual(accuracy(rows, "a"), 1)
        self.assertEqual(joint_reliability(rows), dict(stable_correct=1,
            stable_wrong=0, unstable=0, invalid_incomplete=0))

    def test_stable_does_not_mean_correct(self):
        rows = [row(gold="INCORRECT")]
        self.assertEqual(jss(rows), 1)
        self.assertEqual(accuracy(rows, "a"), 0)
        self.assertEqual(joint_reliability(rows)["stable_wrong"], 1)

    def test_flip_rate(self):
        rows = [row(b="INCORRECT"), row("INCORRECT", "INCORRECT", "INCORRECT")]
        self.assertEqual(jss(rows), .5)
        self.assertEqual(flip_rate(rows), .5)

    def test_missing_gold_for_agreement(self):
        self.assertEqual(jss([{"decision_a": "CORRECT", "decision_b": "CORRECT"}]), 1)
        with self.assertRaises(ValueError):
            accuracy([{"decision_a": "CORRECT"}], "a")
        with self.assertRaises(ValueError):
            joint_reliability([{"decision_a": "CORRECT"}])

    def test_task_specific_binary(self):
        self.assertEqual(jss([row("YES", "YES")], {"YES", "NO"}), 1)
        self.assertIsNone(jss([row("YES", "YES")]))

    def test_coherence(self):
        rows = [row(4, "4", "4"), row("3", "2", "3")]
        self.assertEqual(jss(rows, COHERENCE_LABELS), .5)
        self.assertEqual(accuracy(rows, "a", COHERENCE_LABELS), 1)

    def test_parser_is_strict(self):
        for value in [None, True, False, 4.0, [], {}, "CORRECT because", "INCORRECT CORRECT", "correct", "1-5", ""]:
            with self.subTest(value=value):
                self.assertEqual(parse_label(value)["status"], "invalid")
                self.assertIsNone(parse_label(value)["label"])
        self.assertEqual(parse_label(" CORRECT\n")["label"], "CORRECT")
        self.assertEqual(parse_label(4, COHERENCE_LABELS)["label"], "4")
        self.assertEqual(parse_label(4.0, COHERENCE_LABELS)["status"], "invalid")

    def test_invalid_is_not_a_flip(self):
        report = agreement_report([row(), row(b="INCORRECT"), row(None, None), {}])
        self.assertEqual(report["jss"], .5)
        self.assertEqual(report["coverage"], .5)
        self.assertEqual(report["strict_agreement"], .25)
        self.assertEqual(report["verdict_flips"], 1)
        self.assertEqual(report["invalid_output_rate"], .5)

    def test_all_invalid(self):
        report = agreement_report([{}])
        self.assertIsNone(report["jss"])
        self.assertIsNone(report["flip_rate"])
        self.assertEqual(report["coverage"], 0)
        self.assertEqual(report["strict_agreement"], 0)

    def test_independent_arm_accuracy(self):
        self.assertEqual(accuracy([row(b="garbage")], "a"), 1)
        self.assertEqual(accuracy([row(a=None)], "b"), 1)
        report = accuracy_report([row(), row(a=None)], "a")
        self.assertEqual(report["accuracy"], .5)
        self.assertEqual(report["valid_accuracy"], 1)
        self.assertEqual(report["coverage"], .5)

    def test_joint_categories(self):
        rows = [row(), row(gold="INCORRECT"), row(b="INCORRECT"), row(b=None)]
        self.assertEqual(set(joint_reliability(rows).values()), {1})
        self.assertEqual(set(joint_reliability_proportions(rows).values()), {.25})

    def test_detection_with_abstentions(self):
        rows = [row("INCORRECT", gold="INCORRECT"), row("INCORRECT"),
                row("CORRECT", gold="INCORRECT"), row(None, gold="INCORRECT"), row(None), row()]
        r = incorrect_solution_metrics(rows, "a")
        self.assertEqual((r["tp"], r["fp"], r["fn"], r["tn"], r["invalid_negative"]), (1, 1, 2, 1, 1))
        self.assertEqual(r["precision"], .5)
        self.assertAlmostEqual(r["recall"], 1/3)
        self.assertEqual(r["f1"], .4)

    def test_no_predictions_with_positives(self):
        r = incorrect_solution_metrics([row(gold="INCORRECT")], "a")
        self.assertIsNone(r["precision"])
        self.assertEqual(r["recall"], 0)
        self.assertEqual(r["f1"], 0)

    def test_no_positives(self):
        r = incorrect_solution_metrics([row()], "a")
        for k in ("precision", "recall", "f1"):
            self.assertIsNone(r[k])
        r = incorrect_solution_metrics([row("INCORRECT")], "a")
        self.assertEqual(r["precision"], 0)
        self.assertIsNone(r["recall"])
        self.assertEqual(r["f1"], 0)

    def test_empty_metrics(self):
        self.assertIsNone(jss([]))
        self.assertIsNone(flip_rate([]))
        self.assertIsNone(accuracy([], "a"))
        self.assertIsNone(incorrect_solution_metrics([], "a")["f1"])
        self.assertEqual(sum(joint_reliability([]).values()), 0)
        self.assertTrue(all(v is None for v in joint_reliability_proportions([]).values()))

    def test_bad_configuration(self):
        with self.assertRaises(ValueError): accuracy([], "c")
        with self.assertRaises(ValueError): jss([], [])
        with self.assertRaises(ValueError): jss([None])

    def test_generator_input(self):
        self.assertEqual(jss(row() for _ in range(2)), 1)
