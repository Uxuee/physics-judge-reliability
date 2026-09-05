import json
import unittest
from pathlib import Path


class DataTests(unittest.TestCase):
    def test_pilot_ids_are_unique_and_fields_present(self):
        path = Path(__file__).parents[1] / "data" / "physics_pilot.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        required = {"item_id", "level", "domain", "question", "candidate_solution",
                    "expert_label", "error_type", "final_answer_correct", "expert_rationale"}
        self.assertGreaterEqual(len(rows), 10)
        self.assertEqual(len({row["item_id"] for row in rows}), len(rows))
        self.assertTrue(all(required <= row.keys() for row in rows))
        self.assertEqual({row["expert_label"] for row in rows}, {"CORRECT", "INCORRECT"})
