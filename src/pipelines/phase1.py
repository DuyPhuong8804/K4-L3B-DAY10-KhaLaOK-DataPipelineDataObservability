from __future__ import annotations

from typing import Any

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_dataframe, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

DEMO_QUESTION_COUNT = 2


def _run_agent_demo(settings: Settings, index: LocalEmbeddingIndex, test_set: list[dict[str, Any]]) -> None:
    try:
        require_llm_credentials(settings)
    except RuntimeError as exc:
        print(f"[phase1] Agent demo skipped: {exc}")
        return

    from retrieval.agent import build_agent, run_agent_question

    try:
        agent = build_agent(settings, index)
        demo = [
            {"question": item["question"], "answer": run_agent_question(agent, item["question"])}
            for item in test_set[:DEMO_QUESTION_COUNT]
        ]
    except Exception as exc:  # external LLM call; the demo must not fail the baseline run
        print(f"[phase1] Agent demo skipped: {settings.llm_provider} call failed ({exc}).")
        return
    write_json(settings.paths.demo_answers, demo)
    print(f"[phase1] Agent demo answers -> {settings.paths.demo_answers}")


def main() -> None:
    settings = load_settings()
    paths = settings.paths
    run_date = now_utc()

    records = fetch_source_records(settings)
    print(f"[phase1] Raw records: {len(records)}")

    clean_df = build_clean_dataframe(records, run_date)
    write_dataframe(clean_df, paths.clean_csv, paths.clean_json)
    print(f"[phase1] Clean rows: {len(clean_df)} -> {paths.clean_json.name}")

    quality = run_data_quality_checks(clean_df, settings, "baseline")
    write_json(paths.baseline_quality_report, quality)
    freshness = build_freshness_report(clean_df, settings, paths.freshness_report)
    print(f"[phase1] Quality gate success={quality['success']} | fresh={freshness['is_fresh']}")
    if not quality["success"]:
        raise SystemExit(
            f"[phase1] Baseline data failed the quality gate; not indexing it. See {paths.baseline_quality_report}"
        )
    if not freshness["is_fresh"]:
        print("[phase1] WARNING: freshness SLA breached on baseline data.")

    index = LocalEmbeddingIndex.build(clean_df, settings, paths.embeddings_json)
    print(f"[phase1] Indexed {len(index.documents)} docs into collection '{index.collection_name}'")

    if settings.refresh_test_set or not paths.eval_testset.exists():
        build_test_set(clean_df, paths.eval_testset)
    test_set = read_json(paths.eval_testset)
    print(f"[phase1] Test set: {len(test_set)} questions")

    bundle = evaluate_pipeline(settings, index, paths.eval_testset, paths.baseline_metrics, paths.baseline_answers)
    metrics = bundle.summary
    print(
        f"[phase1] Baseline retrieval_hit_rate={metrics['retrieval_hit_rate']:.4f} "
        f"mean_token_f1={metrics['mean_token_f1']:.4f}"
    )

    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "raw_records": len(records),
        "total_records": len(clean_df),
        "run_date": run_date.isoformat(),
    }
    generate_phase1_report(paths.baseline_report, source_summary, metrics, quality, freshness)
    print(f"[phase1] Report -> {paths.baseline_report}")

    _run_agent_demo(settings, index, test_set)
