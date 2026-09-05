import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from physics_judge.baseline import main


class BaselineTests(unittest.TestCase):
    def test_explicit_path_and_mock_marker(self):
        path = Path(__file__).resolve().parents[1] / "data" / "physics_pilot.jsonl"
        out = io.StringIO()
        with contextlib.redirect_stdout(out): main(["--dataset", str(path)])
        report = json.loads(out.getvalue())
        self.assertEqual(report["result_kind"], "mock")
        self.assertIn("not empirical", report["warning"])
        self.assertEqual(report["n_items"], 12)
        self.assertEqual(sum(report["joint_counts"].values()), 12)

    def test_path_required(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit): main([])

    def test_external_working_directory(self):
        root = Path(__file__).resolve().parents[1]
        code = "import sys; sys.path.insert(0, sys.argv[1]); from physics_judge.baseline import main; main(['--dataset', sys.argv[2]])"
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run([sys.executable, "-c", code, str(root / "src"),
                                     str(root / "data" / "physics_pilot.jsonl")],
                                    cwd=d, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["result_kind"], "mock")
