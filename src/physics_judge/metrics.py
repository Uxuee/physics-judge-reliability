"""Offline scoring contracts. Undefined ratios return None (JSON null).

Rows are descriptive observations, not independent inferential samples.
See docs/study_protocol.md for denominators and problem-level clustering.
"""
from collections.abc import Mapping

BINARY_LABELS = frozenset({"CORRECT", "INCORRECT"})
COHERENCE_LABELS = frozenset({"1", "2", "3", "4", "5"})
PARSER_VERSION = "strict-label-v1"


def _labels(labels):
    values = tuple(labels)
    if not values or any(type(v) is not str or not v or v != v.strip() for v in values):
        raise ValueError("Allowed labels must be nonempty canonical strings")
    return frozenset(values)


def parse_label(value, labels=BINARY_LABELS):
    """Exact token after whitespace stripping; no substring/case coercion.

    Integer coherence values are accepted only through their canonical token.
    Booleans, floats, explanations, multiple labels and missing values are invalid.
    """
    allowed = _labels(labels)
    token = str(value) if type(value) is int else value
    token = token.strip() if type(token) is str else None
    valid = token in allowed
    return {"label": token if valid else None,
            "status": "valid" if valid else "invalid",
            "parser_version": PARSER_VERSION}


def _rows(records):
    rows = list(records)
    if any(not isinstance(r, Mapping) for r in rows):
        raise ValueError("Judgment records must be mappings")
    return rows


def _ratio(n, d):
    return n / d if d else None


def agreement_report(records, labels=BINARY_LABELS):
    allowed = _labels(labels)
    rows = _rows(records)
    valid = agree = invalid_outputs = 0
    for row in rows:
        a, b = (parse_label(row.get(f"decision_{arm}"), allowed) for arm in ("a", "b"))
        invalid_outputs += (a["status"] == "invalid") + (b["status"] == "invalid")
        if a["status"] == b["status"] == "valid":
            valid += 1
            agree += a["label"] == b["label"]
    return {"n_pairs": len(rows), "valid_pairs": valid,
            "invalid_pairs": len(rows) - valid, "agreements": agree,
            "verdict_flips": valid - agree,
            "jss": _ratio(agree, valid), "flip_rate": _ratio(valid - agree, valid),
            "coverage": _ratio(valid, len(rows)),
            "strict_agreement": _ratio(agree, len(rows)),
            "invalid_output_rate": _ratio(invalid_outputs, 2 * len(rows))}


def jss(records, labels=BINARY_LABELS):
    return agreement_report(records, labels)["jss"]


def flip_rate(records, labels=BINARY_LABELS):
    """Disagreement among valid pairs only; invalid pairs are not flips."""
    return agreement_report(records, labels)["flip_rate"]


def _arm_rows(records, arm, labels):
    if arm not in {"a", "b"}:
        raise ValueError("arm must be 'a' or 'b'")
    allowed = _labels(labels)
    rows = _rows(records)
    decisions = []
    for row in rows:
        gold = parse_label(row.get("expert_label"), allowed)
        if gold["status"] != "valid":
            raise ValueError("Correctness metrics require a valid expert_label on every row")
        decisions.append((gold["label"], parse_label(row.get(f"decision_{arm}"), allowed)["label"]))
    return decisions


def accuracy_report(records, arm, labels=BINARY_LABELS):
    decisions = _arm_rows(records, arm, labels)
    valid = sum(pred is not None for _, pred in decisions)
    correct = sum(gold == pred for gold, pred in decisions)
    return {"n": len(decisions), "valid": valid, "correct": correct,
            "coverage": _ratio(valid, len(decisions)),
            "accuracy": _ratio(correct, len(decisions)),
            "valid_accuracy": _ratio(correct, valid)}


def accuracy(records, arm, labels=BINARY_LABELS):
    """Strict arm accuracy: invalid selected-arm outputs count as failures."""
    return accuracy_report(records, arm, labels)["accuracy"]


def incorrect_solution_metrics(records, arm):
    """INCORRECT is positive. Invalid positive cases count as missed detections.

    Invalid negative cases are reported separately, never credited as true negatives.
    Precision denominator is valid positive predictions; recall denominator is all
    gold positives. F1 = 2 TP / (2 TP + FP + FN); zero denominators return None.
    """
    decisions = _arm_rows(records, arm, BINARY_LABELS)
    tp = sum(g == "INCORRECT" and p == "INCORRECT" for g, p in decisions)
    fp = sum(g == "CORRECT" and p == "INCORRECT" for g, p in decisions)
    fn = sum(g == "INCORRECT" and p != "INCORRECT" for g, p in decisions)
    tn = sum(g == "CORRECT" and p == "CORRECT" for g, p in decisions)
    invalid_negative = sum(g == "CORRECT" and p is None for g, p in decisions)
    invalid = sum(p is None for _, p in decisions)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "invalid_negative": invalid_negative, "invalid": invalid,
            "coverage": _ratio(len(decisions) - invalid, len(decisions)),
            "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn),
            "f1": _ratio(2 * tp, 2 * tp + fp + fn)}


def joint_reliability(records):
    """Binary physics counts; invalid/incomplete decisions occupy a fourth category.

    Missing/invalid gold is a data error, not a model-output failure.
    """
    rows = _rows(records)
    arms_a = _arm_rows(rows, "a", BINARY_LABELS)
    arms_b = _arm_rows(rows, "b", BINARY_LABELS)
    counts = dict.fromkeys(("stable_correct", "stable_wrong", "unstable", "invalid_incomplete"), 0)
    for (gold, a), (_, b) in zip(arms_a, arms_b):
        if a is None or b is None:
            category = "invalid_incomplete"
        elif a != b:
            category = "unstable"
        else:
            category = "stable_correct" if a == gold else "stable_wrong"
        counts[category] += 1
    return counts


def joint_reliability_proportions(records):
    counts = joint_reliability(records)
    return {key: _ratio(value, sum(counts.values())) for key, value in counts.items()}
