# Phase 1 — Baseline Pipeline Report

## 1. Data Source Summary

- **Source:** Crossref REST API
- **Total records:** 24
- **Query:** agentic retrieval augmented generation large language model

## 2. Retrieval & Evaluation Metrics

| Metric | Value |
|--------|-------|
| Samples | 10 |
| Retrieval Hit Rate | 1.0000 |
| Mean Token F1 | 1.0000 |
| Judge Accuracy | 1.0000 |
| Mean Judge Score | 5.00 |

## 3. Data Quality (Great Expectations 1.x)

- **Overall status:** PASS
- **Row count:** 24

| Expectation | Column | Result |
|-------------|--------|--------|
| expect_table_row_count_to_be_between | N/A | PASS |
| expect_column_values_to_not_be_null | paper_id | PASS |
| expect_column_values_to_be_unique | paper_id | PASS |
| expect_column_values_to_not_be_null | title | PASS |
| expect_column_value_lengths_to_be_between | title | PASS |
| expect_column_values_to_not_be_null | summary | PASS |
| expect_column_value_lengths_to_be_between | summary | PASS |

## 4. Freshness Report

- **Latest published:** 2026-07-22
- **Oldest published:** 2026-03-28
- **Threshold:** 180 days
- **Stale rows:** 1 / 24
- **Stale ratio:** 0.0417
- **Is fresh:** PASS

---
*Report generated automatically by the baseline pipeline.*
