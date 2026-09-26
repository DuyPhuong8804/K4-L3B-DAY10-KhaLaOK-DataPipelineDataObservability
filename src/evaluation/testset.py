from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from core.utils import first_sentence, normalize_whitespace, write_json


REQUIRED_COLUMNS = {
    "paper_id",
    "title",
    "summary",
    "authors_joined",
    "categories_joined",
    "published",
}

QUESTION_TYPES = (
    "summary",
    "authors",
    "date",
    "categories",
    "summary",
    "authors",
    "date",
    "categories",
    "summary",
    "authors",
)


def _string_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    return normalize_whitespace(str(value))


def _date_value(value: Any) -> str:
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return _string_value(value)


def _select_representative_rows(df: pd.DataFrame, count: int) -> pd.DataFrame:
    """Select deterministic rows spread across the corpus, not only its head."""
    ordered = df.sort_values("paper_id", kind="stable").reset_index(drop=True)
    last_index = len(ordered) - 1
    positions = [(index * last_index) // (count - 1) for index in range(count)]
    return ordered.iloc[positions].reset_index(drop=True)


def _build_question(question_type: str, row: pd.Series) -> tuple[str, str]:
    title = _string_value(row["title"])
    if question_type == "summary":
        return f"Summarize the paper '{title}'.", first_sentence(_string_value(row["summary"]))
    if question_type == "authors":
        return f"Who authored the paper '{title}'?", _string_value(row["authors_joined"])
    if question_type == "date":
        return f"When was the paper '{title}' published?", _date_value(row["published"])
    if question_type == "categories":
        return f"What categories are assigned to the paper '{title}'?", _string_value(
            row["categories_joined"]
        )
    raise ValueError(f"Unsupported question type: {question_type}")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build and persist a deterministic 10-question benchmark.

    The quoted paper title lets the QA layer perform an exact lookup before
    semantic retrieval. The same benchmark can therefore be reused to compare
    baseline, corrupted, and repaired indexes fairly.
    """
    missing_columns = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    candidates = df.drop_duplicates(subset=["paper_id"], keep="first").copy()
    for column in REQUIRED_COLUMNS:
        candidates = candidates[candidates[column].map(lambda value: bool(_string_value(value)))]

    question_count = len(QUESTION_TYPES)
    if len(candidates) < question_count:
        raise ValueError(
            f"At least {question_count} complete, unique papers are required; "
            f"found {len(candidates)}."
        )

    selected = _select_representative_rows(candidates, question_count)
    test_set: list[dict[str, Any]] = []
    for number, (question_type, (_, row)) in enumerate(
        zip(QUESTION_TYPES, selected.iterrows(), strict=True),
        start=1,
    ):
        question, ground_truth = _build_question(question_type, row)
        test_set.append(
            {
                "id": f"q{number:02d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [_string_value(row["paper_id"])],
            }
        )

    write_json(output_path, test_set)
    return test_set
