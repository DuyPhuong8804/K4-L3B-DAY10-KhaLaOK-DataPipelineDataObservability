# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Thị Thu Hiền |
| MSSV | 2A202602737 |
| Khóa/Lớp | K4 — L3B |
| Tên nhóm | KhaLaOK |
| Vai trò chính | Evaluation set & Retrieval (Người C) |
| Repository | https://github.com/DuyPhuong8804/K4-L3B-DAY10-KhaLaOK-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Benchmark evaluation set | `src/evaluation/testset.py`: `build_test_set` | DataFrame sạch có `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published` | `data/eval/test_set.json` gồm 10 câu hỏi và ground truth | Hoàn thành |
| Vector index manifest | `src/retrieval/index.py`: `LocalEmbeddingIndex.build`, `LocalEmbeddingIndex.load` | Clean/corrupted/repaired DataFrame, `Settings`, manifest path | Ba collection Chroma và manifest có `persist_path = data/chroma` | Hoàn thành |
| Evaluation tests | `tests/test_evaluation.py` | Test fixtures và fake embedding/Chroma client | 7 pytest cho test set, Token F1, exact-title QA và manifest path | Hoàn thành |
| Khởi động module nhẹ hơn | `src/evaluation/__init__.py`, `src/retrieval/__init__.py`, import trong `metrics.py`/`index.py` | Yêu cầu import từng chức năng | Lazy import, tránh tải Ragas/SentenceTransformer khi chưa dùng | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Xác minh contract của clean DataFrame | Người B — `src/ingestion/cleaning.py` | Test set nhận đúng 24 dòng và các cột helper cần thiết |
| Kiểm tra tích hợp Phase 1 | Người A — `src/pipelines/phase1.py` | `python script/run_phase1.py` exit code 0; index đủ 24 documents; test set đủ 10 câu |
| Đối chiếu kết quả ba trạng thái | Cả nhóm | Dùng cùng `test_set.json` để so sánh Baseline/Corrupted/Repaired công bằng |

Các commit chính của tôi là `e4fc9cd` (test set, retrieval/evaluation và tests), `1efed84` (manifest path tương đối và loại generated artifacts khỏi commit); nội dung tương ứng đã được merge vào `main` ở `cc22afe` và `0c14e43`.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Sinh benchmark xác định | `build_test_set`, `data/eval/test_set.json` | 10 câu: 3 summary, 3 authors, 2 date, 2 categories | Lệnh nghiệm thu CP2 in `Sinh được 10 câu hỏi test` |
| Đảm bảo test set đại diện | `_select_representative_rows` | Chọn rải đều trên corpus đã sort theo `paper_id`, không chỉ lấy 10 dòng đầu | Kiểm tra `ground_truth_doc_ids` trong `test_set.json` |
| Build và persist vector index | `LocalEmbeddingIndex`, `data/chroma/` | Ba collection `papers-baseline`, `papers-corrupted`, `papers-repaired`; baseline/repaired 24 docs, corrupted 27 docs | Chạy hai pipeline và kiểm tra Chroma collection count |
| Loại đường dẫn máy cá nhân | `data/embeddings/*.json` | Manifest ghi `data/chroma`, không chứa `C:\Users\...` | Test `test_embedding_manifest_stores_relative_chroma_path` |
| Đo chất lượng RAG | `evaluation/metrics.py`, `data/results/*_metrics.json` | Baseline Hit Rate/F1 = 1.0/1.0; Corrupted = 0.7/0.8223; Repaired = 1.0/1.0 | Đối chiếu ba metrics JSON |
| Kiểm thử tự động | `tests/test_evaluation.py` | 7/7 test pass | `python -m pytest -q tests` |

Artifact tiêu biểu của phần việc là `data/eval/test_set.json`. Bộ benchmark này giữ nguyên giữa ba trạng thái dữ liệu và liên kết mỗi câu hỏi với `ground_truth_doc_ids`, nhờ đó mức giảm retrieval không bị che khuất bởi việc thay đổi câu hỏi giữa các lần chạy.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần một bộ đánh giá nhỏ nhưng tái lập được để đo cùng lúc hai việc: vector search có lấy đúng bài báo hay không, và câu trả lời trích từ metadata có khớp ground truth hay không. Ngoài ra, ChromaDB phải persist được trên máy khác mà manifest không chứa đường dẫn tuyệt đối của máy phát triển.

### Cách triển khai

