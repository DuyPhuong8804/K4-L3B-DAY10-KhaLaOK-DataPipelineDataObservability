from __future__ import annotations

import random
from datetime import UTC, datetime

import pandas as pd

from core.utils import write_json

# Fixed seed for reproducible corruption patterns across demo runs
_CORRUPTION_SEED = 42


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate 6 types of data corruption on a clean dataframe.

    Corruption scenarios:
    1. Drop latest 20% records.
    2. Blank summary on some rows.
    3. Inject noise characters into summary.
    4. Truncate title to < 8 characters.
    5. Set published date to a stale value (2020-01-01).
    6. Duplicate rows.

    After all corruptions, text_for_embedding is rebuilt.
    A detailed corruption log is written to output_log_path.
    """
    rng = random.Random(_CORRUPTION_SEED)
    df = df.copy().reset_index(drop=True)
    log_entries: list[dict] = []
    n = len(df)

    # ---- 1. Drop latest 20% records ----
    drop_count = max(1, int(n * 0.2))
    df_sorted = df.sort_values("published", ascending=False)
    dropped_rows = df_sorted.head(drop_count)
    drop_ids = dropped_rows.index.tolist()
    dropped_paper_ids = dropped_rows["paper_id"].tolist()
    df = df.drop(drop_ids).reset_index(drop=True)
    log_entries.append({
        "corruption_type": "drop_latest",
        "affected_rows": drop_count,
        "paper_ids": dropped_paper_ids,
        "description": f"Dropped {drop_count} latest records (top 20% by published date)",
    })
    n = len(df)

    # ---- 2. Blank summary ----
    blank_count = min(3, n)
    blank_indices = rng.sample(range(n), blank_count)
    blank_paper_ids = []
    for i in blank_indices:
        df.at[i, "summary"] = ""
        blank_paper_ids.append(df.at[i, "paper_id"])
    log_entries.append({
        "corruption_type": "blank_summary",
        "affected_rows": blank_count,
        "paper_ids": blank_paper_ids,
        "description": f"Blanked summary for {blank_count} rows",
    })

    # ---- 3. Inject noise into summary ----
    noise_count = min(3, n)
    available_for_noise = [i for i in range(n) if i not in blank_indices]
    noise_indices = rng.sample(available_for_noise, min(noise_count, len(available_for_noise)))
    noise_paper_ids = []
    for i in noise_indices:
        original = str(df.at[i, "summary"])
        mid = len(original) // 2
        df.at[i, "summary"] = original[:mid] + " @#$%^&*NOISE_CORRUPTED!!! " + original[mid:]
        noise_paper_ids.append(df.at[i, "paper_id"])
    log_entries.append({
        "corruption_type": "inject_noise",
        "affected_rows": len(noise_indices),
        "paper_ids": noise_paper_ids,
        "description": f"Injected noise characters into summary of {len(noise_indices)} rows",
    })

    # ---- 4. Truncate title to < 8 characters ----
    trunc_count = min(3, n)
    trunc_indices = rng.sample(range(n), trunc_count)
    trunc_paper_ids = []
    for i in trunc_indices:
        df.at[i, "title"] = str(df.at[i, "title"])[:7]
        trunc_paper_ids.append(df.at[i, "paper_id"])
    log_entries.append({
        "corruption_type": "truncate_title",
        "affected_rows": trunc_count,
        "paper_ids": trunc_paper_ids,
        "description": f"Truncated title to <8 chars for {trunc_count} rows",
    })

    # ---- 5. Stale date (push published far into the past) ----
    stale_count = min(5, n)
    stale_indices = rng.sample(range(n), stale_count)
    stale_date_str = "2020-01-01"
    now_date = datetime.now(UTC).date()
    stale_age = (now_date - datetime(2020, 1, 1).date()).days
    stale_paper_ids = []
    for i in stale_indices:
        df.at[i, "published"] = stale_date_str
        df.at[i, "age_days"] = stale_age
        stale_paper_ids.append(df.at[i, "paper_id"])
    log_entries.append({
        "corruption_type": "stale_date",
        "affected_rows": stale_count,
        "paper_ids": stale_paper_ids,
        "description": f"Set published date to {stale_date_str} for {stale_count} rows (age_days={stale_age})",
    })

    # ---- 6. Duplicate rows ----
    dup_count = min(3, n)
    duplicates = df.head(dup_count).copy()
    dup_paper_ids = duplicates["paper_id"].tolist()
    df = pd.concat([df, duplicates], ignore_index=True)
    log_entries.append({
        "corruption_type": "duplicate_rows",
        "affected_rows": dup_count,
        "paper_ids": dup_paper_ids,
        "description": f"Duplicated first {dup_count} rows",
    })

    # ---- Rebuild text_for_embedding ----
    df["authors_joined"] = df["authors"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    df["categories_joined"] = df["categories"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = (
        "Title: " + df["title"].astype(str) + "\n"
        + "Authors: " + df["authors_joined"].astype(str) + "\n"
        + "Categories: " + df["categories_joined"].astype(str) + "\n"
        + "Published: " + df["published"].astype(str) + "\n"
        + "Summary: " + df["summary"].astype(str)
    )

    # ---- Write corruption log ----
    write_json(output_log_path, log_entries)

    return df
