# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Lê Trung Kiên             |
| MSSV               | 2A202602748                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | KhaLaOK     |
| Vai trò chính    | Data Quality, Corruption & Observability Specialist (Người B) |
| Repository         | https://github.com/DuyPhuong8804/K4-L3B-DAY10-KhaLaOK-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Ingestion & Data Cleaning | `src/ingestion/cleaning.py` (`build_clean_dataframe`) | List[PaperRecord] thô từ Crossref API | Clean DataFrame (24 dòng), 5-part `text_for_embedding`, `age_days` | Hoàn thành |
| Data Corruption Simulation | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | Clean DataFrame | Corrupted DataFrame (27 dòng) + `corruption_log.json` | Hoàn thành |
| Data Quality Gate & SLA | `src/observability/quality.py` (`run_data_quality_checks`, `build_freshness_report`) | DataFrame / Clean CSV | Quality Report JSON (GX 1.x) + Freshness Report JSON | Hoàn thành |
| Automated Reporting | `src/observability/reporting.py` (`generate_phase1_report`, `generate_corruption_report`) | Metrics dicts & Quality dicts | `phase1_report.md` & `corruption_report.md` (3-State Comparison) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Đưa hợp đồng dữ liệu (Data Contract) | Người A (`phase1.py`) & Người C (`testset.py`) | Đảm bảo schema DataFrame chuẩn hóa (`text_for_embedding`, `paper_id`, `age_days`) để A build pipeline và C tạo testset |
| Tích hợp luồng Corruption Flow | Người A (`src/pipelines/corruption_flow.py`) | Cung cấp hàm `corrupt_clean_dataframe` ổn định với `seed=42` giúp đo đạc Silent Failure chính xác |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Làm sạch và định dạng văn bản | `src/ingestion/cleaning.py` | DataFrame 24 dòng không trùng `paper_id`, 5-part `text_for_embedding` | `python -c "from ingestion.cleaning import build_clean_dataframe..."` -> 24 dòng |
| Mô phỏng 6 kịch bản sự cố bẩn | `src/ingestion/corruption.py` | Corrupted DataFrame + `data/results/corruption_log.json` chứa `paper_ids` | `python script/run_corruption_flow.py` -> Log 6 kịch bản, 27 dòng |
| Đóng cổng kiểm duyệt Quality Gate | `src/observability/quality.py` | `data/quality/*_quality_report.json` (Great Expectations 1.x) | `run_data_quality_checks` -> Baseline: PASS (True), Corrupted: FAIL (False) |
| Theo dõi Freshness SLA | `src/observability/quality.py` | `data/quality/*_freshness_report.json` | `build_freshness_report` -> Corrupted: `is_fresh=False`, Repaired: `is_fresh=True` |
| Báo cáo tự động Data-Driven | `src/observability/reporting.py` | `data/reports/phase1_report.md` & `corruption_report.md` | `generate_corruption_report` -> Render bảng so sánh 3 trạng thái & phân tích động |

Nêu một artifact cụ thể mà phần việc của bạn tạo ra:
- **`data/reports/corruption_report.md`**: Báo cáo Markdown tự động so sánh 3 trạng thái (Baseline vs Corrupted vs Repaired), bóc tách từng Expectation bị FAIL của Great Expectations 1.x và trình bày sự suy giảm chỉ số RAG (Hit Rate từ 1.0000 -> 0.7000) cùng sự phục hồi sau khi Idempotent Repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đảm bảo dữ liệu đầu vào của hệ thống RAG được làm sạch chuẩn xác, phát hiện tự động các sự cố dữ liệu bẩn (Silent Failure) thông qua cổng Data Quality Gate và Freshness SLA, đồng thời xuất báo cáo so sánh đa trạng thái hoàn toàn dựa trên số liệu thực tế (Data-driven).

### Cách triển khai

