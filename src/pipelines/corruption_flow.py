from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_dataframe, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

COMPARED_METRICS = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")


def _require(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"[corruption] Missing {path}. Run `python script/run_phase1.py` first.")


def _quality_checks(df: pd.DataFrame, settings: Settings, state: str) -> tuple[dict[str, Any], dict[str, Any]]:
    quality_dir = settings.paths.quality_dir
    quality = run_data_quality_checks(df, settings, state)
    write_json(quality_dir / f"{state}_quality_report.json", quality)
    freshness = build_freshness_report(df, settings, quality_dir / f"{state}_freshness_report.json")
    print(f"[corruption] {state}: rows={len(df)} quality_gate={quality['success']} fresh={freshness['is_fresh']}")
    return quality, freshness


def _index_and_evaluate(
    df: pd.DataFrame,
    settings: Settings,
    embeddings_path: Path,
    metrics_path: Path,
    answers_path: Path,
) -> dict[str, Any]:
    index = LocalEmbeddingIndex.build(df, settings, embeddings_path)
    return evaluate_pipeline(settings, index, settings.paths.eval_testset, metrics_path, answers_path).summary


def _repair_from_raw(settings: Settings) -> pd.DataFrame:
    # Always rebuilt from the preserved raw snapshot, never patched from corrupted rows,
    # so re-running the repair yields the same dataset every time.
    records = load_raw_records(settings.paths.raw_records_json)
    return build_clean_dataframe(records, now_utc())


def _print_comparison(baseline: dict[str, Any], corrupted: dict[str, Any], repaired: dict[str, Any]) -> None:
    print(f"\n{'Metric':<20}{'Baseline':>10}{'Corrupted':>11}{'Repaired':>10}")
    for name in COMPARED_METRICS:
        values = [state.get(name) for state in (baseline, corrupted, repaired)]
        cells = "".join(f"{v:>10.4f} " if isinstance(v, (int, float)) else f"{'N/A':>10} " for v in values)
        print(f"{name:<20}{cells}")
    print()


def main() -> None:
    settings = load_settings()
    paths = settings.paths
    for required in (paths.clean_json, paths.baseline_metrics, paths.eval_testset, paths.raw_records_json):
        _require(required)

    baseline_metrics = read_json(paths.baseline_metrics)
    clean_df = pd.DataFrame(read_json(paths.clean_json))

    corrupted_df = corrupt_clean_dataframe(clean_df, paths.corruption_log)
    write_dataframe(corrupted_df, paths.corrupted_clean_csv, paths.corrupted_clean_json)
    print(f"[corruption] Injected corruption: {len(clean_df)} -> {len(corrupted_df)} rows, log -> {paths.corruption_log}")
    corrupted_quality, corrupted_freshness = _quality_checks(corrupted_df, settings, "corrupted")
    if not corrupted_quality["success"]:
        print("[corruption] Quality gate caught the corrupted batch; indexing it anyway to measure the impact.")
    corrupted_metrics = _index_and_evaluate(
        corrupted_df, settings, paths.corrupted_embeddings_json, paths.corrupted_metrics, paths.corrupted_answers
    )

    repaired_df = _repair_from_raw(settings)
    write_dataframe(repaired_df, paths.repaired_clean_csv, paths.repaired_clean_json)
    repaired_quality, repaired_freshness = _quality_checks(repaired_df, settings, "repaired")
    if not repaired_quality["success"]:
        raise SystemExit("[corruption] Repaired data still fails the quality gate; check the raw snapshot.")
    repaired_metrics = _index_and_evaluate(
        repaired_df, settings, paths.repaired_embeddings_json, paths.repaired_metrics, paths.repaired_answers
    )

    generate_corruption_report(
        paths.comparison_report,
        baseline_metrics,
        corrupted_metrics,
        repaired_metrics,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    _print_comparison(baseline_metrics, corrupted_metrics, repaired_metrics)
    print(f"[corruption] Report -> {paths.comparison_report}")
