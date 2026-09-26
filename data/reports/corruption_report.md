# Corruption & Repair Report — 3-State Comparison

## 1. Performance Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| Samples | 10 | 10 | 10 |
| Retrieval Hit Rate | 1.0000 | 0.7000 | 1.0000 |
| Mean Token F1 | 1.0000 | 0.8223 | 1.0000 |
| Judge Accuracy | 1.0000 | 0.8000 | 1.0000 |
| Mean Judge Score | 5.00 | 4.20 | 5.00 |

## 2. Data Quality Gate (GX 1.x)

| State | Overall Pass |
|-------|-------------|
| Corrupted | FAIL |
| Repaired | PASS |

### Corrupted Data — Expectation Details

| Expectation | Column | Result |
|-------------|--------|--------|
| expect_table_row_count_to_be_between | N/A | PASS |
| expect_column_values_to_not_be_null | paper_id | PASS |
| expect_column_values_to_be_unique | paper_id | FAIL |
| expect_column_values_to_not_be_null | title | PASS |
| expect_column_value_lengths_to_be_between | title | FAIL |
| expect_column_values_to_not_be_null | summary | PASS |
| expect_column_value_lengths_to_be_between | summary | FAIL |

## 3. Freshness SLA

| Metric | Corrupted | Repaired |
|--------|-----------|----------|
| Stale rows | 8 | 1 |
| Total rows | 27 | 24 |
| Stale ratio | 0.2963 | 0.0417 |
| Is fresh | FAIL | PASS |

## 4. Analysis

### Silent Failure Observed

- **Retrieval Hit Rate** suy giảm từ **1.0000** xuống **0.7000** (-0.3000) khi dữ liệu bị bẩn.
- **Mean Token F1** suy giảm từ **1.0000** xuống **0.8223** (-0.1777).
- Cổng Data Quality (GX 1.x) đã phát hiện lỗi dữ liệu bẩn và báo **FAIL** ở các kiểm định: `expect_column_values_to_be_unique` (column: `paper_id`), `expect_column_value_lengths_to_be_between` (column: `title`), `expect_column_value_lengths_to_be_between` (column: `summary`).

### Recovery via Idempotent Repair

- Hiệu năng Retrieval đã phục hồi về gần mức ban đầu khi Hit Rate đạt **1.0000** (so với Baseline **1.0000**).

---
*Report generated automatically by the corruption flow pipeline.*