1. `build_test_set` kiểm tra đủ sáu cột bắt buộc, loại `paper_id` trùng và bỏ record thiếu dữ liệu cần làm ground truth.
2. Dữ liệu được sort ổn định theo `paper_id`, sau đó chọn 10 vị trí rải đều trên toàn corpus. Lịch loại câu hỏi cố định gồm 3 `summary`, 3 `authors`, 2 `date`, 2 `categories`.
3. Tiêu đề bài báo được đặt trong dấu nháy đơn. `qa.py` nhận diện tiêu đề này để ưu tiên exact lookup, sau đó kết hợp semantic search top-k. Các cụm `Who authored`, `When was`, `What categories` giúp bộ trích xuất chọn đúng metadata field.
4. Mỗi sample có `id`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids`. Summary ground truth dùng câu đầu tiên để khớp contract của QA; ngày được chuẩn hóa ISO `YYYY-MM-DD`.
5. `LocalEmbeddingIndex.build` tạo embeddings bằng `all-MiniLM-L6-v2`, lưu vector và metadata vào collection tương ứng. Manifest chỉ ghi `data/chroma`; `load` ghép đường dẫn này với `settings.paths.project_dir`. Payload cũ chứa absolute path vẫn tương thích vì `Path / absolute_path` trả lại absolute path.
6. Evaluation đánh dấu `retrieval_hit=True` nếu một `ground_truth_doc_id` nằm trong top-k. Token F1 đo overlap token giữa prediction và ground truth. Cùng một `test_set.json` được tái sử dụng cho cả ba collection.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Clean DataFrame có `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`, `text_for_embedding` và URL metadata |
| Output | `test_set.json`; manifest embeddings; collection Chroma; `baseline/corrupted/repaired_metrics.json` và answers JSON |
| Module phụ thuộc | `ingestion.cleaning`, `core.config`, `core.utils`, `retrieval.embeddings`, ChromaDB |
| Module sử dụng output | `pipelines.phase1`, `pipelines.corruption_flow`, `evaluation.metrics`, báo cáo Phase 1/corruption |
| Điều kiện lỗi cần xử lý | Thiếu cột; dưới 10 paper hoàn chỉnh; record trùng/rỗng; output path chưa có thư mục; manifest cũ chứa absolute path |

### Cách xác minh

```powershell
$env:PYTHONIOENCODING="utf-8"
python -m pytest -q tests
python script/run_phase1.py
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"
```

- **Kết quả mong đợi:** 7 tests pass; Phase 1 exit code 0; Chroma index 24 documents; CP2 sinh 10 câu; manifest ghi `data/chroma`.
- **Kết quả thực tế:** `7 passed`; Phase 1 exit code 0; `retrieval_hit_rate=1.0000`, `mean_token_f1=1.0000`; CP2 in đúng `Tín hiệu hoàn thành: Sinh được 10 câu hỏi test`.
- **Artifact/log:** `data/eval/test_set.json`, `data/embeddings/papers_embeddings.json`, `data/results/baseline_metrics.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Nếu test set được chọn ngẫu nhiên hoặc tạo lại riêng cho từng trạng thái thì kết quả Baseline/Corrupted/Repaired không còn so sánh trực tiếp được.
- **Các phương án đã cân nhắc:** (a) lấy ngẫu nhiên 10 paper mỗi lần; (b) lấy 10 dòng đầu; (c) sort theo khóa ổn định, chọn rải đều và lưu một test set dùng chung.
- **Phương án đã chọn:** (c).
- **Lý do:** Cách này deterministic, phủ được nhiều vị trí trong corpus và không để thay đổi thứ tự DataFrame làm thay đổi benchmark. Dùng cùng ground truth giúp mức giảm metric phản ánh thay đổi dữ liệu/index thay vì thay đổi đề kiểm tra.
- **Bằng chứng quyết định phù hợp:** Baseline và Repaired cùng đạt Hit Rate/F1 `1.0/1.0`, trong khi chỉ Corrupted giảm còn `0.7/0.8223` trên chính bộ 10 câu đó.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `papers_embeddings.json` chứa `"persist_path": "C:\\Users\\Admin\\...\\data\\chroma"`, khiến manifest phụ thuộc máy cá nhân và có nguy cơ bị trừ điểm portability.
- **Lệnh hoặc bước tái hiện:** chạy Phase 1 rồi mở `data/embeddings/papers_embeddings.json`.
- **Nguyên nhân gốc:** `LocalEmbeddingIndex.build` serialize trực tiếp `str(settings.paths.chroma_dir)`, trong khi `chroma_dir` đã được resolve thành absolute path.
- **Cách xử lý:** khi ghi manifest, dùng `persist_path.relative_to(settings.paths.project_dir).as_posix()`; khi load, dùng `settings.paths.project_dir / payload["persist_path"]`.
- **Cách xác minh sau khi sửa:** test dùng fake embeddings và fake `PersistentClient` xác nhận manifest bằng `data/chroma`, trong khi client vẫn nhận absolute path; Phase 1 chạy lại exit 0 và tìm kiếm bình thường.
- **Điều học được:** artifact trao đổi giữa môi trường phải lưu đường dẫn portable; absolute path chỉ nên tồn tại trong runtime object, không nên ghi vào manifest được commit/chia sẻ.

## 7. Hiểu biết về luồng end-to-end

