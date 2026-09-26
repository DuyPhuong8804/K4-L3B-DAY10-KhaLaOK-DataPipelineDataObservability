from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from evaluation.metrics import _token_f1
from evaluation.testset import build_test_set
from retrieval.index import SearchResult
from retrieval.qa import answer_question


def _papers(count: int = 12) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "paper_id": f"10.1000/{index:02d}",
                "title": f"Paper {index:02d}",
                "summary": f"Summary sentence {index}. Additional detail.",
                "authors_joined": f"Author {index}, Coauthor {index}",
                "categories_joined": "RAG, Evaluation",
                "published": pd.Timestamp(2026, 1, index),
            }
            for index in range(1, count + 1)
        ]
    )


def test_build_test_set_writes_ten_questions_covering_all_types(tmp_path) -> None:
    output_path = tmp_path / "test_set.json"

    result = build_test_set(_papers(), output_path)

    assert len(result) == 10
    assert [item["id"] for item in result] == [f"q{index:02d}" for index in range(1, 11)]
    assert [item["question_type"] for item in result].count("summary") == 3
    assert [item["question_type"] for item in result].count("authors") == 3
    assert [item["question_type"] for item in result].count("date") == 2
    assert [item["question_type"] for item in result].count("categories") == 2
    assert all(item["ground_truth_doc_ids"] for item in result)
    assert all("'Paper " in item["question"] for item in result)
    assert json.loads(output_path.read_text(encoding="utf-8")) == result


def test_build_test_set_formats_summary_and_date_for_qa_extractor(tmp_path) -> None:
    result = build_test_set(_papers(), tmp_path / "test_set.json")

    summary_item = next(item for item in result if item["question_type"] == "summary")
    date_item = next(item for item in result if item["question_type"] == "date")

    assert summary_item["ground_truth"].endswith(".")
    assert "Additional detail" not in summary_item["ground_truth"]
    assert date_item["ground_truth"].startswith("2026-01-")
    assert len(date_item["ground_truth"]) == 10


def test_build_test_set_rejects_missing_columns(tmp_path) -> None:
    with pytest.raises(ValueError, match="Missing required columns: categories_joined"):
        build_test_set(_papers().drop(columns=["categories_joined"]), tmp_path / "test_set.json")


def test_build_test_set_requires_ten_complete_unique_papers(tmp_path) -> None:
    papers = _papers(10)
    papers.loc[0, "summary"] = ""

    with pytest.raises(ValueError, match="At least 10 complete, unique papers are required"):
        build_test_set(papers, tmp_path / "test_set.json")


def test_token_f1_handles_exact_partial_and_empty_answers() -> None:
    assert _token_f1("alpha beta", "alpha beta") == 1.0
    assert _token_f1("alpha beta", "alpha gamma") == 0.5
    assert _token_f1("", "alpha") == 0.0


def test_qa_promotes_exact_quoted_title_before_semantic_result() -> None:
    exact_document = {
        "paper_id": "10.1000/exact",
        "title": "Exact Paper",
        "content": "Exact content",
        "metadata": {
            "authors_joined": "Alice, Bob",
            "published": "2026-01-01",
            "categories_joined": "RAG, Evaluation",
            "summary": "Exact summary.",
        },
    }
    semantic_result = SearchResult(
        paper_id="10.1000/other",
        title="Other Paper",
        score=0.9,
        content="Other content",
        metadata={
            "authors_joined": "Wrong Author",
            "published": "2025-01-01",
            "categories_joined": "Other",
            "summary": "Wrong summary.",
        },
    )

    class FakeIndex:
        def lookup(self, value: str):
            return exact_document if value == "Exact Paper" else None

        def search(self, query: str, top_k: int | None = None):
            return [semantic_result]

    result = answer_question(
        "Who authored the paper 'Exact Paper'?",
        settings=SimpleNamespace(top_k=4),
        index=FakeIndex(),
    )

    assert result.answer == "Alice, Bob"
    assert result.retrieved_doc_ids[0] == "10.1000/exact"
