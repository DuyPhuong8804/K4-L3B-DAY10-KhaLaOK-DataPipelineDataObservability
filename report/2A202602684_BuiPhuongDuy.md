# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Bùi Phương Duy |
| MSSV | 2A202602684 |
| Khóa/Lớp | K4 — L3B |
| Tên nhóm | KhaLaOK |
| Vai trò chính | Trưởng nhóm — Source ingestion & Pipeline integration owner |
| Repository | https://github.com/DuyPhuong8804/K4-L3B-DAY10-KhaLaOK-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw ingestion | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref REST API hoặc snapshot `data/raw/crossref_response.json` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` (24 `PaperRecord`) | Hoàn thành |
| Baseline orchestration | `src/pipelines/phase1.py`: `run_phase1_pipeline(settings)` | Raw records, các hàm cleaning/quality/testset/index/evaluate | `data/clean/`, `data/embeddings/`, `data/eval/`, `baseline_metrics.json`, `phase1_report.md` | Hoàn thành |
| Corruption flow & repair | `src/pipelines/corruption_flow.py`: `run_corruption_flow_pipeline(settings)`, `repair_from_raw_snapshot(settings)` | Clean dataset, baseline metrics, test set, raw records | `corrupted_metrics.json`, `repaired_metrics.json`, collection `papers-corrupted` / `papers-repaired`, `corruption_report.md` | Hoàn thành |
| Helper ghi artifact | `src/core/utils.py`: `dataframe_records`, `write_dataframe` | DataFrame | CSV + JSON cho baseline/corrupted/repaired | Hoàn thành |
| Chạy tích hợp cuối & commit artifacts | Toàn bộ `data/` (trừ `data/raw/`) | Code của cả nhóm trên `main` | Commit `b8fe9cf`, `b4d1aa5`, bản cuối `15ff71b` | Hoàn thành |
| Độ tin cậy của judge & chuyển provider | `src/evaluation/metrics.py` (`_judge_answer`), `src/retrieval/agent.py`, `src/core/config.py` (`normalized_provider`) | Kết quả gọi LLM | Retry 3 lần trước khi fallback; trường `judge_fallbacks` trong metrics; agent trả văn bản thuần; nhận `LLM_PROVIDER=google` (commit `c4bf3d4`) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Review nhánh `kien` 3 vòng, chạy code thật trong worktree riêng | Lê Trung Kiên — `quality.py`, `reporting.py`, `corruption.py` | Phát hiện 2 báo cáo `.md` chứa số liệu không sinh từ pipeline (Hit Rate 0.8/0.4/0.8 khi chưa có file metrics nào) → bị xóa trước khi vào `main`; phát hiện lỗi `Stale rows` cột Repaired đọc nhầm `total_rows` → Kiên sửa ở `c083ad5` |
| Review nhánh `Thuhien` | Trần Thị Thu Hiền — `testset.py`, `retrieval/index.py` | Phát hiện manifest ghi đường dẫn tuyệt đối trên máy cá nhân (rubric −5đ) → Hiền sửa ở `1efed84`; phát hiện artifact nhị phân Chroma bị commit → được gỡ |
| Bổ sung Freshness SLA vào Quality Gate | `src/observability/quality.py` (module của Kiên) | Thêm `evaluate_freshness_sla()`; `run_data_quality_checks` trả thêm `freshness`, `gx_success`; `success = GX pass AND is_fresh` (commit `ec25971`) |
| Sửa kịch bản stale date đúng codelab | `src/ingestion/corruption.py` (module của Kiên) | Lùi `published` 365 ngày theo từng dòng thay vì gán cứng `2020-01-01` (commit `2991b4e`) |
| Phát hiện suy giảm quá yếu khi ghép corruption + test set thật | Kiên & Hiền | Phân tích từng lỗi trúng câu hỏi nào → nhóm quyết định tăng cường độ làm bẩn lên 35% (Kiên thực hiện, `4a4c30f`) thay vì chỉnh test set |
| `.gitattributes` cho Chroma | Toàn repo | Đánh dấu `data/chroma/**` là binary để `core.autocrlf` không làm hỏng file HNSW (`7b93c16`) |
| Kịch bản live demo CP6 | Cả nhóm | Kịch bản 5 phút chia vai A/B/C (tài liệu nội bộ, không nộp kèm repo); đo thời gian chạy thật ~20 giây/script với `HF_HUB_OFFLINE=1` |

