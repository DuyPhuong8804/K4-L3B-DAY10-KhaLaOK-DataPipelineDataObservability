"""Smoke test: cleaning -> corruption -> quality check on corrupted data."""
from datetime import datetime, timezone
from pathlib import Path

from core.config import load_settings
from core.utils import read_json
from ingestion.crossref import PaperRecord
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from observability.quality import run_data_quality_checks, build_freshness_report

s = load_settings()

# Step 1: Load raw & clean
raw = read_json(s.paths.raw_records_json)
records = [PaperRecord(**r) for r in raw]
df_clean = build_clean_dataframe(records, datetime.now(timezone.utc))
print(f"[1] Clean: {len(df_clean)} rows")

# Step 2: Corrupt
log_path = s.paths.corruption_log
df_corrupted = corrupt_clean_dataframe(df_clean, log_path)
print(f"[2] Corrupted: {len(df_corrupted)} rows")

# Step 3: Show corruption log
corruption_log = read_json(log_path)
print(f"[3] Corruption log ({len(corruption_log)} entries):")
for entry in corruption_log:
    print(f"    - {entry['corruption_type']}: {entry['description']}")

# Step 4: Quality check on corrupted data (expect FAIL)
res = run_data_quality_checks(df_corrupted, s, "corrupted")
print(f"[4] Quality check on corrupted data: success = {res['success']}")
for r in res["results"]:
    print(f"    - {r['expectation_type']}: {'PASS' if r['success'] else 'FAIL'}")

# Step 5: Freshness on corrupted data
fr = build_freshness_report(df_corrupted, s, s.paths.quality_dir / "corrupted_freshness.json")
print(f"[5] Freshness: is_fresh = {fr['is_fresh']}, stale = {fr['stale_rows']}/{fr['total_rows']}")
