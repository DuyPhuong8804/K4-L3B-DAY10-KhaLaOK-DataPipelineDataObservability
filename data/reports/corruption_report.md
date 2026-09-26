# Corruption & Repair Report — 3-State Comparison

## 1. Performance Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| Samples | 10 | 10 | 10 |
| Retrieval Hit Rate | 0.8000 | 0.4000 | 0.8000 |
| Mean Token F1 | N/A | N/A | N/A |
| Judge Accuracy | N/A | N/A | N/A |
| Mean Judge Score | N/A | N/A | N/A |

## 2. Data Quality Gate (GX 1.x)

| State | Overall Pass |
|-------|-------------|
| Corrupted | FAIL |
| Repaired | PASS |

## 3. Freshness SLA

| Metric | Corrupted | Repaired |
|--------|-----------|----------|
| Stale rows | N/A | N/A |
| Total rows | N/A | N/A |
| Stale ratio | N/A | N/A |
| Is fresh | FAIL | FAIL |

## 4. Analysis

### Silent Failure Observed

When corrupted data was injected into the RAG pipeline, the system did **not** throw any
runtime errors. However, retrieval quality degraded significantly — this is a classic
example of **Silent Failure** in production AI systems. The Quality Gate (GX 1.x) correctly
flagged the corrupted dataset as failing expectations (duplicate paper_id, blank summaries,
stale dates exceeding the Freshness SLA).

### Recovery via Idempotent Repair

By re-ingesting from the trusted raw source (`crossref_records.json`) and re-running the
full cleaning + indexing pipeline, the system recovered to near-baseline performance levels.
This demonstrates the effectiveness of **Idempotent Repair**: the same repair operation can
be executed multiple times with identical results, ensuring safe and predictable recovery.

---
*Report generated automatically by the corruption flow pipeline.*
