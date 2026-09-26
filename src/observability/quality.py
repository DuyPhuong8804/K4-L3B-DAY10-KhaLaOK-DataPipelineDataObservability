from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
)
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df_or_path: pd.DataFrame | Path | str, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run data quality checks using Great Expectations 1.x ephemeral context.

    Expectations:
    1. Row count between 1 and 100.
    2. paper_id not null.
    3. paper_id unique.
    4. title not null.
    5. summary length >= 10 characters.
    """
    if isinstance(df_or_path, (str, Path)):
        df = pd.read_csv(df_or_path)
    else:
        df = df_or_path

    # --- GX 1.x ephemeral context setup ---
    context = gx.get_context(mode="ephemeral")

    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")

    # --- Define Expectation Suite ---
    suite = context.suites.add(gx.ExpectationSuite(name=report_name))
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=1, max_value=100))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(ExpectColumnValueLengthsToBeBetween(column="summary", min_value=10))

    batch_request = batch_def.build_batch_request(batch_parameters={"dataframe": df})
    validation_def = context.validation_definitions.add(
        gx.ValidationDefinition(
            name=f"{report_name}_validation",
            data=batch_def,
            suite=suite,
        )
    )
    results = validation_def.run(batch_parameters={"dataframe": df})

    # --- Build result dictionary ---
    result_list = []
    for r in results.results:
        entry: dict[str, Any] = {
            "expectation_type": type(r.expectation_config).__name__,
            "success": r.success,
        }
        result_list.append(entry)

    report: dict[str, Any] = {
        "success": results.success,
        "report_name": report_name,
        "row_count": len(df),
        "results": result_list,
    }

    # Save report to quality directory
    output_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(output_path, report)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Compute freshness report based on age_days and threshold.

    A dataset is considered NOT fresh (is_fresh=False) when more than 25%
    of its papers have age_days exceeding the freshness_threshold_days (180).
    """
    threshold = settings.freshness_threshold_days  # default 180
    total = len(df)

    if total == 0:
        report: dict[str, Any] = {
            "latest_published": None,
            "oldest_published": None,
            "freshness_threshold_days": threshold,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": True,
        }
        write_json(report_path, report)
        return report

    stale_count = int((df["age_days"] > threshold).sum())
    stale_ratio = stale_count / total

    report = {
        "latest_published": str(df["published"].max()),
        "oldest_published": str(df["published"].min()),
        "freshness_threshold_days": threshold,
        "stale_rows": stale_count,
        "total_rows": total,
        "stale_ratio": round(stale_ratio, 4),
        "is_fresh": stale_ratio <= 0.25,
    }

    write_json(report_path, report)
    return report
