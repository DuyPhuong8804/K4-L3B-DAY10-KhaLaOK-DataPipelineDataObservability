# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `KhaLaOK`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-KhaLaOK-DataPipelineDataObservability`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Bùi Phương Duy | 2A202602684 | phuongduy080804@gmail.com | Trưởng nhóm — Source ingestion & Pipeline integration (`crossref.py`, `phase1.py`, `corruption_flow.py`, `core/utils.py`; chạy tích hợp cuối) | `report/2A202602684_BuiPhuongDuy.md` |
| 2 | Lê Trung Kiên | 2A202602748 | kienthemano12@gmail.com | Data model, Observability & Corruption (`cleaning.py`, `quality.py` GX 1.x, `corruption.py`, `reporting.py`) | `report/2A202602748_LeTrungKien.md` |
| 3 | Trần Thị Thu Hiền | 2A202602737 | thuhientranthi.ai@gmail.com | Evaluation set & Retrieval (`testset.py`, `retrieval/index.py`, `tests/test_evaluation.py`) | `report/2A202602737_TranThiThuHien.md` |

Phân công theo checkpoint:

| Checkpoint | Owner chính | Hỗ trợ |
|---|---|---|
| CP0 — Môi trường & Ingestion | Duy | — |
| CP1 — Cleaning & GX 1.x + Freshness | Kiên | Duy (Freshness SLA trong gate) |
| CP2 — Test set & ChromaDB index | Hiền | — |
| CP3 — Baseline pipeline & báo cáo pha 1 | Duy | Kiên (`generate_phase1_report`) |
| CP4 — Corruption suite | Kiên | Duy (kịch bản stale date 365 ngày) |
| CP5 — Repair & báo cáo 3 trạng thái | Duy | Kiên (`generate_corruption_report`) |
| CP6 — Live demo & nộp bài | Cả nhóm | Duy (chuẩn bị kịch bản demo, rà checklist nộp bài) |

---

## # Cá nhân

### ## BuiPhuongDuy-2A202602684
- **Vai trò:** Trưởng nhóm — Source ingestion & Pipeline integration.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng `src/ingestion/crossref.py`: parse payload Crossref (gỡ JATS, chuẩn hóa tác giả/subject/ngày, loại record không hợp lệ), gọi API có retry cho 429/5xx tôn trọng `Retry-After`, fallback đọc snapshot offline, lưu 2 raw artifact phục vụ lineage (`7ed4783`).
  - Nối luồng `src/pipelines/phase1.py` — `run_phase1_pipeline(settings)`: ingest → clean → Quality Gate trước khi index → ChromaDB `papers-baseline` → test set → evaluate → `phase1_report.md` (`d378044`, `03f3291`).
  - Nối luồng `src/pipelines/corruption_flow.py` — `run_corruption_flow_pipeline(settings)` và `repair_from_raw_snapshot(settings)`: repair idempotent dựng lại từ raw snapshot, gate trước khi index `papers-repaired`, bảng so sánh 3 trạng thái (`d378044`, `593ceca`).
  - Bổ sung `evaluate_freshness_sla()` vào Quality Gate (`ec25971`) và sửa kịch bản stale date lùi 365 ngày theo codelab (`2991b4e`); helper `write_dataframe` trong `core/utils.py`.
  - Review, chạy kiểm chứng và merge nhánh `kien`, `Thuhien`; chặn 2 báo cáo chứa số liệu không sinh từ pipeline trước khi vào `main`; chạy tích hợp cuối từ `data/` rỗng và commit artifacts (`b8fe9cf`, `b4d1aa5`, bản cuối `15ff71b`).
  - Tăng độ tin cậy judge (retry + `judge_fallbacks`), agent trả văn bản thuần, nhận alias `LLM_PROVIDER=google` (`c4bf3d4`).
- **Điều học được / Đóng góp chính:**
  - Giữ raw bất biến làm lineage anchor giúp Repair trở thành phép tính lại idempotent — kiểm chứng bằng việc dữ liệu repaired trùng từng byte với baseline và chạy lại 2 lần cho cùng kết quả.
  - Quality Gate phải chạy trên đúng object sắp được index; quality (hợp lệ) và freshness (kịp thời) là hai trục độc lập — stale date chỉ bị Freshness SLA bắt được.

### ## LeTrungKien-2A202602748
- **Vai trò:** Data model, Observability & Corruption.
- **Công việc chi tiết đã hoàn thành (theo lịch sử commit):**
  - `src/ingestion/cleaning.py` — `build_clean_dataframe`: gỡ JATS, `age_days`, dedup `paper_id`, `text_for_embedding` 5 phần (`817922d`).
  - `src/observability/quality.py` — suite GX 1.x ephemeral context với 7 expectations (`7b80133`, `52eb8cd`).
  - `src/ingestion/corruption.py` — 6 kịch bản corruption, seed 42, log theo `paper_ids`, tăng cường độ 35% và rải noise khắp summary (`52eb8cd`, `4a4c30f`).
  - `src/observability/reporting.py` — báo cáo pha 1 và báo cáo 3 trạng thái với phần phân tích sinh từ số liệu thật (`52eb8cd`, `c083ad5`).
- **Điều học được / Đóng góp chính:**
  - Đóng góp chính: Quality Gate GX 1.x bắt đúng 3 loại lỗi trên dữ liệu bẩn (`paper_id` unique, độ dài `title`, độ dài `summary`); bộ corruption 6 kịch bản tái lập được (seed 42) làm Hit Rate giảm 1.0 → 0.7; báo cáo 3 trạng thái có phần phân tích sinh từ số liệu thật.

### ## TranThiThuHien-2A202602737
- **Vai trò:** Evaluation set & Retrieval.
- **Công việc chi tiết đã hoàn thành (theo lịch sử commit):**
  - `src/evaluation/testset.py` — `build_test_set`: 10 câu hỏi cố định phủ 4 dạng (summary/authors/date/categories), chọn rải đều theo `paper_id`, tiêu đề trong dấu nháy cho tra cứu chính xác (`e4fc9cd`, `cc22afe`).
  - `src/retrieval/index.py` — manifest embeddings lưu `persist_path` tương đối `data/chroma` thay cho đường dẫn tuyệt đối (`1efed84`); lazy import trong `evaluation/`, `retrieval/`.
  - `tests/test_evaluation.py` — 7 test pytest (test set, token F1, QA ưu tiên tiêu đề chính xác, manifest đường dẫn tương đối).
- **Điều học được / Đóng góp chính:**
  - Đóng góp chính: bộ benchmark 10 câu cố định dùng chung cho baseline/corrupted/repaired giúp so sánh công bằng; loại bỏ đường dẫn tuyệt đối khỏi manifest (tránh −5đ); bộ test pytest là nền cho bonus B3.
