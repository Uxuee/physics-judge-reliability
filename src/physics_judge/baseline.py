"""Offline demonstration of the scoring pipeline using mock decisions."""

from __future__ import annotations

import json
from pathlib import Path

from .metrics import accuracy, flip_rate, joint_reliability, jss


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_pilot() -> list[dict]:
    path = project_root() / "data" / "physics_pilot.jsonl"
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


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
        rows.append({"item_id": item["item_id"], "expert_label": gold,
                     "decision_a": a, "decision_b": b})
    return rows


def main() -> None:
    records = mock_judgments(load_pilot())
    report = {
        "warning": "Mock decisions only; these are not empirical LLM results.",
        "n_items": len(records),
        "jss": jss(records),
        "flip_rate": flip_rate(records),
        "accuracy_a": accuracy(records, "a"),
        "accuracy_b": accuracy(records, "b"),
        "joint_reliability": joint_reliability(records),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