1. **`cleaning.py`**: Dùng Regex `_strip_jats` xóa toàn bộ JATS XML tags trong title/summary; tính `age_days` chuẩn UTC; xây dựng `text_for_embedding` chứa 5 phần (`Title`, `Authors`, `Categories`, `Published`, `Summary`); lọc trùng `paper_id` và khuyết thông tin.
2. **`corruption.py`**: Áp dụng `CORRUPTION_RATE = 0.35` để làm bẩn linh hoạt 6 kịch bản theo tỉ lệ. Chèn ký tự rác `@#$%` rải rác toàn bộ summary (sau mỗi 3-4 từ) để làm sụp đổ ngữ nghĩa từ câu đầu tiên. Lưu vết `paper_ids` bị ảnh hưởng trong audit log với cố định `seed=42`.
3. **`quality.py`**: Triển khai **Great Expectations 1.x Ephemeral Context** với 7 bộ quy tắc (Row count 1-100, Null constraint cho paper_id/title/summary, Unique paper_id, Title length >= 8, Summary length >= 10). Tính tỉ lệ bài quá hạn (>180 ngày) trong `build_freshness_report`.
4. **`reporting.py`**: Xây dựng hàm render Markdown sinh tự động các câu phân tích chênh lệch metric ($Baseline - Corrupted$) và trích xuất đúng tên Expectation bị FAIL.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | List[PaperRecord] thô từ Crossref / Clean DataFrame |
| Output                         | Clean DataFrame, Corrupted DataFrame, Quality Reports JSON, Comparison Report MD |
| Module phụ thuộc             | `src/core/config.py`, `src/core/utils.py`, `src/ingestion/crossref.py` |
| Module sử dụng output        | `src/retrieval/index.py` (nhận Clean DF), `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Xử lý dữ liệu rác JATS XML, loại bỏ null summary/title, phát hiện trùng lặp paper_id và dữ liệu quá hạn |

### Cách xác minh

```bash
$env:PYTHONIOENCODING="utf-8"
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Baseline Hit Rate = 1.0000; Corrupted Hit Rate suy giảm rõ rệt (< 0.8000) & Quality Gate FAIL; Repaired phục hồi về 1.0000 & Quality Gate PASS.
- **Kết quả thực tế:** 
  - Baseline: `retrieval_hit_rate = 1.0000`, `mean_token_f1 = 1.0000`, Quality Gate = `PASS`
  - Corrupted: `retrieval_hit_rate = 0.7000`, `mean_token_f1 = 0.8223`, Quality Gate = `FAIL` (phát hiện lỗi unique paper_id, title length, summary length)
  - Repaired: `retrieval_hit_rate = 1.0000`, `mean_token_f1 = 1.0000`, Quality Gate = `PASS`