Công cụ AI (Claude Code) được dùng để hỗ trợ viết code, review và chạy kiểm thử theo đúng chính sách AI của khóa (`docs/SUBMISSION.md` §4); mọi thay đổi đều được tôi chạy lại và đối chiếu artifact trước khi commit.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Ingestion Crossref có retry + fallback | `src/ingestion/crossref.py` | 24 records; `crossref_records.json` sinh lại trùng byte với bản gốc | Lệnh CP0 → `Tín hiệu hoàn thành: Đã tải 24 bài báo`; `git diff data/raw` rỗng |
| Nối luồng Phase 1 | `src/pipelines/phase1.py` | `baseline_metrics.json`: hit rate 1.0, token F1 1.0; `phase1_report.md` | `python script/run_phase1.py` → exit 0 |
| Nối luồng corruption → repair → so sánh | `src/pipelines/corruption_flow.py` | Bảng 3 trạng thái trên console + `corruption_report.md` | `python script/run_corruption_flow.py` → exit 0 |
| Chứng minh Repair idempotent | `repair_from_raw_snapshot` | Chạy corruption flow 2 lần: `papers_clean_repaired.json`, `repaired_metrics.json`, `corrupted_metrics.json` trùng từng byte; repaired == baseline clean | `filecmp.cmp(papers_clean.json, papers_clean_repaired.json)` → `True` |
| Chạy tích hợp cuối từ `data/` rỗng | toàn bộ `data/` | 14 deliverable theo `SUBMISSION.md`; 3 collection Chroma (24/27/24 docs); không có path tuyệt đối/secret; `judge_fallbacks = 10` | Commit `15ff71b` |
| Kiểm chứng chuyển provider (tiêu chí #5) | `core/config.py`, `retrieval/llm.py` | `mock` chạy trọn 2 pipeline exit 0; `google`→`gemini`, `Anthorpic`→`anthropic`; provider cần key báo lỗi rõ ràng | Chạy 2 script với `LLM_PROVIDER=mock` |
| Thử LLM judge thật (Gemini free tier) | `.env` (không commit) | Phase 1 chạy được với 9/10 câu do LLM chấm; phát hiện quota `gemini-3.6-flash` chỉ 20 request/ngày/model → không đủ cho một lượt đầy đủ | Lỗi `429 RESOURCE_EXHAUSTED`, `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier` |

Output cụ thể phần việc của tôi tạo ra: **bảng so sánh 3 trạng thái** in bởi `run_corruption_flow.py` và ghi vào `data/reports/corruption_report.md` — Hit Rate 1.0 → 0.7 → 1.0, Token F1 1.0 → 0.8223 → 1.0, Quality Gate PASS → FAIL → PASS.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

(1) Đưa dữ liệu Crossref vào pipeline một cách tái lập được và không phụ thuộc mạng; (2) nối các module của 3 người thành hai luồng chạy một lệnh; (3) chứng minh được Silent Failure và khả năng phục hồi bằng số liệu thật, trên cùng một test set.

### Cách triển khai

- **Ingestion:** `parse_crossref_payload` gỡ markup JATS (xóa tag trước rồi mới `html.unescape` để không biến `&lt;...&gt;` thành tag), ghép tên tác giả từ `given`/`family` hoặc `name` (tác giả là tổ chức), khử trùng subject, lấy ngày theo thứ tự `published → published-online → published-print → issued → created` và bổ sung tháng/ngày thiếu, bỏ record thiếu DOI/title/abstract/ngày. `fetch_source_records` mặc định đọc snapshot; chỉ khi `REFRESH_SOURCE=1` mới gọi `https://api.crossref.org/works` với retry 4 lần cho 429/5xx, tôn trọng `Retry-After`, lỗi thì fallback về snapshot.
- **Phase 1:** ingest → clean → **Quality Gate chạy trước khi index** (không qua thì `SystemExit`, không đưa dữ liệu bẩn vào vector store) → index `papers-baseline` → tạo/tái dùng test set → evaluate → report → demo agent (tự bỏ qua khi không có API key).
- **Corruption flow:** đọc `papers_clean.json` của Phase 1 → tiêm lỗi → chạy gate (FAIL) nhưng **vẫn index** `papers-corrupted` có chủ đích để đo tác hại → `repair_from_raw_snapshot` dựng lại từ `crossref_records.json` → gate phải PASS mới index `papers-repaired` → cả 3 trạng thái đánh giá trên **cùng** `data/eval/test_set.json` → report + bảng console.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `Settings` (`core/config.py`); raw snapshot `data/raw/crossref_records.json`; các hàm có chữ ký cố định: `build_clean_dataframe(records, run_date)`, `run_data_quality_checks(df, settings, name)`, `build_freshness_report(df, settings, path)`, `build_test_set(df, path)`, `LocalEmbeddingIndex.build(df, settings, path)`, `evaluate_pipeline(...)`, `corrupt_clean_dataframe(df, log_path)` |
| Output | Artifact đúng đường dẫn trong `config.Paths`; quality report theo quy ước `{state}_quality_report.json`; hàm `run_*_pipeline` trả dict metrics |
| Module phụ thuộc | `ingestion/cleaning.py`, `ingestion/corruption.py`, `observability/quality.py`, `observability/reporting.py` (Kiên); `evaluation/testset.py`, `retrieval/index.py` (Hiền); `evaluation/metrics.py` (scaffold) |
| Module sử dụng output | `script/run_phase1.py`, `script/run_corruption_flow.py`; corruption flow dùng `papers_clean.json`, `baseline_metrics.json`, `test_set.json` của Phase 1 |
| Điều kiện lỗi cần xử lý | API 429/5xx/mất mạng → fallback snapshot; thiếu artifact Phase 1 → dừng với thông báo "Run `python script/run_phase1.py` first"; baseline/repaired không qua gate → dừng, không index; không có LLM key → bỏ qua demo agent, judge dùng heuristic |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"
python script/run_phase1.py
python script/run_corruption_flow.py
python -c "import filecmp; print(filecmp.cmp('data/clean/papers_clean.json', 'data/clean/papers_clean_repaired.json', shallow=False))"
```

- **Kết quả mong đợi:** 24 bài; hai script exit 0; bảng 3 trạng thái cho thấy Corrupted thấp hơn rõ rệt và Repaired về bằng Baseline; repaired trùng baseline.
- **Kết quả thực tế:** đúng như trên — `Đã tải 24 bài báo`; Hit Rate 1.0 / 0.7 / 1.0; `True`.
- **Artifact/log:** `data/results/*_metrics.json`, `data/quality/*_quality_report.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Repair phải khôi phục dữ liệu sau khi bị tiêm 6 loại lỗi, và phải an toàn khi chạy lại nhiều lần (trong demo, trong CI).
- **Các phương án đã cân nhắc:** (a) vá trực tiếp dataframe bẩn — xóa dòng trùng, điền lại summary, sửa ngày; (b) dựng lại hoàn toàn từ raw snapshot bất biến `data/raw/crossref_records.json` qua đúng hàm cleaning của baseline.
- **Phương án đã chọn:** (b) — `repair_from_raw_snapshot()`.
- **Lý do:** (a) phải biết trước từng kiểu lỗi và không sửa được lỗi mất thông tin (summary bị xóa trắng, tiêu đề bị cắt, dòng bị drop); kết quả phụ thuộc trạng thái đầu vào nên không idempotent. (b) chỉ phụ thuộc bản raw bất biến nên chạy N lần cho cùng kết quả, và dùng lại đúng code cleaning nên không có "logic sửa" riêng dễ lệch với baseline. Đánh đổi: tốn thời gian re-index toàn bộ, chấp nhận được với 24 tài liệu.
- **Bằng chứng quyết định phù hợp:** chạy corruption flow 2 lần → `papers_clean_repaired.json` và `repaired_metrics.json` trùng từng byte; `papers_clean_repaired.json` trùng từng byte với `papers_clean.json`; metrics Repaired = Baseline (1.0 / 1.0 / 1.0 / 5.0); repaired quality 7/7 expectation PASS, fresh.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Khi review nhánh `kien`, file `corrupted_clean_dataset_quality_report.json` cho thấy expectation độ dài `summary` **PASS** dù corruption đã xóa trắng 3 summary.
- **Lệnh hoặc bước tái hiện:** tiêm lỗi → gọi `run_data_quality_checks` hai cách: truyền DataFrame trong bộ nhớ và truyền đường dẫn CSV. Kết quả expectation summary: DataFrame → `False` (đúng), CSV → `True` (sai).
- **Nguyên nhân gốc:** hàm chấp nhận đường dẫn và đọc lại CSV; `pd.read_csv` biến chuỗi rỗng thành `NaN`, mà `ExpectColumnValueLengthsToBeBetween` của GX bỏ qua giá trị null → summary rỗng không bị đếm là vi phạm.
- **Cách xử lý:** yêu cầu (qua prompt review) đưa hàm về chỉ nhận DataFrame như chữ ký gốc và thêm `ExpectColumnValuesToNotBeNull(column="summary")`; đồng thời thêm `ExpectColumnValueLengthsToBeBetween(column="title", min_value=8)` vì title bị cắt cũng đang lọt. Kiên sửa ở `52eb8cd`.
- **Cách xác minh sau khi sửa:** trên dữ liệu bẩn hiện tại, gate FAIL đúng 3 expectation: `paper_id` unique, độ dài `title`, độ dài `summary` (`data/quality/corrupted_quality_report.json`).
- **Điều học được:** kiểm định giá trị (length/regex) và kiểm định null là hai lớp khác nhau trong GX; chuyển đổi định dạng (DataFrame ↔ CSV) có thể âm thầm đổi ngữ nghĩa dữ liệu, nên gate phải chạy trên đúng object sẽ được index.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. Crossref trả JSON; `crossref.py` lưu nguyên bản rồi bóc thành 24 `PaperRecord` → `cleaning.py` gỡ JATS, khử trùng `paper_id`, tính `age_days`, ghép `text_for_embedding` 5 phần → Quality Gate (GX + Freshness) → `LocalEmbeddingIndex.build` embed bằng `all-MiniLM-L6-v2` và ghi vào collection ChromaDB (cosine), manifest lưu ở `data/embeddings/`.
2. Mỗi câu hỏi có `ground_truth` (đáp án) và `ground_truth_doc_ids` (DOI của bài đúng). Hit Rate = tỉ lệ câu có DOI đúng nằm trong top-k tài liệu truy xuất; Token F1 so từ giữa câu trả lời và `ground_truth`; judge chấm đúng/sai (fallback heuristic theo F1 khi không có LLM key).
3. Quality checks kiểm tra **tính hợp lệ của từng giá trị/cấu trúc** (null, unique, độ dài, số dòng); freshness kiểm tra **tính kịp thời của cả batch** theo thời gian (bao nhiêu % bài quá 180 ngày). Dữ liệu có thể hợp lệ hoàn toàn mà vẫn cũ — kịch bản stale date không làm vỡ expectation nào, chỉ Freshness SLA bắt được.
4. Nếu đổi câu hỏi giữa các trạng thái thì chênh lệch metric có thể đến từ độ khó câu hỏi chứ không phải dữ liệu; giữ nguyên `data/eval/test_set.json` (sha256 `bda74cf75f28…`) thì thay đổi duy nhất là dữ liệu trong index.
5. Repair thành công khi: repaired quality 7/7 PASS và fresh; `papers_clean_repaired.json` trùng baseline; `repaired_metrics.json` bằng `baseline_metrics.json` trên cùng test set.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.7000 | 1.0000 | 3/10 câu mất tài liệu đúng; phục hồi hoàn toàn |
| `mean_token_f1` | 1.0000 | 0.8223 | 1.0000 | Giảm do trả lời từ tài liệu sai và token rác `@#$%` |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | Judge heuristic (không có API key, `judge_fallbacks = 10` ở cả 3 trạng thái) nên bám theo F1 |
| `mean_judge_score` | 5.00 | 4.20 | 5.00 | |
| Quality checks | 7/7 PASS | 4/7 (FAIL `paper_id` unique, `title` length, `summary` length) | 7/7 PASS | Gate bắt đúng 3 loại lỗi cấu trúc |
| Freshness status | Fresh (1/24 = 4.17%) | Stale (8/27 = 29.63% > 25%) | Fresh (1/24) | Chỉ Freshness bắt được lỗi stale date |

### Kết luận từ số liệu

1. Nhân bản dòng + cắt tiêu đề + xóa trắng summary → gate FAIL ở `paper_id` unique / độ dài `title` / độ dài `summary`, lùi ngày 365 ngày → Freshness 29.63% > 25% → Hit Rate 1.0 → 0.7, Token F1 1.0 → 0.8223 — trong khi script vẫn exit 0 (Silent Failure).
2. `repair_from_raw_snapshot` dựng lại từ raw → gate 7/7 PASS, Freshness về 4.17% → Hit Rate, Token F1, judge đều về đúng mức baseline.

**Corruption ảnh hưởng rõ nhất:** tổ hợp **truncate title + blank summary** trên cùng một bài. Đối chiếu `corrupted_answers.json` với `corruption_log.json`: 2/3 câu mất retrieval (q03, q08) rơi vào bài bị cả hai lỗi này. Câu hỏi đặt tiêu đề trong dấu nháy để tra cứu chính xác; tiêu đề bị cắt làm tra cứu chính xác thất bại, còn summary rỗng làm vector gần như chỉ còn metadata, nên semantic search cũng trượt. Câu mất retrieval còn lại (q04) do bài bị drop.

**Kết quả khác kỳ vọng:**
- q04 mất tài liệu đúng (bài `…808` bị drop) nhưng Token F1 vẫn 1.0: agent trả lời bằng categories của một bài khác trùng nhãn. Đây là Silent Failure "đúng do may mắn" — chỉ Hit Rate phát hiện, F1 và judge không.
- Stale date không làm giảm metric nào (các câu trên bài bị lùi ngày không hỏi về ngày) → lỗi này chỉ lộ ra qua Freshness SLA, minh chứng vì sao cần observability riêng thay vì chỉ nhìn metric của agent.
- Lần tích hợp đầu (mỗi lỗi 3–5 dòng) chỉ giảm Hit Rate xuống 0.9, F1 giữ 1.0; tôi kiểm tra từng lỗi trúng câu hỏi nào và thấy hầu hết rơi vào trường không được hỏi. Nhóm tăng cường độ lên 35% số dòng thay vì chỉnh test set để số liệu vẫn trung thực.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** giữ raw bất biến làm lineage anchor biến Repair thành phép tính lại thuần túy — idempotent, kiểm chứng được bằng so sánh byte, không cần logic sửa riêng.
2. **Data quality/observability:** gate phải chạy trên đúng object sắp được index và trước khi index; quality và freshness là hai trục độc lập — thiếu một trục sẽ bỏ lọt cả một lớp lỗi.
3. **Ảnh hưởng tới RAG:** dữ liệu bẩn không làm hệ thống crash mà làm câu trả lời sai lặng lẽ; một metric (F1) có thể vẫn đẹp trong khi retrieval đã sai, nên cần đo nhiều tín hiệu cùng lúc.

### Nếu có thêm thời gian

Thêm expectation so sánh số dòng với baseline (ví dụ `ExpectTableRowCountToBeBetween(min_value=0.9 × baseline)`) để gate bắt được kịch bản **drop latest** — hiện là loại lỗi duy nhất chỉ lộ qua metric. Đo bằng cách chạy lại corruption flow và kiểm tra `corrupted_quality_report.json` có thêm expectation FAIL tương ứng với `paper_ids` bị drop trong `corruption_log.json`.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Bùi Phương Duy
**Ngày xác nhận:** 2026-09-26
