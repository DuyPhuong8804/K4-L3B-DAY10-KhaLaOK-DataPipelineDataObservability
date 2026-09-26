from __future__ import annotations

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

MAX_STALE_RATIO = 0.25


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Freshness SLA: the batch is stale when more than 25% of papers are older than the threshold."""
    threshold = settings.freshness_threshold_days
    total = len(df)
    stale_count = int((df["age_days"] > threshold).sum()) if total else 0
    stale_ratio = stale_count / total if total else 0.0
    return {
        "latest_published": str(df["published"].max()) if total else None,
        "oldest_published": str(df["published"].min()) if total else None,
        "freshness_threshold_days": threshold,
        "max_stale_ratio": MAX_STALE_RATIO,
        "stale_rows": stale_count,
        "total_rows": total,
        "stale_ratio": round(stale_ratio, 4),
        "is_fresh": stale_ratio <= MAX_STALE_RATIO,
    }


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run data quality checks using Great Expectations 1.x ephemeral context.

    Expectations:
    1. Row count between 1 and 100.
    2. paper_id not null.
    3. paper_id unique.
    4. title not null.
    5. title length >= 8 characters.
    6. summary not null.
    7. summary length >= 10 characters.

    The gate passes only when all expectations pass AND the freshness SLA holds.
    """
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
    suite.add_expectation(ExpectColumnValueLengthsToBeBetween(column="title", min_value=8))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="summary"))
    suite.add_expectation(ExpectColumnValueLengthsToBeBetween(column="summary", min_value=10))

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
        cfg = r.expectation_config
        entry: dict[str, Any] = {
            "expectation_type": cfg.type if hasattr(cfg, "type") else type(cfg).__name__,
            "column": cfg.kwargs.get("column") if hasattr(cfg, "kwargs") else None,
            "success": r.success,
        }
        result_list.append(entry)

    freshness = evaluate_freshness_sla(df, settings)
    report: dict[str, Any] = {
        "success": bool(results.success and freshness["is_fresh"]),
        "gx_success": results.success,
        "report_name": report_name,
        "row_count": len(df),
        "results": result_list,
        "freshness": freshness,
    }

    # Save report to quality directory
    output_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(output_path, report)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    report = evaluate_freshness_sla(df, settings)
    write_json(report_path, report)
    return report
