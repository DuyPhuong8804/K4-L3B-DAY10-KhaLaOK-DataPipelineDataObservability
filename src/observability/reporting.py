from __future__ import annotations

from typing import Any

from core.utils import write_text


def _fmt(val: Any, decimals: int = 4) -> str:
    """Format a numeric value for display in markdown tables."""
    if isinstance(val, (int, float)):
        return f"{val:.{decimals}f}"
    return str(val) if val is not None else "N/A"


def _pass_fail(flag: bool | None) -> str:
    if flag is None:
        return "N/A"
    return "PASS" if flag else "FAIL"


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate a markdown report summarizing the baseline pipeline run.

    Sections: source overview, retrieval/evaluation metrics, data quality
    (GX 1.x) results, and freshness SLA status.
    """
    lines = [
        "# Phase 1 — Baseline Pipeline Report",
        "",
        "## 1. Data Source Summary",
        "",
        f"- **Source:** {source_summary.get('source', 'Crossref REST API')}",
        f"- **Total records:** {source_summary.get('total_records', 'N/A')}",
        f"- **Query:** {source_summary.get('query', 'N/A')}",
        "",
        "## 2. Retrieval & Evaluation Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Samples | {_fmt(metrics.get('samples'), 0)} |",
        f"| Retrieval Hit Rate | {_fmt(metrics.get('retrieval_hit_rate'))} |",
        f"| Mean Token F1 | {_fmt(metrics.get('mean_token_f1'))} |",
        f"| Judge Accuracy | {_fmt(metrics.get('judge_accuracy'))} |",
        f"| Mean Judge Score | {_fmt(metrics.get('mean_judge_score'), 2)} |",
        "",
        "## 3. Data Quality (Great Expectations 1.x)",
        "",
        f"- **Overall status:** {_pass_fail(quality.get('success'))}",
        f"- **Row count:** {quality.get('row_count', 'N/A')}",
        "",
    ]

    if "results" in quality:
        lines.append("| Expectation | Column | Result |")
        lines.append("|-------------|--------|--------|")
        for r in quality["results"]:
            status = "PASS" if r.get("success") else "FAIL"
            col = r.get("column") or "N/A"
            lines.append(f"| {r.get('expectation_type', 'N/A')} | {col} | {status} |")
        lines.append("")

    lines.extend([
        "## 4. Freshness Report",
        "",
        f"- **Latest published:** {freshness.get('latest_published', 'N/A')}",
        f"- **Oldest published:** {freshness.get('oldest_published', 'N/A')}",
        f"- **Threshold:** {freshness.get('freshness_threshold_days', 180)} days",
        f"- **Stale rows:** {freshness.get('stale_rows', 'N/A')} / {freshness.get('total_rows', 'N/A')}",
        f"- **Stale ratio:** {_fmt(freshness.get('stale_ratio'))}",
        f"- **Is fresh:** {_pass_fail(freshness.get('is_fresh'))}",
        "",
        "---",
        "*Report generated automatically by the baseline pipeline.*",
        "",
    ])

    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Generate a markdown report comparing baseline / corrupted / repaired.

    This is the key deliverable demonstrating Silent Failure detection and
    Idempotent Repair effectiveness.
    """
    lines = [
        "# Corruption & Repair Report — 3-State Comparison",
        "",
        "## 1. Performance Metrics Comparison",
        "",
        "| Metric | Baseline | Corrupted | Repaired |",
        "|--------|----------|-----------|----------|",
        f"| Samples | {_fmt(baseline_metrics.get('samples'), 0)} "
        f"| {_fmt(corrupted_metrics.get('samples'), 0)} "
        f"| {_fmt(repaired_metrics.get('samples'), 0)} |",
        f"| Retrieval Hit Rate | {_fmt(baseline_metrics.get('retrieval_hit_rate'))} "
        f"| {_fmt(corrupted_metrics.get('retrieval_hit_rate'))} "
        f"| {_fmt(repaired_metrics.get('retrieval_hit_rate'))} |",
        f"| Mean Token F1 | {_fmt(baseline_metrics.get('mean_token_f1'))} "
        f"| {_fmt(corrupted_metrics.get('mean_token_f1'))} "
        f"| {_fmt(repaired_metrics.get('mean_token_f1'))} |",
        f"| Judge Accuracy | {_fmt(baseline_metrics.get('judge_accuracy'))} "
        f"| {_fmt(corrupted_metrics.get('judge_accuracy'))} "
        f"| {_fmt(repaired_metrics.get('judge_accuracy'))} |",
        f"| Mean Judge Score | {_fmt(baseline_metrics.get('mean_judge_score'), 2)} "
        f"| {_fmt(corrupted_metrics.get('mean_judge_score'), 2)} "
        f"| {_fmt(repaired_metrics.get('mean_judge_score'), 2)} |",
        "",
        "## 2. Data Quality Gate (GX 1.x)",
        "",
        "| State | Overall Pass |",
        "|-------|-------------|",
        f"| Corrupted | {_pass_fail(corrupted_quality.get('success'))} |",
        f"| Repaired | {_pass_fail(repaired_quality.get('success'))} |",
        "",
    ]

    # Corrupted expectation detail breakdown
    failed_expectations = []
    if "results" in corrupted_quality:
        lines.append("### Corrupted Data — Expectation Details")
        lines.append("")
        lines.append("| Expectation | Column | Result |")
        lines.append("|-------------|--------|--------|")
        for r in corrupted_quality["results"]:
            status = _pass_fail(r.get("success"))
            col = r.get("column") or "N/A"
            exp_type = r.get("expectation_type", "N/A")
            lines.append(f"| {exp_type} | {col} | {status} |")
            if not r.get("success"):
                failed_expectations.append(f"`{exp_type}` (column: `{col}`)")
        lines.append("")

    lines.extend([
        "## 3. Freshness SLA",
        "",
        "| Metric | Corrupted | Repaired |",
        "|--------|-----------|----------|",
        f"| Stale rows | {corrupted_freshness.get('stale_rows', 'N/A')} | {repaired_freshness.get('total_rows', 'N/A')} |",
        f"| Total rows | {corrupted_freshness.get('total_rows', 'N/A')} | {repaired_freshness.get('total_rows', 'N/A')} |",
        f"| Stale ratio | {_fmt(corrupted_freshness.get('stale_ratio'))} | {_fmt(repaired_freshness.get('stale_ratio'))} |",
        f"| Is fresh | {_pass_fail(corrupted_freshness.get('is_fresh'))} | {_pass_fail(repaired_freshness.get('is_fresh'))} |",
        "",
        "## 4. Analysis",
        "",
        "### Silent Failure Observed",
        "",
    ])

    # Dynamic Analysis Generation based on actual metrics
    base_hr = baseline_metrics.get("retrieval_hit_rate")
    corr_hr = corrupted_metrics.get("retrieval_hit_rate")
    rep_hr = repaired_metrics.get("retrieval_hit_rate")

    base_f1 = baseline_metrics.get("mean_token_f1")
    corr_f1 = corrupted_metrics.get("mean_token_f1")
    rep_f1 = repaired_metrics.get("mean_token_f1")

    # Hit Rate analysis
    if base_hr is not None and corr_hr is not None:
        diff_hr = corr_hr - base_hr
        if corr_hr < base_hr:
            lines.append(
                f"- **Retrieval Hit Rate** suy giảm từ **{_fmt(base_hr)}** xuống **{_fmt(corr_hr)}** "
                f"({diff_hr:+.4f}) khi dữ liệu bị bẩn."
            )
        else:
            lines.append(
                f"- **Retrieval Hit Rate** không suy giảm đáng kể (Baseline: **{_fmt(base_hr)}**, Corrupted: **{_fmt(corr_hr)}**)."
            )
    else:
        lines.append("- **Retrieval Hit Rate**: N/A (chưa có đủ dữ liệu để so sánh).")

    # Token F1 analysis
    if base_f1 is not None and corr_f1 is not None:
        diff_f1 = corr_f1 - base_f1
        if corr_f1 < base_f1:
            lines.append(
                f"- **Mean Token F1** suy giảm từ **{_fmt(base_f1)}** xuống **{_fmt(corr_f1)}** "
                f"({diff_f1:+.4f})."
            )
        else:
            lines.append(
                f"- **Mean Token F1** giữ mức tương đương (Baseline: **{_fmt(base_f1)}**, Corrupted: **{_fmt(corr_f1)}**)."
            )

    # Failed expectations summary
    if failed_expectations:
        failed_str = ", ".join(failed_expectations)
        lines.append(
            f"- Cổng Data Quality (GX 1.x) đã phát hiện lỗi dữ liệu bẩn và báo **FAIL** ở các kiểm định: {failed_str}."
        )
    elif corrupted_quality.get("success") is True:
        lines.append("- Cổng Data Quality (GX 1.x) vượt qua tất cả kiểm định trên tập bẩn.")
    else:
        lines.append("- Trạng thái Data Quality (GX 1.x): N/A.")

    lines.extend([
        "",
        "### Recovery via Idempotent Repair",
        "",
    ])

    # Repair analysis
    if rep_hr is not None and corr_hr is not None and base_hr is not None:
        if rep_hr >= corr_hr and abs(rep_hr - base_hr) <= 0.05:
            lines.append(
                f"- Hiệu năng Retrieval đã phục hồi về gần mức ban đầu khi Hit Rate đạt **{_fmt(rep_hr)}** "
                f"(so với Baseline **{_fmt(base_hr)}**)."
            )
        elif rep_hr > corr_hr:
            lines.append(
                f"- Hiệu năng Retrieval có sự cải thiện sau repair (Hit Rate tăng từ **{_fmt(corr_hr)}** lên **{_fmt(rep_hr)}**)."
            )
        else:
            lines.append(
                f"- Sau repair, Hit Rate đạt **{_fmt(rep_hr)}** (Baseline: **{_fmt(base_hr)}**, Corrupted: **{_fmt(corr_hr)}**)."
            )
    else:
        lines.append("- Kết quả Idempotent Repair: N/A (chưa có đủ dữ liệu kiểm thử).")

    lines.extend([
        "",
        "---",
        "*Report generated automatically by the corruption flow pipeline.*",
        "",
    ])

    write_text(report_path, "\n".join(lines))
