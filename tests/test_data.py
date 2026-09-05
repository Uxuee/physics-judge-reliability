import copy
import json
from pathlib import Path
import tempfile
import unittest
from physics_judge.dataset import load_dataset, validate_dataset, TEXT_FIELDS, BOOL_FIELDS

PATH = Path(__file__).resolve().parents[1] / "data" / "physics_pilot.jsonl"


class DataTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_dataset(PATH)

    def test_pilot_schema_and_provisional_status(self):
        self.assertEqual(len(self.rows), 12)
        self.assertEqual(len({r["problem_id"] for r in self.rows}), 11)
        self.assertEqual({r["annotation_status"] for r in self.rows}, {"provisional"})
        self.assertEqual({r["dataset_version"] for r in self.rows}, {"0.2.0-dev"})
        self.assertEqual(sum(r["expert_label"] == "CORRECT" for r in self.rows), 6)

    def test_shared_kerr_problem(self):
        a, b = [r for r in self.rows if r["item_id"] in {"gr_001", "gr_002"}]
        self.assertEqual(a["problem_id"], b["problem_id"])
        self.assertEqual(a["question"], b["question"])

    def test_missing_fields(self):
        for field in TEXT_FIELDS | BOOL_FIELDS:
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                del rows[0][field]
                with self.assertRaisesRegex(ValueError, field): validate_dataset(rows)

    def test_field_types(self):
        for field in TEXT_FIELDS | BOOL_FIELDS:
            for bad in [None, 1, [], {}]:
                with self.subTest(field=field, bad=bad):
                    rows = copy.deepcopy(self.rows)
                    rows[0][field] = bad
                    with self.assertRaises(ValueError): validate_dataset(rows)
        for field in BOOL_FIELDS:
            rows = copy.deepcopy(self.rows)
            rows[0][field] = "false"
            with self.assertRaises(ValueError): validate_dataset(rows)

    def test_empty_text(self):
        for field in TEXT_FIELDS:
            rows = copy.deepcopy(self.rows)
            rows[0][field] = "  "
            with self.assertRaises(ValueError): validate_dataset(rows)

    def test_allowed_values(self):
        for field, value in [("expert_label", "YES"), ("annotation_status", "verified"), ("level", "easy")]:
            rows = copy.deepcopy(self.rows)
            rows[0][field] = value
            with self.assertRaises(ValueError): validate_dataset(rows)

    def test_duplicate_and_empty(self):
        with self.assertRaises(ValueError): validate_dataset([])
        with self.assertRaises(ValueError): validate_dataset([self.rows[0], self.rows[0]])
        with self.assertRaises(ValueError): validate_dataset([None])

    def test_all_label_truth_table_combinations(self):
        for reasoning in (True, False):
            for answer in (True, False):
                for gold in ("CORRECT", "INCORRECT"):
                    with self.subTest(reasoning=reasoning, answer=answer, gold=gold):
                        r = copy.deepcopy(self.rows[0])
                        r.update(reasoning_valid=reasoning, final_answer_correct=answer,
                                 expert_label=gold, error_type="none" if gold == "CORRECT" else "arithmetic")
                        if (gold == "CORRECT") == (reasoning and answer):
                            self.assertEqual(len(validate_dataset([r])), 1)
                        else:
                            with self.assertRaises(ValueError): validate_dataset([r])

    def test_error_type_consistency(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["error_type"] = "none"
        with self.assertRaises(ValueError): validate_dataset(rows)

    def test_context_and_version_consistency(self):
        rows = copy.deepcopy(self.rows)
        rows[8]["question"] += " Changed"
        with self.assertRaises(ValueError): validate_dataset(rows)
        rows = copy.deepcopy(self.rows)
        rows[0]["dataset_version"] = "other"
        with self.assertRaises(ValueError): validate_dataset(rows)

    def test_loader_errors(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.jsonl"
            for content in ["", "\n", "{broken}"]:
                p.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError): load_dataset(p)
            p.write_text("\n" + json.dumps(self.rows[0]) + "\n", encoding="utf-8")
            self.assertEqual(len(load_dataset(p)), 1)
