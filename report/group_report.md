# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4 — L3B |
| Tên nhóm | KhaLaOK |
| Repository | https://github.com/DuyPhuong8804/K4-L3B-DAY10-KhaLaOK-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Bùi Phương Duy | 2A202602684 | Trưởng nhóm — Source ingestion & Pipeline integration | `src/ingestion/crossref.py`; `src/pipelines/phase1.py` (`run_phase1_pipeline`); `src/pipelines/corruption_flow.py` (`run_corruption_flow_pipeline`, `repair_from_raw_snapshot`); helper `src/core/utils.py`; chạy tích hợp cuối và commit `data/` |
| 2 | Lê Trung Kiên | 2A202602748 | Data model, Observability & Corruption | `src/ingestion/cleaning.py`; `src/observability/quality.py` (GX 1.x suite); `src/ingestion/corruption.py` (6 kịch bản); `src/observability/reporting.py` |
| 3 | Trần Thị Thu Hiền | 2A202602737 | Evaluation set & Retrieval | `src/evaluation/testset.py`; `src/retrieval/index.py` (manifest đường dẫn tương đối); lazy import `evaluation/`, `retrieval/`; `tests/test_evaluation.py` (7 test) |

Ownership khớp với lịch sử commit trên `main` (Insights → Contributors). Các phần một thành viên bổ sung vào module của người khác được ghi rõ trong báo cáo cá nhân (ví dụ Freshness SLA trong `quality.py` và kịch bản stale date 365 ngày do Duy bổ sung).

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm hoàn thành đầy đủ hai luồng end-to-end: `run_phase1.py` (baseline) và `run_corruption_flow.py` (corruption → repair → so sánh), cả hai chạy exit 0 trên `main` từ thư mục `data/` rỗng (chỉ giữ raw snapshot). Baseline tạo ra raw records (24), cleaned dataset CSV/JSON, collection ChromaDB `papers-baseline`, test set 10 câu, `baseline_metrics.json`, báo cáo quality/freshness và `phase1_report.md`. Trên dữ liệu sạch, Retrieval Hit Rate và Token F1 đều đạt 1.0, Quality Gate 7/7 PASS, Freshness 1/24 bài quá hạn (fresh).

Sáu kịch bản làm bẩn (35% số dòng mỗi kịch bản, drop 20% bài mới nhất) khiến Hit Rate giảm xuống 0.7 và Token F1 xuống 0.8223 trong khi script vẫn không báo lỗi — minh chứng Silent Failure. Quality Gate phát hiện 3 expectation FAIL và Freshness SLA vỡ (29.63% > 25%). Tổ hợp cắt tiêu đề + xóa trắng summary gây mất retrieval nhiều nhất. Repair dựng lại từ raw snapshot phục hồi toàn bộ chỉ số về đúng baseline và trùng từng byte với dữ liệu sạch.

Giới hạn chính: không cấu hình API key LLM nên judge dùng heuristic theo Token F1, Ragas không chạy; bộ dữ liệu nhỏ (24 bài, 10 câu hỏi); kịch bản drop latest chưa có expectation riêng.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (REFRESH_SOURCE=1) / snapshot data/raw/crossref_response.json
    -> raw response + raw records (data/raw/, bất biến — lineage anchor)
    -> cleaning & data modeling (JATS strip, dedup paper_id, age_days, text_for_embedding)
    -> Quality Gate: GX 1.x (7 expectations) + Freshness SLA  ── FAIL → dừng, không index
    -> embedding all-MiniLM-L6-v2 + ChromaDB "papers-baseline"
    -> test set 10 câu (dùng chung 3 trạng thái) -> evaluation baseline -> phase1_report.md
    -> corruption (6 kịch bản) -> gate FAIL (vẫn index có chủ đích để đo tác hại)
    -> re-index "papers-corrupted" + re-evaluate
    -> repair_from_raw_snapshot (dựng lại từ data/raw/) -> gate PASS
    -> re-index "papers-repaired" + re-evaluate
    -> corruption_report.md (Baseline vs Corrupted vs Repaired)
