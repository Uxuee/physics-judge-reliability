"""Offline demonstration of the scoring pipeline using mock decisions."""

from __future__ import annotations

import argparse
import json
from .dataset import load_dataset

from .metrics import (accuracy_report, agreement_report, incorrect_solution_metrics,
                      joint_reliability, joint_reliability_proportions)


def mock_judgments(items: list[dict]) -> list[dict]:
    """Create transparent fake outputs solely to exercise the metrics."""
    rows = []
    for index, item in enumerate(items):
        gold = item["expert_label"]
        # Every third item flips; every fifth non-flip is stably wrong.
        if index % 3 == 0:
            a, b = gold, "INCORRECT" if gold == "CORRECT" else "CORRECT"
        elif index % 5 == 0:
            a = b = "INCORRECT" if gold == "CORRECT" else "CORRECT"
        else:
            a = b = gold
        rows.append({"item_id": item["item_id"], "problem_id": item["problem_id"], "expert_label": gold,
                     "decision_a": a, "decision_b": b})
    return rows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Path to a physics JSONL dataset")
    args = parser.parse_args(argv)
    records = mock_judgments(load_dataset(args.dataset))
    report = {
        "result_kind": "mock",
        "warning": "Mock decisions only; these are not empirical LLM results.",
        "n_items": len(records),
        "agreement": agreement_report(records),
        "accuracy_a": accuracy_report(records, "a"),
        "accuracy_b": accuracy_report(records, "b"),
        "incorrect_a": incorrect_solution_metrics(records, "a"),
        "incorrect_b": incorrect_solution_metrics(records, "b"),
        "joint_counts": joint_reliability(records),
        "joint_proportions": joint_reliability_proportions(records),
    }
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
