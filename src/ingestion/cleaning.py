from __future__ import annotations

import re
from dataclasses import asdict
from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def _strip_jats(text: str) -> str:
    """Remove JATS XML tags and normalize whitespace."""
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a dataframe ready for embedding.

    Steps:
    1. Normalize title, summary (strip JATS XML tags, whitespace).
    2. Parse published date, compute age_days.
    3. Create helper columns: authors_joined, categories_joined,
       summary_chars, text_for_embedding.
    4. Drop duplicates by paper_id, filter out bad rows.
    5. Sort by published descending and return.
    """
    # Convert PaperRecord list to DataFrame
    rows = [asdict(r) for r in records]
    df = pd.DataFrame(rows)

    # Normalize text fields — strip JATS XML tags and extra whitespace
    df["title"] = df["title"].apply(lambda x: _strip_jats(str(x)) if pd.notna(x) else "")
    df["summary"] = df["summary"].apply(lambda x: _strip_jats(str(x)) if pd.notna(x) else "")

    # Ensure published is a string in YYYY-MM-DD format
    df["published"] = df["published"].astype(str)

    # Calculate age_days = (run_date - published).days
    run_date_date = run_date.date() if hasattr(run_date, "date") else run_date
    df["age_days"] = df["published"].apply(
        lambda d: (run_date_date - datetime.strptime(d[:10], "%Y-%m-%d").date()).days
        if d and d != "nan" and len(d) >= 10
        else 0
    )

    # Create helper columns
    df["authors_joined"] = df["authors"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    df["categories_joined"] = df["categories"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    df["summary_chars"] = df["summary"].str.len()

    # Build text_for_embedding (5-part structure)
    df["text_for_embedding"] = (
        "Title: " + df["title"] + "\n"
        + "Authors: " + df["authors_joined"] + "\n"
        + "Categories: " + df["categories_joined"] + "\n"
        + "Published: " + df["published"] + "\n"
        + "Summary: " + df["summary"]
    )

    # Drop duplicates by paper_id, keep first occurrence
    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    # Filter out rows with empty title or empty summary
    df = df[df["title"].str.strip().astype(bool) & df["summary"].str.strip().astype(bool)]

    # Sort by published date descending (newest first)
    df = df.sort_values("published", ascending=False).reset_index(drop=True)

    return df
