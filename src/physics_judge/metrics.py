"""Dependency-free metrics for the physics-judge study.

Each record represents one physics solution evaluated under two semantically
equivalent rubric prompts. ``decision_a`` and ``decision_b`` are normalized as
``CORRECT`` or ``INCORRECT``; ``expert_label`` is the human gold label.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

VALID_LABELS = {"CORRECT", "INCORRECT"}


def _records(records: Iterable[dict]) -> list[dict]:
    rows = list(records)
    if not rows:
        raise ValueError("At least one judgment record is required.")
    for row in rows:
        for field in ("decision_a", "decision_b", "expert_label"):
            if row.get(field) not in VALID_LABELS:
                raise ValueError(f"{field} must be CORRECT or INCORRECT")
    return rows


def jss(records: Iterable[dict]) -> float:
    """Judge Sensitivity Score: prompt-pair decision agreement."""
    rows = _records(records)
    return sum(r["decision_a"] == r["decision_b"] for r in rows) / len(rows)


def flip_rate(records: Iterable[dict]) -> float:
    """Fraction of items whose verdict changes under rubric paraphrase."""
    return 1.0 - jss(records)


def accuracy(records: Iterable[dict], arm: str) -> float:
    """Agreement with expert labels for prompt arm ``a`` or ``b``."""
    if arm not in {"a", "b"}:
        raise ValueError("arm must be 'a' or 'b'")
    rows = _records(records)
    key = f"decision_{arm}"
    return sum(r[key] == r["expert_label"] for r in rows) / len(rows)


def joint_reliability(records: Iterable[dict]) -> dict[str, int]:
    """Count stable/correct, stable/wrong, and unstable prompt pairs.

    This is the central extension beyond JSS: it prevents a consistently wrong
    judge from being described as reliable merely because its JSS is high.
    """
    rows = _records(records)
    counts: Counter[str] = Counter()
    for row in rows:
        a, b, gold = row["decision_a"], row["decision_b"], row["expert_label"]
        if a != b:
            counts["unstable"] += 1
        elif a == gold:
            counts["stable_correct"] += 1
        else:
            counts["stable_wrong"] += 1
    return {
        "stable_correct": counts["stable_correct"],
        "stable_wrong": counts["stable_wrong"],
        "unstable": counts["unstable"],
    }