1. Crossref API hoặc snapshot cung cấp raw metadata. Cleaning gỡ JATS, chuẩn hóa tác giả/category/ngày, tính `age_days` và ghép `text_for_embedding` năm phần. Quality Gate kiểm tra dữ liệu trước khi MiniLM mã hóa văn bản thành vector và ChromaDB lưu vector cùng metadata.
2. Mỗi evaluation sample có ground-truth answer và `ground_truth_doc_ids`. Hit Rate kiểm tra bài đúng có nằm trong top-k hay không; Token F1 so sánh nội dung câu trả lời với ground truth; judge bổ sung đánh giá mức đúng về ngữ nghĩa.
3. Quality checks đo tính hợp lệ của cấu trúc/nội dung như null, unique và độ dài. Freshness monitoring đo tính kịp thời theo `age_days > 180` và tỷ lệ stale tối đa 25%. Dữ liệu có thể đúng schema nhưng vẫn quá cũ.
4. Dùng cùng test set giúp kiểm soát biến số: chỉ dataset/index thay đổi. Nếu đổi câu hỏi thì không thể kết luận metric giảm là do corruption.
5. Repair thành công khi clean repaired trở về 24 dòng, Quality Gate và Freshness đều PASS, collection repaired được dựng lại từ raw snapshot, và metrics trở về bằng baseline. Artifact hiện tại cho thấy Hit Rate/F1 trở về `1.0/1.0`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.7000 | 1.0000 | Ba trong mười câu mất ground-truth document khỏi top-k khi dữ liệu bị bẩn |
| `mean_token_f1` | 1.0000 | 0.8223 | 1.0000 | Noise/mất metadata làm chất lượng câu trả lời giảm, repair phục hồi hoàn toàn |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | Judge fallback ghi nhận hai câu trả lời sai đáng kể ở corrupted state |
| `mean_judge_score` | 5.0000 | 4.2000 | 5.0000 | Điểm trung bình giảm 0.8 rồi trở lại mức baseline |
| Quality checks | PASS | FAIL | PASS | Corrupted vi phạm unique `paper_id`, độ dài title và summary |
| Freshness status | PASS | FAIL | PASS | Stale ratio tăng từ 0.0417 lên 0.2963, vượt SLA 0.25 |

### Kết luận từ số liệu

1. Sáu corruption làm mất dòng, cắt title, xóa/chèn noise summary, làm cũ ngày và tạo duplicate → Quality Gate/Freshness cùng FAIL → Hit Rate giảm `0.3`, Token F1 giảm khoảng `0.1777`.
2. Repair dựng lại từ raw snapshot → Quality Gate/Freshness PASS → Hit Rate, Token F1 và judge metrics trở về đúng baseline.

Ảnh hưởng rõ nhất xuất hiện ở `q03`, `q04`, `q08`: cả ba có `retrieval_hit=False`, làm Hit Rate còn 0.7. Trong đó `q03` có Token F1 bằng 0 và `q08` chỉ còn khoảng 0.2857. `q01` và `q09` vẫn retrieval đúng nhưng Token F1 giảm nhẹ còn khoảng 0.9677/0.9697 do summary bị chèn noise. `q04` là trường hợp đáng chú ý: retrieval miss nhưng Token F1 vẫn bằng 1 vì tài liệu khác được lấy lên có cùng category; điều này cho thấy cần đọc cả retrieval metric và answer metric, không dùng một chỉ số riêng lẻ.

Kết quả khác kỳ vọng ban đầu là một câu trả lời có thể đúng dù retrieval sai (`q04`). Sau khi đối chiếu `corrupted_answers.json`, nguyên nhân là category ground truth không đủ phân biệt giữa các paper. Vì vậy `ground_truth_doc_ids` và Hit Rate vẫn cần thiết để phát hiện lỗi retrieval bị Token F1 che khuất.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Một benchmark tốt phải deterministic, có data contract rõ ràng và được cố định trước khi so sánh các trạng thái pipeline.
2. Retrieval quality và answer quality là hai lớp khác nhau; câu trả lời có thể tình cờ đúng từ tài liệu sai nên phải đo cả Hit Rate lẫn Token F1/judge.
3. Tính portable của artifact cũng là một phần của data engineering: manifest không được phụ thuộc đường dẫn máy người tạo.

### Nếu có thêm thời gian

Tôi sẽ bổ sung metric theo từng `question_type` và kiểm tra độ phân biệt của ground truth. Ví dụ category question có thể dùng kết hợp category + paper title hoặc đánh giá retrieval bắt buộc, tránh trường hợp tài liệu sai nhưng category trùng vẫn đạt Token F1 cao. Cải thiện sẽ được đo bằng bảng Hit Rate/F1 theo bốn nhóm câu hỏi trên cùng corruption seed.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Thị Thu Hiền  
**Ngày xác nhận:** 2026-09-26