```

Khác starter: Quality Gate được đặt **trước** bước index để dữ liệu không đạt chuẩn không bao giờ vào vector store.

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref `/works` hoặc snapshot | Retry 4 lần cho 429/5xx + `Retry-After`, fallback snapshot, parse & validate record | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Duy |
| Cleaning | `PaperRecord` list, `run_date` | Gỡ JATS/khoảng trắng, dedup `paper_id`, bỏ dòng thiếu title/summary, `age_days`, `text_for_embedding` 5 phần | `data/clean/papers_clean.{csv,json}` | Kiên |
| Embedding/index | Clean DataFrame | `all-MiniLM-L6-v2`, ChromaDB cosine, 3 collection tách biệt, manifest path tương đối | `data/chroma/`, `data/embeddings/*.json` | Scaffold + Hiền |
| Evaluation | Clean DataFrame, index | Test set 10 câu / 4 dạng; Hit Rate, Token F1, judge | `data/eval/test_set.json`, `data/results/*_metrics.json`, `*_answers.json` | Hiền (test set), scaffold (metrics) |
| Observability | DataFrame | GX 1.x ephemeral context 7 expectations + Freshness SLA | `data/quality/*_quality_report.json`, `*freshness_report.json` | Kiên (GX), Duy (Freshness trong gate) |
| Corruption/repair | Clean DataFrame / raw records | 6 kịch bản seed 42; repair dựng lại từ raw | `data/results/corruption_log.json`, `data/clean/papers_clean_{corrupted,repaired}.*` | Kiên (corruption), Duy (repair) |
| Orchestration | `Settings` | Thứ tự chạy, gate, chia collection, dùng chung test set | `phase1_report.md`, `corruption_report.md`, bảng console | Duy |
| Reporting | Metrics, quality, freshness | Markdown 3 trạng thái, phần phân tích sinh từ số liệu thật | `data/reports/*.md` | Kiên |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` (không đặt `GOOGLE_API_KEY` → judge fallback heuristic, demo agent bỏ qua; `judge_fallbacks = 10` trong cả 3 file metrics) |
| `LLM_MODEL` | `gemini-3.6-flash` (không được gọi khi không có key) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 (`max_results=24`, snapshot) |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày; stale nếu > 25% số bài quá ngưỡng |
| Random seed, nếu có | 42 (corruption); `CORRUPTION_RATE = 0.35` |

### Lệnh cài đặt

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Trên Windows PowerShell nên đặt `$env:PYTHONIOENCODING = "utf-8"` để console in được tiếng Việt, và `$env:HF_HUB_OFFLINE = "1"` sau lần tải model đầu tiên để bước load embedding không gọi mạng (nhóm gặp trường hợp treo ở bước này khi mạng chập chờn).

### Lệnh chạy

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công (exit 0, ~21 giây với `HF_HUB_OFFLINE=1`) | 2026-09-26 14:50 (GMT+7) | Commit `15ff71b`: `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công (exit 0, ~21 giây với `HF_HUB_OFFLINE=1`) | 2026-09-26 14:50 (GMT+7) | Commit `15ff71b`: `data/results/{corrupted,repaired}_metrics.json`, `data/reports/corruption_report.md` |

Toàn bộ lệnh nghiệm thu trong `docs/CHECKPOINTS.md` và codelab đã chạy lại nguyên văn trên phiên bản nộp: `Môi trường sẵn sàng`, `Đã tải 24 bài báo`, `Clean thành công 24 dòng`, `Quality check status = True`, `Sinh được 10 câu hỏi test`, `Corrupted 27 dòng`; `pytest` 7/7 pass. Pipeline cũng chạy trọn với `LLM_PROVIDER=mock` (exit 0).

Chạy lại corruption flow lần 2 cho `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_log.json` và `papers_clean_repaired.json` trùng từng byte với lần 1.

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API `https://api.crossref.org/works`; bài nộp dùng snapshot `data/raw/crossref_response.json` của lab |
| Query/filter | `query="agentic retrieval augmented generation large language model"`, `filter=from-pub-date:<run_date−180d>,has-abstract:true`, `rows=24` |
| Thời điểm lấy dữ liệu | Snapshot lab; lần xử lý cuối 2026-09-26 14:50. Gọi API thật (`REFRESH_SOURCE=1`) đã được thử: trả 24 record hợp lệ nhưng không ghi đè snapshot |
| Số record nhận được | 24 (24 DOI duy nhất) |
| Cơ chế retry/backoff | Tối đa 4 lần cho HTTP 429/500/502/503/504 và lỗi mạng; chờ theo `Retry-After` (tối đa 60s) hoặc 2^attempt giây; hết lượt → fallback snapshot |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | str (DOI, lowercase) | Có | Document ID ổn định | Thiếu → bỏ record; trùng → giữ bản đầu |
| `title` | str | Có | Tiêu đề | Gỡ markup; rỗng → bỏ record |
| `summary` | str | Có | Abstract | Gỡ JATS + unescape HTML; rỗng → bỏ record |
| `authors` | list[str] | Không | Tác giả | `given family` hoặc `name` (tổ chức); rỗng → list rỗng |
| `categories` / `primary_category` | list[str] / str | Không | Subject Crossref | Khử trùng giữ thứ tự; rỗng → `[]` / `""` |
| `published` | str `YYYY-MM-DD` | Có | Ngày xuất bản | Lấy theo `published → published-online → published-print → issued → created`; thiếu tháng/ngày → 1; không có → bỏ record |
| `updated`, `abs_url`, `pdf_url`, `comment` | str | Không | Metadata phụ | Fallback về `published` / `https://doi.org/<DOI>` |
| `age_days` | int | Có (clean) | Tuổi bài tại `run_date` | Tính khi cleaning |
| `authors_joined`, `categories_joined`, `summary_chars`, `text_for_embedding` | str/int | Có (clean) | Cột phục vụ index & QA | Sinh khi cleaning |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Gỡ thẻ JATS (`<jats:p>`…) và khoảng trắng thừa trong abstract | Validity | 24 | Không còn `<jats` trong `papers_clean.json` |
| Khử trùng lặp theo `paper_id` | Uniqueness | 0 (snapshot không trùng) | GX `ExpectColumnValuesToBeUnique(paper_id)` PASS |
| Bỏ dòng thiếu title hoặc summary | Completeness | 0 | GX not-null/length PASS; 24 → 24 dòng |
| Tính `age_days = run_date − published` | Timeliness | 24 (1 bài > 180 ngày) | `freshness_report.json`: 1/24 |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`paper_id` là DOI chuẩn hóa chữ thường — ổn định giữa các lần chạy và giữa raw/clean/index. `age_days` là số ngày từ `published` đến thời điểm chạy (UTC), dùng cho Freshness SLA. `text_for_embedding` ghép 5 phần theo mẫu `Title: … / Authors: … / Categories: … / Published: … / Summary: …` để vector mang cả nội dung lẫn metadata mà câu hỏi hay hỏi tới.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| Các `question_type` | `summary` (3), `authors` (3), `date` (2), `categories` (2) |
| Ground-truth document ID | `paper_id` (DOI) của bài dùng để sinh câu hỏi; tiêu đề đặt trong dấu nháy để QA tra cứu chính xác |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB persistent `data/chroma`, cosine; `papers-baseline` / `papers-corrupted` / `papers-repaired` |
| Retrieval `top_k` | 4 |
| LLM provider/model | `gemini` / `gemini-3.6-flash` — không có key nên judge dùng heuristic theo Token F1 (`judge_fallbacks = 10`) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (sha256 `bda74cf75f28…`) |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set được sinh một lần từ dữ liệu sạch (chọn rải đều theo `paper_id`, cố định) và mọi trạng thái đều đọc cùng file. Khi câu hỏi, đáp án và DOI đúng không đổi, thay đổi metric chỉ có thể đến từ dữ liệu trong index — đúng biến số cần đo. Nhóm cũng quyết định **không chỉnh test set** để làm tăng mức suy giảm, mà tăng cường độ corruption.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | 24 records, sinh lại trùng byte |
| Cleaned dataset | `data/clean/` | Có | 24 dòng, 16 cột |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/` | Có | `persist_path: "data/chroma"`, 3 collection (24/27/24 docs) |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | |
| Quality/freshness | `data/quality/` | Có | baseline/corrupted/repaired quality + freshness |
| Baseline report | `data/reports/phase1_report.md` | Có | |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 10/10 câu có DOI đúng trong top-4 |
| `mean_token_f1` | 1.0000 | Câu trả lời trích xuất khớp hoàn toàn đáp án |
| `judge_accuracy` | 1.0000 | Judge heuristic (F1 ≥ 0.5 → đúng); `judge_fallbacks = 10/10` xác nhận không câu nào do LLM chấm |
| `mean_judge_score` | 5.00 | |
| Ragas, nếu có | N/A | Không chạy (`RUN_RAGAS` không bật, không có LLM key) |

Baseline đạt tuyệt đối vì câu hỏi dạng trích xuất có tiêu đề chính xác trên corpus sạch 24 bài — đây là mốc tham chiếu, không phải đánh giá năng lực tổng quát của agent.

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `ExpectTableRowCountToBeBetween` | Volume | 1–100 dòng | PASS (24) | `data/quality/baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull(paper_id)` | Completeness | 0 null | PASS | như trên |
| `ExpectColumnValuesToBeUnique(paper_id)` | Uniqueness | 0 trùng | PASS | như trên |
| `ExpectColumnValuesToNotBeNull(title)` | Completeness | 0 null | PASS | như trên |
| `ExpectColumnValueLengthsToBeBetween(title)` | Validity | ≥ 8 ký tự | PASS | như trên |
| `ExpectColumnValuesToNotBeNull(summary)` | Completeness | 0 null | PASS | như trên |
| `ExpectColumnValueLengthsToBeBetween(summary)` | Validity | ≥ 10 ký tự | PASS | như trên |

Gate chỉ PASS khi cả 7 expectation PASS **và** Freshness SLA đạt (`success = gx_success AND is_fresh`).

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | Clean dataset trước khi index (`age_days`) |
| Timestamp mới nhất | 2026-07-22 (cũ nhất 2026-03-28) |
| Ngưỡng freshness | 180 ngày; tối đa 25% bài vượt ngưỡng |
| Trạng thái baseline | Fresh |
| Lý do | 1/24 bài (4.17%) vượt 180 ngày (bài 2026-03-28, 182 ngày) < 25% |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| Drop latest | Bỏ 20% bài mới nhất theo `published` | 4 | (không có expectation riêng) | q04 mất retrieval | Dựng lại từ raw |
| Blank summary | Gán summary = `""` | 7 | `summary` length FAIL | FAIL; góp phần mất retrieval q03, q08 | Dựng lại từ raw |
| Inject noise | Chèn `@#$%` sau mỗi 3 từ trong summary | 7 | (không đổi cấu trúc) | Token F1 q01 = 0.968, q09 = 0.970 | Dựng lại từ raw |
| Truncate title | Cắt title còn 7 ký tự | 7 | `title` length FAIL | FAIL; tra cứu tiêu đề thất bại ở q03, q08 | Dựng lại từ raw |
| Stale date | Lùi `published` 365 ngày, `age_days` +365 | 7 | Freshness SLA vỡ | 8/27 = 29.63% > 25% → stale; không làm giảm metric | Dựng lại từ raw |
| Duplicate rows | Nhân bản 7 dòng đầu | 7 | `paper_id` unique FAIL | FAIL; 20 → 27 dòng | Dựng lại từ raw |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: đủ 6 loại theo đúng thứ tự, mỗi mục có `corruption_type`, `affected_rows`, `paper_ids` (khớp số lượng) và `description` sinh từ tham số thực tế; seed cố định nên log tái lập được.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

`repair_from_raw_snapshot()` không đọc dữ liệu bẩn: nó nạp lại `data/raw/crossref_records.json` (bất biến, được lưu ngay khi ingest) và chạy đúng hàm `build_clean_dataframe` của baseline. Dữ liệu sau repair phải qua lại Quality Gate (7/7 PASS, fresh) mới được index vào collection riêng `papers-repaired`, rồi đánh giá trên cùng test set. Bằng chứng: `papers_clean_repaired.json` trùng từng byte với `papers_clean.json`, và chạy repair 2 lần cho kết quả giống hệt (idempotent).

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.7000 | 1.0000 | −0.3000 | 100% | 3/10 câu mất tài liệu đúng |
| `mean_token_f1` | 1.0000 | 0.8223 | 1.0000 | −0.1777 | 100% | Trả lời từ tài liệu sai + token rác |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | −0.2000 | 100% | Judge heuristic theo F1 |
| `mean_judge_score` | 5.00 | 4.20 | 5.00 | −0.80 | 100% | |
| Quality checks pass/fail | 7/7 PASS | 4/7 (3 FAIL) | 7/7 PASS | −3 expectation | 100% | FAIL: `paper_id` unique, `title` length, `summary` length |
| Freshness status | Fresh (4.17%) | Stale (29.63%) | Fresh (4.17%) | +25.46 điểm % | 100% | Chỉ freshness bắt được stale date |

Kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. Duplicate rows + truncate title + blank summary + stale date → GX FAIL 3 expectation và Freshness 29.63% > 25% (`corrupted_quality_report.json`) → Hit Rate 1.0 → 0.7, Token F1 1.0 → 0.8223 (`corrupted_metrics.json`), trong khi `run_corruption_flow.py` vẫn exit 0 — Silent Failure mà chỉ gate phát hiện.
2. `repair_from_raw_snapshot` dựng lại từ raw → gate 7/7 PASS, Freshness 4.17% (`repaired_quality_report.json`) → mọi metric về đúng baseline (`repaired_metrics.json`).

Đối chiếu `corrupted_answers.json` với `corruption_log.json`: 2/3 câu mất retrieval (q03, q08) rơi vào bài vừa bị cắt tiêu đề vừa bị xóa summary — mất cả đường tra cứu chính xác lẫn nội dung semantic. q04 mất retrieval do bài bị drop nhưng F1 vẫn 1.0 vì categories trùng với một bài khác — chỉ Hit Rate phát hiện được. Stale date không làm giảm metric nào nhưng Freshness SLA bắt được, cho thấy vai trò riêng của observability.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi ghép `corruption.py` (Kiên) với `testset.py` thật (Hiền) và pipeline (Duy), bảng so sánh gần như không suy giảm: Hit Rate 1.0 → 0.9 → 1.0, Token F1 giữ 1.0 — không đủ minh chứng cho tiêu chí #8.
- **Nguyên nhân:** Mỗi kịch bản chỉ làm bẩn 3–5/20 dòng và chọn ngẫu nhiên độc lập với test set; ánh xạ `paper_ids` trong log với `ground_truth_doc_ids` cho thấy lỗi phần lớn rơi vào trường không được hỏi (bài bị xóa summary lại bị hỏi categories, bài bị lùi ngày lại bị hỏi authors, truncate title không trúng câu nào). Ngoài ra noise chèn giữa summary không chạm tới câu đầu mà QA trích xuất.
- **Cách xử lý:** Nhóm cân nhắc hai hướng (tăng cường độ corruption vs. chọn câu hỏi ưu tiên bài mới) và chọn hướng thứ nhất để không "tối ưu test set cho số đẹp": `CORRUPTION_RATE = 0.35` cho kịch bản 2–6 và rải noise khắp summary (`4a4c30f`). Seed giữ nguyên 42, không thử nhiều seed.
- **Cách xác minh:** Chạy lại hai pipeline → Hit Rate 1.0 → 0.7 → 1.0, Token F1 1.0 → 0.8223 → 1.0; chạy corruption flow 2 lần cho kết quả trùng từng byte.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Không có LLM key → judge heuristic theo F1, Ragas bỏ qua, demo agent không chạy | `judge_accuracy` không độc lập với `mean_token_f1` | Nhóm đã thử Gemini free tier: chạy được 1 lần Phase 1 với LLM judge (9/10 câu do LLM chấm, 1 câu lỗi tạm thời) nhưng quota `gemini-3.6-flash` chỉ 20 request/ngày/model, không đủ ~30+ lệnh gọi cho một lượt đầy đủ, và model bỏ qua `temperature=0` nên điểm judge không cố định. Đã thêm retry 3 lần + trường `judge_fallbacks` để khi có key trả phí vẫn báo cáo trung thực; bước tiếp theo: bật billing, chạy lại và so judge LLM với heuristic trên cùng `*_answers.json` |
| Drop latest không có expectation riêng | Mất 20% bài mới chỉ lộ qua metric | Thêm expectation số dòng tối thiểu theo baseline; kiểm tra `corrupted_quality_report.json` có FAIL tương ứng |
| Corpus nhỏ (24 bài, 10 câu), câu hỏi dạng trích xuất có tiêu đề | Baseline 1.0 không phản ánh độ khó thực tế | Mở rộng `max_results` và thêm câu hỏi không chứa tiêu đề; theo dõi Hit Rate baseline |
| Dùng snapshot cố định | Không phản ánh drift của nguồn sống | Chạy định kỳ với `REFRESH_SOURCE=1` và so freshness/metrics giữa các lần |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng. *(Duy: `report/2A202602684_BuiPhuongDuy.md`; Kiên: `report/2A202602748_LeTrungKien.md`; Hiền: `report/2A202602737_TranThiThuHien.md`)*
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
