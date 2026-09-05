"""Validation for provisional physics fixtures; validation is not expert review."""
import json
from pathlib import Path

ANNOTATION_STATUSES = {"provisional", "independently_reviewed", "adjudicated"}
TEXT_FIELDS = {"item_id", "problem_id", "level", "domain", "question",
               "candidate_solution", "expert_label", "expert_rationale",
               "error_type", "dataset_version", "source_notes", "annotation_status"}
BOOL_FIELDS = {"reasoning_valid", "final_answer_correct"}


def validate_dataset(records):
    rows = list(records)
    if not rows:
        raise ValueError("Dataset must contain at least one item")
    seen, problems, versions = set(), {}, set()
    for index, row in enumerate(rows, 1):
        prefix = f"Item {index}"
        if not isinstance(row, dict):
            raise ValueError(f"{prefix}: expected an object")
        for field in TEXT_FIELDS | BOOL_FIELDS:
            if field not in row:
                raise ValueError(f"{prefix}: missing {field}")
            value = row[field]
            if field in TEXT_FIELDS and (type(value) is not str or not value.strip()):
                raise ValueError(f"{prefix}: {field} must be a nonempty string")
            if field in BOOL_FIELDS and type(value) is not bool:
                raise ValueError(f"{prefix}: {field} must be boolean")
        if row["expert_label"] not in {"CORRECT", "INCORRECT"}:
            raise ValueError(f"{prefix}: invalid expert_label")
        if row["annotation_status"] not in ANNOTATION_STATUSES:
            raise ValueError(f"{prefix}: invalid annotation_status")
        if row["level"] not in {"undergraduate", "advanced"}:
            raise ValueError(f"{prefix}: invalid level")
        correct = row["reasoning_valid"] and row["final_answer_correct"]
        if (row["expert_label"] == "CORRECT") != correct:
            raise ValueError(f"{prefix}: expert_label conflicts with reasoning/answer")
        if (row["error_type"] == "none") != correct:
            raise ValueError(f"{prefix}: error_type conflicts with expert_label")
        if row["item_id"] in seen:
            raise ValueError(f"{prefix}: duplicate item_id")
        seen.add(row["item_id"])
        context = (row["question"], row["domain"], row["level"])
        if row["problem_id"] in problems and problems[row["problem_id"]] != context:
            raise ValueError(f"{prefix}: inconsistent shared problem context")
        problems[row["problem_id"]] = context
        versions.add(row["dataset_version"])
    if len(versions) != 1:
        raise ValueError("Dataset mixes versions")
    return rows


def load_dataset(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {number}") from exc
    return validate_dataset(rows)