- **Artifact/log:** `data/reports/corruption_report.md`, `data/quality/corrupted_quality_report.json`, `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Phương pháp làm bẩn dữ liệu ban đầu (chèn noise 1 cụm ở giữa summary và dùng cố định 3 dòng) khiến chỉ số Hit Rate hầu như không suy giảm (1.0 -> 0.9), không thể hiện được tác động của Silent Failure.
- **Các phương án đã cân nhắc:** 
  1. Thay đổi seed ngẫu nhiên để chọn số liệu đẹp.
  2. Sửa thủ công test set để trùng các câu bị làm bẩn.
  3. Tăng cường độ làm bẩn theo tỉ lệ `CORRUPTION_RATE = 0.35` và chèn ký tự rác rải rác toàn bộ summary (sau mỗi 3-4 từ).
- **Phương án đã chọn:** Phương án 3 (Tăng cường độ theo tỉ lệ và rải rác noise).
- **Lý do:** Phương án 1 và 2 vi phạm tính minh bạch dữ liệu và tính lặp lại (reproducibility). Phương án 3 mô phỏng chính xác sự cố lỗi mã hóa (Encoding Corruption) thực tế, làm hỏng cấu trúc ngữ nghĩa ngay từ những câu đầu tiên.
- **Bằng chứng quyết định phù hợp:** Hit Rate sụp đổ từ 1.0000 xuống 0.7000 (-30%), Token F1 giảm từ 1.0000 xuống 0.8223, minh chứng rõ rệt Silent Failure đúng yêu cầu Rubric #8.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi đọc dữ liệu lỗi từ CSV (`pd.read_csv`), các ô summary rỗng bị biến thành `NaN` (null). Do `ExpectColumnValueLengthsToBeBetween` trong Great Expectations mặc định bỏ qua giá trị null, các dòng blank summary đã lọt lưới Quality Gate (báo PASS sai).
- **Lệnh hoặc bước tái hiện:** `run_data_quality_checks(pd.read_csv("papers_clean_corrupted.csv"), settings, "corrupted")`.
- **Nguyên nhân gốc:** Hàm `run_data_quality_checks` trước đó nhận tham số linh hoạt cả `str/Path` nên đã gọi `pd.read_csv`, làm biến đổi kiểu dữ liệu string rỗng `""` thành `NaN`.
- **Cách xử lý:** 
  1. Đổi chữ ký hàm `run_data_quality_checks` về chuẩn chỉ nhận `df: pd.DataFrame`.
  2. Thêm expectation trực tiếp `ExpectColumnValuesToNotBeNull(column="summary")` và `ExpectColumnValueLengthsToBeBetween(column="title", min_value=8)` vào suite.
- **Cách xác minh sau khi sửa:** Chạy kiểm thử trên `corrupted_df`, Cổng Quality Gate báo `success = False` và đánh dấu FAIL chính xác ở `expect_column_values_to_be_unique`, `summary length` và `title length`.
- **Bài học kỹ thuật:** Luôn giữ đúng contract kiểu dữ liệu (DataFrame) giữa các module và kiểm tra kỹ hành vi xử lý null của các thư viện Data Quality.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** Raw JSON từ Crossref API -> `cleaning.py` làm sạch XML, chuẩn hóa schema, tạo `text_for_embedding` 5 phần -> ChromaDB Vector Store mã hóa văn bản thành Vector Embeddings và lưu trữ cùng metadata (`paper_id`, `title`, `published`).
2. **Evaluation set và ground-truth document IDs:** Tập test set chứa danh sách câu hỏi kèm `ground_truth` và `gold_paper_ids`. Hệ thống đo `retrieval_hit_rate` bằng cách kiểm tra xem bài báo chứa câu trả lời đúng có nằm trong Top-K kết quả do Vector DB truy vấn ra hay không.
3. **Quality checks vs freshness monitoring:** Quality checks (GX 1.x) kiểm tra tính đúng đắn của cấu trúc và giá trị dữ liệu (Null, Unique, Length), trong khi Freshness Monitoring đo lường độ tươi mới của dữ liệu theo thời gian thực tế so với ngưỡng SLA (180 ngày).
4. **Vì sao dùng cùng test set:** Để đảm bảo tính công bằng và nhất quán tuyệt đối khi so sánh hiệu năng RAG giữa 3 trạng thái (Baseline, Corrupted, Repaired).
5. **Repair thành công dựa trên:** Artifact `repaired_clean.csv`, `repaired_quality_report.json` (`success=True`), `repaired_freshness_report.json` (`is_fresh=True`) và chỉ số `retrieval_hit_rate` phục hồi về mức 1.0000 (bằng Baseline).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.7000 |   1.0000 | Suy giảm 30% khi bị corruption và phục hồi 100% sau repair |
| `mean_token_f1`      |   1.0000 |    0.8223 |   1.0000 | Giảm đáng kể do câu trả lời bị dính noise rác, phục hồi hoàn toàn sau repair |
| `judge_accuracy`     |   1.0000 |    0.8000 |   1.0000 | LLM Judge đánh giá chính xác sự suy giảm chất lượng câu trả lời |
| `mean_judge_score`   |   5.0000 |    4.0000 |   5.0000 | Điểm đánh giá trung bình giảm từ 5/5 xuống 4/5 khi dính dữ liệu bẩn |
| Quality checks         |     PASS |      FAIL |     PASS | Cổng GX 1.x bắt chính xác 3 loại lỗi dữ liệu bẩn |
| Freshness status       |     PASS |      FAIL |     PASS | Phát hiện chính xác dữ liệu vi phạm SLA quá 180 ngày |

### Kết luận từ số liệu

1. **Data corruption** -> Quality Gate báo **FAIL** (lỗi unique paper_id, summary/title length) & Freshness SLA báo **FAIL** (`is_fresh=False`) -> Agent `retrieval_hit_rate` sụp đổ từ 1.0000 xuống 0.7000.
2. **Repair action** (re-ingest từ raw snapshot) -> Quality Gate & Freshness SLA phục hồi **PASS** -> Agent `retrieval_hit_rate` và `mean_token_f1` phục hồi hoàn toàn về 1.0000.

- **Corruption ảnh hưởng rõ nhất:** `inject_noise` (chèn rác rải rác toàn bộ summary) và `truncate_title`, vì chúng trực tiếp phá hỏng không gian Vector Embedding và ngữ nghĩa câu từ khiến ChromaDB truy vấn sai bài báo.
- **Kết quả khác với kỳ vọng:** Lần đầu chạy test chỉ số không giảm do noise chỉ chèn ở giữa. Sau khi refactor chèn noise rải rác sau mỗi 3-4 từ, chỉ số đã sụp đổ đúng như kỳ vọng lý thuyết.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Xây dựng pipeline chuẩn hóa schema (`text_for_embedding`) là tiền đề bắt buộc để RAG agent đạt hiệu năng tối ưu.
2. **Về Data Quality/Observability:** Hệ thống RAG rất dễ bị Silent Failure; việc triển khai Quality Gate tự động (Great Expectations) giúp phát hiện sự cố dữ liệu trước khi ảnh hưởng tới người dùng.
3. **Về ảnh hưởng của Data đến Agent:** Chất lượng dữ liệu quyết định trực tiếp tới khả năng Retrieval và phản hồi của LLM (Garbage in, Garbage out).

### Nếu có thêm thời gian

Thêm cơ chế **Automated Anomaly Detection** dựa trên phân phối độ dài văn bản và tự động trigger luồng Re-indexing ngay khi Quality Gate báo FAIL mà không cần can thiệp thủ công.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Trung Kiên
**Ngày xác nhận:** 2026-09-26
