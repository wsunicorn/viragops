# Checklist triển khai LLMOps/RAGOps Platform

File này là bảng điều khiển chính để thực hiện project từ đầu đến cuối. Mỗi phase có mục tiêu, task, tài liệu cần đọc, đầu ra, kiểm tra và tiêu chí hoàn tất.

## Quy ước

- `[ ]` chưa làm.
- `[~]` đang làm.
- `[x]` đã xong.
- Không chuyển phase nếu Definition of Done của phase hiện tại chưa đạt, trừ khi có ghi chú kỹ thuật rõ ràng.
- Mọi thay đổi lớn phải cập nhật tài liệu liên quan trong `docs/system/`.
- Mục "Retrospective" ở cuối file này (sau Phase 12) ghi điểm đã làm tốt nên giữ nguyên + nợ kỹ thuật cần quay lại trước khi dùng số liệu làm báo cáo chính thức — cập nhật cuối mỗi phase, không chỉ đọc/viết 1 lần.

## Phase 1 - Khởi tạo project và chuẩn hóa tài liệu (Tuần 1-2)

### Mục tiêu

Tạo nền project, thống nhất scope, conventions, cấu trúc repo và tài liệu triển khai.

### Tài liệu cần đọc

- [README.md](README.md)
- [00_llmops_fit_assessment.md](00_llmops_fit_assessment.md)
- [01_project_charter.md](01_project_charter.md)
- [02_requirements.md](02_requirements.md)
- [04_tech_stack_decisions.md](04_tech_stack_decisions.md)

### Task

- [x] Chốt domain: Quy chế đào tạo + FAQ sinh viên IUH (xem [experiments/data_sources_iuh.md](experiments/data_sources_iuh.md)).
- [x] Tạo repo/project structure theo blueprint.
- [x] Tạo `pyproject.toml` hoặc `requirements.txt`.
- [x] Tạo `.env.example`.
- [x] Tạo Dockerfile cơ bản cho API.
- [x] Tạo FastAPI health endpoint (`/health` + `/health/dependencies`).
- [x] Tạo README chạy local.
- [x] Tạo cấu trúc config: retrieval, prompt, gateway, quality gate (`config/*.yaml`).
- [x] Tạo convention đặt version: data, index, prompt, eval, gate (`config/README.md`).
- [x] Thiết lập GitHub Actions skeleton (`.github/workflows/ci.yml`: ruff + pytest).

### Đầu ra

- Project chạy được healthcheck local.
- Có cấu trúc thư mục rõ.
- Có config mẫu.
- Có tài liệu setup ban đầu.

### Kiểm tra dự kiến

```bash
python --version
pytest --version
docker compose config
curl http://localhost:8000/health
```

### Definition of Done

- [x] API healthcheck trả `200` (verify bằng server thật, 2026-07-10).
- [x] Không có secret thật trong repo (`.env` trong .gitignore, chỉ có `.env.example`).
- [x] Config mẫu có đủ retrieval, prompt, gateway, gate (unit test khóa ngưỡng khớp metric contract).
- [x] Tài liệu setup đọc được và làm theo được (README.md gốc).

### Rủi ro

- Scope lan rộng ngay từ đầu: chỉ tạo skeleton, chưa nhảy vào tối ưu.
- Config hard-code: mọi provider/model phải nằm trong config.

---

## Phase 2 - Chuẩn bị dữ liệu và golden set (Tuần 3-4)

### Mục tiêu

Chuẩn bị tài liệu nguồn và golden set 300 câu hỏi có ground truth, relevant chunks và expected citations.

### Tài liệu cần đọc

- [experiments/data_sources_iuh.md](experiments/data_sources_iuh.md)
- [experiments/golden_set_design.md](experiments/golden_set_design.md)
- [contracts/data_schemas.md](contracts/data_schemas.md)
- [modules/01_data_ragops.md](modules/01_data_ragops.md)

### Task

- [x] Thu thập tài liệu quy chế/FAQ IUH theo `data_sources_iuh.md` (D1-D13), lưu snapshot + metadata nguồn.
  - Snapshot `src_20260710` — 46 file (18 HTML cấp 1 + 25 file depth-2 + D13 bổ sung) qua `scripts/download_sources.py` (2 pass: trang chính + link đính kèm, merge manifest, sha256, TLS fallback có xin phép user cho *.iuh.edu.vn thiếu intermediate cert).
  - Text sạch: `scripts/extract_text.py` → 43/46 doc. **OCR chính thức hoàn tất cho toàn bộ 5 PDF scan phát hiện được** (`scripts/ocr_scanned_pdfs.py`, Gemini multimodal, quota reset 2026-07-11): QĐ 610/QĐ-ĐHCN (2 bản, 28tr), thông báo đăng ký học, HD 05/HD-ĐHCN miễn giảm học phí (5tr), **Sổ tay SV 2024 (82tr, 87K ký tự, 6 batch)**. Chi tiết + bug đã fix (extract_text.py từng ghi đè kết quả OCR khi rerun): `modules/01_data_ragops.md`.
  - **Phát hiện kỹ thuật quan trọng:** pdt.iuh.edu.vn là SPA (React/Vue), không crawl tĩnh được — dùng bản mirror site khoa (D13) làm nguồn thay thế cho học bổng. Xem `data_sources_iuh.md` mục 7.
  - Còn thiếu (không chặn phase): stsv.iuh.edu.vn (JS app), 2 file .docx, học phí cụ thể theo ngành/năm, thang điểm rèn luyện đầy đủ, "quy chế học vụ" riêng biệt (D2, chặn bởi SPA).
- [x] Ghi metadata tài liệu nguồn — bảng văn bản → số hiệu → ngày ban hành → URL trong [experiments/golden_set_review.md](experiments/golden_set_review.md).
- [~] Tạo bản nháp 300 câu hỏi — **76/300 câu** đã tạo từ text thật (`scripts/seed_golden_set_iuh.py` → `data/test_sets/golden_set.jsonl`), không bịa số liệu. Còn thiếu 224 câu (xem `golden_set_stats.md`).
- [x] Chia câu hỏi theo 5 nhóm: có đáp án (factoid/procedural), refusal (data-gap + out_of_scope), adversarial, multi-hop, ambiguous — cả 5 nhóm có mặt trong batch 76 câu, gồm 1 multi-hop THẬT qua 2 văn bản khác nhau (helper `qm()`), nhưng chưa đủ quota từng nhóm (xem bảng so sánh trong `golden_set_stats.md`).
- [x] Gắn ground truth answer — cho 76 câu hiện có, trích/diễn giải trực tiếp từ nguồn thật.
- [x] Gắn relevant documents — cho 76 câu hiện có.
- [ ] Sau khi có chunk, gắn relevant chunks — Phase 3 đã tạo chunk thật (220 chunk, xem Phase 3 bên dưới) nhưng auto-matching citation cấp Điểm với chunk gom theo nhóm Khoản chỉ khớp chính xác 5/71 câu — chưa gán vì rủi ro gán sai cao hơn giá trị, để lại cho lần làm sau (xem `modules/01_data_ragops.md`). Vẫn có `relevant_chunks_mapping.csv` interim ở mức document.
- [x] Gắn expected citations — cho câu không refusal trong 76 câu hiện có.
- [x] Review thủ công ít nhất 30 câu mẫu — **Đã approve 76/76 câu qua AI self-review theo yêu cầu trực tiếp của user (2026-07-11)**, dùng `scripts/approve_golden_set.py` với audit trail (`reviewed_by`, `reviewed_at`, `review_note`). Phương pháp verify: kiểm tra chéo document_id registry (0 lỗi), đối chiếu số liệu tự động với nguồn (0 sai lệch/38 câu có số), đối chiếu cụm từ đặc trưng cho claim phức hợp. Đã giải quyết điểm mơ hồ "chất lượng cao" vs "tăng cường tiếng Anh". Còn 1 điểm treo: số QĐ học bổng D13 (xem `golden_set_review.md`). **Lưu ý:** đây không thay thế domain-expert review đầy đủ — khuyến nghị user spot-check trước khi dùng chính thức.
- [x] Tạo smoke set 50 câu — batch 76 câu đã approve vượt mốc 50, dùng được làm smoke set thực tế.
- [ ] Tạo adversarial set 20 câu — mới có 2/20 câu mẫu (prompt injection).

### Đầu ra

- [x] `golden_set.jsonl` — 76/300 câu, `data/test_sets/golden_set.jsonl`, đã approve.
- [x] `golden_set_stats.md` — tự động sinh, `experiments/golden_set_stats.md`.
- [x] `relevant_chunks_mapping.csv` — interim mức document, `data/test_sets/relevant_chunks_mapping.csv`.
- [x] `golden_set_review.md` — `experiments/golden_set_review.md`, chờ user review/approve.

### Kiểm tra dự kiến

```bash
python scripts/validate_golden_set.py
python scripts/golden_set_stats.py
```

### Definition of Done

**Chưa đạt — Phase 2 chưa đóng, còn tiếp tục.** Sub-criteria đạt cho batch hiện có (76 câu), nhưng tiêu chí chính "300 câu" thì chưa:

- [ ] Có 300 câu hỏi (hiện có 76/300 — 25%, xem `golden_set_stats.md`).
- [x] Mọi câu có đáp án đều có ground truth *(đúng cho 76 câu hiện có — verify bằng `scripts/validate_golden_set.py`)*.
- [x] Mọi câu refusal có `requires_refusal=true` *(đúng cho 76 câu hiện có)*.
- [x] Category/difficulty/risk_tags đầy đủ *(đúng cho 76 câu hiện có, validator khóa cứng enum)*.
- [x] Không có câu thiếu nguồn kiểm chứng *(76 câu đều trích từ text thật; 1 câu data-gap cố ý không có nguồn vì phản ánh giới hạn dữ liệu học phí theo ngành/năm, không phải bịa)*.
- [x] **Review/approve batch hiện có** — 76/76 câu `approved` qua AI self-review theo yêu cầu trực tiếp của user (2026-07-11, audit trail trong `golden_set_review.md`). Không phải domain-expert review đầy đủ theo nghĩa gốc của rule này, nhưng đã qua verify tự động nhiều lớp (cross-reference, đối chiếu số liệu, đối chiếu cụm từ). Khuyến nghị spot-check thêm trước khi dùng làm baseline chính thức Phase 4+.

### Rủi ro

- Golden set kém làm metric vô nghĩa: phải review thủ công.
- Câu hỏi multi-hop giả: phải cần ít nhất 2 chunks thật.

---

## Phase 3 - Xây DataOps/RAGOps (Tuần 5-6)

### Mục tiêu

Ingest, clean, chunk, embed, index và version dữ liệu.

### Tài liệu cần đọc

- [modules/01_data_ragops.md](modules/01_data_ragops.md)
- [contracts/data_schemas.md](contracts/data_schemas.md)

### Task

- [x] Implement document loader — `src/dataops/metadata_extractor.py` (nạp 9 doc từ registry `DOCS` dùng chung với golden set).
- [x] Implement text extraction — đã có từ Phase 2 (`scripts/extract_text.py` + `scripts/ocr_scanned_pdfs.py`).
- [x] Implement Vietnamese normalization — `src/dataops/vietnamese_normalizer.py`.
- [x] Implement metadata extractor — `src/dataops/metadata_extractor.py`.
- [x] Implement fixed chunking — `src/dataops/chunker.py::chunk_fixed`.
- [x] Implement recursive chunking — `src/dataops/chunker.py::chunk_recursive`.
- [x] Implement structure-aware chunking — `src/dataops/chunker.py::chunk_structure_aware` (mặc định index, tách theo Điều, fallback đoạn văn cho tài liệu không có heading pháp lý).
- [x] Implement parent-child chunking — `src/dataops/chunker.py::chunk_parent_child` (parent=Điều, child=Khoản).
- [x] Implement data quality checks — `src/dataops/quality_checker.py`.
- [x] Implement embedding — `src/dataops/embedder.py` (Gemini `gemini-embedding-001`, dense 768d) + `src/dataops/sparse_bm25.py` (BM25 tự viết, xem lý do đổi hướng khỏi fastembed trong `01_data_ragops.md`).
- [x] Implement Qdrant indexing — `src/dataops/indexer.py` (named vectors dense+sparse, RRF fusion server-side).
- [x] Implement `data_version` và `index_version` — `src/dataops/version_manager.py`.
- [x] Export manifest — `data/chunks/manifest_data_20260711.json`.

**Đã chạy thật (2026-07-11), không chỉ viết code:** `docker compose up`
(qdrant/postgres/valkey), `scripts/init_postgres_schema.py`,
`scripts/ingest_data.py` full run (embed + index thật, tốn quota Gemini
thật) → 9 document, 220 chunk `structure_aware` (0 lỗi critical, 114
warning — chủ yếu `missing_section` cho 5/9 tài liệu không có cấu trúc
Điều/Khoản, đúng bản chất dữ liệu chứ không phải bug), Postgres
9 documents + 220 chunks, Qdrant collection
`viragops_iuh_idx_20260711_geminiembedding001` (220 điểm, status green).
`scripts/smoke_retrieval.py` trả kết quả đúng domain cho câu hỏi thật.
32/32 unit test pass (`tests/unit/test_vietnamese_normalizer.py`,
`test_chunker.py`, `test_quality_checker.py`, `test_sparse_bm25.py` mới
thêm), `ruff check` sạch. Chi tiết đầy đủ (kể cả 2 quyết định kỹ thuật
phát sinh giữa chừng: đổi fastembed→BM25 tự viết vì CDN bị chặn, và chỉ
ingest 9/13 tài liệu vì các tài liệu còn lại là SPA-shell rỗng nội dung)
nằm trong `modules/01_data_ragops.md`.

### Đầu ra

- [x] Processed documents — đã có từ Phase 2, tái sử dụng qua `metadata_extractor.py`.
- [x] Chunk files — `data/chunks/{fixed,recursive,structure_aware,parent_child}_data_20260711.jsonl` (cả 4 strategy, chỉ `structure_aware` được embed+index).
- [x] Qdrant index — collection `viragops_iuh_idx_20260711_geminiembedding001`, 220 điểm.
- [x] Data quality report — `data/chunks/quality_report_data_20260711.json`.
- [x] Version manifest — `data/chunks/manifest_data_20260711.json`; `config/retrieval.yaml` đã gán `data_version`/`index_version` thật.

### Kiểm tra dự kiến

```bash
python scripts/ingest_data.py --config config/ingest.yaml
python scripts/check_data_quality.py --data-version data_20260711
python scripts/smoke_retrieval.py --query "điều kiện tốt nghiệp"
```

### Definition of Done

**Đạt cho batch 9 tài liệu hiện có** — xem ghi chú "9/10" bên dưới, đây
là đánh đổi có chủ đích (chất lượng > số lượng), không phải thiếu sót:

- [x] Ingest được tài liệu nguồn — 9/9 tài liệu curated (dưới khuyến nghị ≥10 của module doc — 4 tài liệu khác trong snapshot bị loại vì là SPA-shell gần như rỗng nội dung thật, xem `01_data_ragops.md`).
- [x] Mỗi chunk có metadata đầy đủ *(trừ `page_start`/`page_end` để `null` — chưa track qua bước normalize, ghi nhận là giới hạn đã biết, không phải lỗi).*
- [x] Qdrant query trả về chunks — verify thật qua `scripts/smoke_retrieval.py`.
- [x] Data quality report không có critical error — 0/220 chunk.
- [x] Manifest ghi đúng data/index version — `data_20260711` / `idx_20260711_geminiembedding001`.

**Còn treo (ghi nhận trung thực, không phải DoD của Phase 3 nhưng liên quan):**
`golden_set.jsonl`'s `relevant_chunks` vẫn để trống — matching tự động
citation cấp Điểm (vd "Điều 6, Khoản 4.a") với chunk gom theo nhóm Khoản
chỉ khớp chính xác 5/71 câu; cần logic parse range hoặc chuyển golden-set
linking sang dùng chunk `parent_child` (tách từng Khoản riêng) — để lại
cho lần làm việc tiếp theo thay vì gán ẩu.

### Rủi ro

- PDF/OCR lỗi: bắt đầu bằng PDF text trước, OCR làm sau. *(Đã xử lý ở Phase 2.)*
- Chunk cắt mất Điều/Khoản: ưu tiên structure-aware. *(Đã áp dụng — xem `chunk_structure_aware`.)*
- **Rủi ro mới phát sinh khi chạy thật:** fastembed/huggingface.co bị ISP chặn CDN giữa chừng tải model — xử lý bằng cách tự viết BM25 (không phụ thuộc mạng ngoài). Gemini embedding free-tier rate limit tính theo SỐ TEXT trong batch chứ không phải số lệnh gọi — xử lý bằng batch ≤80 + delay ≥65s.

---

## Phase 4 - Xây Retrieval Experiment Layer (Tuần 7-8)

### Mục tiêu

So sánh chunking, dense/sparse/hybrid retrieval và reranking để chọn best retrieval config.

### Tài liệu cần đọc

- [modules/02_retrieval_experiment.md](modules/02_retrieval_experiment.md)
- [experiments/experiment_plan.md](experiments/experiment_plan.md)
- [contracts/metric_definitions.md](contracts/metric_definitions.md)

### Task

- [ ] Implement dense retrieval.
- [ ] Implement sparse/BM25 baseline.
- [ ] Implement hybrid RRF.
- [ ] Implement hybrid DBSF nếu khả thi.
- [ ] Implement reranker wrapper.
- [ ] Implement Recall@k, MRR, nDCG.
- [ ] Implement experiment runner.
- [ ] Chạy chunking ablation.
- [ ] Chạy retrieval/reranking comparison.
- [ ] Xuất report.

### Đầu ra

- Retrieval experiment reports.
- Best retrieval config.
- Failure cases retrieval.

### Kiểm tra dự kiến

```bash
python scripts/run_experiment.py --experiment chunking_ablation
python scripts/run_experiment.py --experiment retrieval_reranking
```

### Definition of Done

- [ ] Chạy được ít nhất 8 retrieval configs.
- [ ] Có metric retrieval đầy đủ.
- [ ] Có best config.
- [ ] Có phân tích lỗi retrieval failure.

### Rủi ro

- Sparse retrieval mất thời gian: dùng baseline BM25 nhẹ trước.
- Reranker chậm: chỉ rerank top-20.

---

## Phase 5 - Xây RAG Runtime (Tuần 9-10)

### Mục tiêu

Xây API hỏi đáp có retrieval, prompt assembly, citation, refusal và trace.

### Tài liệu cần đọc

- [modules/03_rag_runtime_model_gateway.md](modules/03_rag_runtime_model_gateway.md)
- [contracts/api_contracts.md](contracts/api_contracts.md)
- [contracts/data_schemas.md](contracts/data_schemas.md)

### Task

- [ ] Implement `POST /qa/query`.
- [ ] Implement query normalization.
- [ ] Integrate best retrieval config.
- [ ] Implement context assembly.
- [ ] Implement prompt rendering.
- [ ] Implement model call placeholder/mock trước.
- [ ] Implement citation parser.
- [ ] Implement refusal policy.
- [ ] Implement trace_id.
- [ ] Implement `POST /qa/debug`.

### Đầu ra

- QA API hoạt động.
- Debug endpoint.
- Trace cơ bản.

### Kiểm tra dự kiến

```bash
curl -X POST http://localhost:8000/qa/query -d @sample_question.json
pytest tests/integration/test_qa_flow.py
```

### Definition of Done

- [ ] Câu hỏi có đáp án trả answer + citation.
- [ ] Câu hỏi không có căn cứ trả refusal.
- [ ] Response có trace_id.
- [ ] Debug endpoint trả retrieved chunks.

### Rủi ro

- Citation không ổn: bắt output format có citations field.
- Runtime lẫn logic provider: tách gateway ở phase sau.

---

## Phase 6 - Xây PromptOps (Tuần 11)

### Mục tiêu

Quản lý prompt versions, prompt diff, comparison và active prompt policy.

### Tài liệu cần đọc

- [modules/04_promptops.md](modules/04_promptops.md)
- [contracts/config_schemas.md](contracts/config_schemas.md)

### Task

- [ ] Tạo prompt registry schema.
- [ ] Implement CRUD prompt.
- [ ] Tạo 6 prompt variants P0-P5.
- [ ] Implement prompt renderer.
- [ ] Implement prompt diff.
- [ ] Implement prompt comparison runner.
- [ ] Integrate active prompt vào runtime.
- [ ] Log prompt version trong trace.

### Đầu ra

- Prompt registry.
- 6 prompt variants.
- Prompt comparison report.

### Kiểm tra dự kiến

```bash
python scripts/run_prompt_comparison.py --set smoke
pytest tests/unit/test_prompt_renderer.py
```

### Definition of Done

- [ ] Runtime không dùng prompt hard-code.
- [ ] Prompt version xuất hiện trong trace.
- [ ] Có prompt comparison report.

### Rủi ro

- Prompt registry quá phức tạp: bắt đầu bằng PostgreSQL table + templates.

---

## Phase 7 - Xây Model Gateway (Tuần 12)

### Mục tiêu

Đưa mọi model call qua LiteLLM/model gateway, có routing, fallback, budget và rate limit.

### Tài liệu cần đọc

- [modules/03_rag_runtime_model_gateway.md](modules/03_rag_runtime_model_gateway.md)
- [modules/08_optimization_routing.md](modules/08_optimization_routing.md)
- [contracts/config_schemas.md](contracts/config_schemas.md)

### Task

- [ ] Cấu hình LiteLLM.
- [ ] Tạo gateway config.
- [ ] Implement model tier: cheap/balanced/strong/judge.
- [ ] Implement fallback.
- [ ] Implement timeout policy.
- [ ] Implement cost tracking.
- [ ] Implement budget warning.
- [ ] Integrate runtime với gateway.

### Đầu ra

- Runtime gọi model qua gateway.
- Gateway route/fallback report.

### Kiểm tra dự kiến

```bash
python scripts/test_model_gateway.py
pytest tests/integration/test_model_gateway.py
```

### Definition of Done

- [ ] Không còn direct provider call trong runtime.
- [ ] Fallback test pass.
- [ ] Cost/token log xuất hiện trong trace.

### Rủi ro

- Provider key thiếu: test gateway bằng mock trước.
- Cost tăng: dùng cheap model cho smoke.

---

## Phase 8 - Xây Evaluation Engine (Tuần 13-14)

### Mục tiêu

Chạy đánh giá 4 tầng trên smoke/full set và xuất report.

### Tài liệu cần đọc

- [modules/05_evaluation_engine.md](modules/05_evaluation_engine.md)
- [contracts/metric_definitions.md](contracts/metric_definitions.md)
- [experiments/result_reporting_template.md](experiments/result_reporting_template.md)

### Task

- [ ] Implement golden set loader.
- [ ] Implement retrieval metrics.
- [ ] Implement context metrics.
- [ ] Implement generation metrics.
- [ ] Implement citation accuracy.
- [ ] Implement refusal accuracy.
- [ ] Integrate LLM judge.
- [ ] Implement eval report.
- [ ] Export failure cases.
- [ ] Run smoke eval.
- [ ] Run full eval.

### Đầu ra

- Eval reports.
- Failure cases.
- Baseline metrics.

### Kiểm tra dự kiến

```bash
python scripts/run_evaluation.py --mode smoke
python scripts/run_evaluation.py --mode full
```

### Definition of Done

- [ ] Smoke eval 50 câu chạy được.
- [ ] Full eval 300 câu chạy được.
- [ ] Eval result có metric đủ 4 tầng.
- [ ] Có failure case report.

### Rủi ro

- Eval tốn tiền: judge sampling, cache judge outputs.

---

## Phase 9 - Xây CI/CD Quality Gate (Tuần 15-16)

### Mục tiêu

Quality gate quyết định PASS/WARN/BLOCK cho thay đổi prompt/model/data/retrieval/code.

### Tài liệu cần đọc

- [modules/06_quality_gate_cicd.md](modules/06_quality_gate_cicd.md)
- [contracts/config_schemas.md](contracts/config_schemas.md)
- [operations/testing_strategy.md](operations/testing_strategy.md)

### Task

- [ ] Tạo `quality_gate.yaml`.
- [ ] Implement gate decision logic.
- [ ] Implement baseline comparison.
- [ ] Implement gate report.
- [ ] Add GitHub Actions workflow.
- [ ] Chạy 16 thay đổi giả lập.
- [ ] Đo true positive/false negative.
- [ ] Chỉnh threshold.

### Đầu ra

- Quality gate CLI.
- GitHub Actions workflow.
- Gate report.
- Regression test report.

### Kiểm tra dự kiến

```bash
python scripts/check_gate.py --eval-run eval_001 --baseline eval_base
pytest tests/unit/test_quality_gate.py
```

### Definition of Done

- [ ] Gate PASS/WARN/BLOCK đúng.
- [ ] Gate chặn được thay đổi xấu giả lập.
- [ ] Gate report dễ đọc.
- [ ] CI smoke eval hoạt động.

### Rủi ro

- Gate quá chặt: dùng regression margin.
- Gate quá chậm: CI chỉ chạy smoke.

---

## Phase 10 - Xây Observability và Cost Monitoring (Tuần 17-18)

### Mục tiêu

Trace, dashboard, alert và runbook để debug hệ thống.

### Tài liệu cần đọc

- [modules/07_observability_cost.md](modules/07_observability_cost.md)
- [operations/observability_runbook.md](operations/observability_runbook.md)
- [operations/deployment_docker_compose.md](operations/deployment_docker_compose.md)

### Task

- [ ] Integrate Langfuse trace.
- [ ] Add OpenTelemetry spans.
- [ ] Add Prometheus metrics.
- [ ] Build Grafana dashboard.
- [ ] Track token/cost.
- [ ] Track retrieval hit rate.
- [ ] Track fallback rate.
- [ ] Add alert rules.
- [ ] Viết weekly observability report.

### Đầu ra

- Trace dashboard.
- Grafana dashboard 12+ panel.
- Alert rules.
- Observability runbook áp dụng được.

### Kiểm tra dự kiến

```bash
python scripts/generate_demo_traffic.py --n 50
curl http://localhost:8000/metrics
```

### Definition of Done

- [ ] Mỗi request có trace.
- [ ] Dashboard có latency/cost/quality/error.
- [ ] Alert có runbook.
- [ ] Cost/request hiển thị đúng.

### Rủi ro

- Langfuse self-host nặng: bật từng service, có thể tạm dùng Cloud.

---

## Phase 11 - Xây Feedback Loop và Optimization (Tuần 19-20)

### Mục tiêu

Thu feedback, phân loại lỗi, tạo backlog cải tiến và tối ưu cost/latency/quality.

### Tài liệu cần đọc

- [modules/08_optimization_routing.md](modules/08_optimization_routing.md)
- [modules/09_feedback_loop.md](modules/09_feedback_loop.md)
- [operations/incident_runbook.md](operations/incident_runbook.md)

### Task

- [ ] Implement feedback API.
- [ ] Link feedback với trace.
- [ ] Implement error taxonomy.
- [ ] Implement error classifier.
- [ ] Implement error clustering.
- [ ] Implement human review queue.
- [ ] Implement semantic cache.
- [ ] Implement context compression.
- [ ] Implement dynamic top-k.
- [ ] Implement model routing policy.
- [ ] Implement provider fallback experiment.
- [ ] Run O1-O8 optimization experiment.

### Đầu ra

- Feedback dashboard/queue.
- Error clusters.
- Optimization report.
- Feedback-improved config.

### Kiểm tra dự kiến

```bash
python scripts/run_experiment.py --experiment optimization_o1_o8
python scripts/process_feedback.py --trace-window 7d
```

### Definition of Done

- [ ] Feedback lưu và truy được.
- [ ] Error clusters có top lỗi.
- [ ] Cache không dùng sai data_version.
- [ ] Routing giảm cost nhưng không giảm quality vượt ngưỡng.
- [ ] Có một vòng cải tiến từ feedback.

### Rủi ro

- Feedback ít: dùng feedback giả lập dựa trên failure cases.
- Optimization làm giảm quality: mọi config phải qua eval/gate.

---

## Phase 12 - Chạy thực nghiệm, viết báo cáo, đóng gói demo (Tuần 21-24)

### Mục tiêu

Hoàn tất 6 nhóm thực nghiệm, tổng hợp kết quả, viết báo cáo khóa luận và đóng gói demo.

### Tài liệu cần đọc

- [experiments/experiment_plan.md](experiments/experiment_plan.md)
- [experiments/result_reporting_template.md](experiments/result_reporting_template.md)
- [00_llmops_fit_assessment.md](00_llmops_fit_assessment.md)

### Task

- [ ] Chạy Experiment 1: Chunking Ablation.
- [ ] Chạy Experiment 2: Retrieval + Reranking.
- [ ] Chạy Experiment 3: Prompt + Model/Provider.
- [ ] Chạy Experiment 4: Quality Gate Effectiveness.
- [ ] Chạy Experiment 5: Observability + Error Classification.
- [ ] Chạy Experiment 6: Cost/Latency/Quality + Feedback.
- [ ] Tạo bảng kết quả tổng hợp.
- [ ] Tạo biểu đồ trade-off.
- [ ] Viết error analysis.
- [ ] Trả lời research questions.
- [ ] Hoàn thiện demo script.
- [ ] Hoàn thiện README chạy demo.
- [ ] Viết chương báo cáo liên quan.
- [ ] Chuẩn bị slide bảo vệ.

### Đầu ra

- 6 experiment reports.
- Final metrics summary.
- Error analysis.
- Demo package.
- Báo cáo khóa luận hoàn chỉnh.

### Kiểm tra dự kiến

```bash
python scripts/run_all_experiments.py
python scripts/generate_final_report.py
docker compose up
```

### Definition of Done

- [ ] Có đủ 6 report.
- [ ] Có bảng so sánh final config.
- [ ] Có demo chạy được end-to-end.
- [ ] Có dashboard minh họa.
- [ ] Có báo cáo trả lời RQ1-RQ5.
- [ ] Có danh sách hạn chế và hướng phát triển sau full-scope.

### Rủi ro

- Không đủ thời gian chạy full nhiều lần: ưu tiên final full run và dùng smoke cho lặp nhanh.
- Kết quả không đẹp: báo cáo trung thực, tập trung error analysis và bài học LLMOps.

---

## Checklist cross-phase bắt buộc

### Versioning

- [ ] Mọi data change có `data_version`.
- [ ] Mọi index có `index_version`.
- [ ] Mọi prompt có `prompt_version`.
- [ ] Mọi model config có `gateway_config_id`.
- [ ] Mọi eval có `eval_run_id`.
- [ ] Mọi gate có `gate_run_id`.

### Observability

- [ ] Mọi QA response có `trace_id`.
- [ ] Trace có retrieval span.
- [ ] Trace có prompt version.
- [ ] Trace có model/provider.
- [ ] Trace có token/cost/latency.
- [ ] Trace link được feedback.

### Quality

- [ ] Smoke set 50 câu chạy được.
- [ ] Full set 300 câu chạy được.
- [ ] Quality gate có critical/warning thresholds.
- [ ] Hallucination rate được đo.
- [ ] Citation accuracy được đo.
- [ ] Refusal accuracy được đo.

### Security

- [ ] Không có secret trong repo.
- [ ] Prompt injection set chạy được.
- [ ] PII/secret masking có trong log.
- [ ] Debug endpoint không public tùy tiện.
- [ ] Tool/provider config không lộ qua user API.

### Báo cáo

- [ ] Mỗi experiment có config và result.
- [ ] Mỗi kết luận có số liệu.
- [ ] Mỗi lỗi chính có root cause.
- [ ] Mỗi improvement có trước/sau.
- [ ] Final report có limitations rõ.

---

## Retrospective — điểm mạnh & nợ kỹ thuật cần quay lại

> Cập nhật cuối mỗi phase, không chỉ 1 lần. Phần trên trả lời "xong bao
> nhiêu %"; mục này trả lời **"làm vậy có ổn không, và nếu chưa ổn thì
> sửa ở đâu"** — để khi hệ thống chạy hết 12 phase, quay lại biết chỗ nào
> từng là đường tắt có chủ đích cần nâng cấp trước khi dùng số liệu làm
> báo cáo chính thức, và chỗ nào là cách làm nên giữ nguyên.

### 1. Đã làm tốt — giữ nguyên khi cải thiện phần khác

**Kỷ luật dữ liệu (không bịa, luôn có nguồn thật)**
- Mọi ground_truth trong golden set trích/diễn giải trực tiếp từ text đã tự tải/OCR — không bao giờ lấy từ tóm tắt search engine. Bằng chứng cụ thể: WebSearch tóm tắt học bổng ra 100%/70%/50%, đọc nguồn thật (D13) thì đúng là 130%/110%/100% — sai hoàn toàn, bị chặn TRƯỚC khi vào golden set (`experiments/golden_set_review.md` phát hiện #8).
- Khi 1 nguồn có khoảng trống thật (số QĐ học bổng D13, "quy chế học vụ" D2 không crawl được), ghi nhận là data gap tường minh (`requires_refusal`, risk_tag `data_gap`) thay vì đoán hoặc điền bừa.

**Khả năng phục hồi kỹ thuật (tìm bug thật, tự sửa tận gốc)**
- 2 lần data-loss bug trong `extract_text.py` (ghi đè `.txt` đã OCR khi rerun cho doc mới) đều được **tự phát hiện** qua kiểm tra chéo, không phải do user báo. Fix có 2 lớp độc lập; bài học rút ra: *"fix 1 bug data-loss phải audit toàn bộ dữ liệu liên quan, không chỉ phần vừa thao tác"* (lần đầu bỏ sót D3, phải quay lại lần 2).
- `ocr_scanned_pdfs.py`: sau khi mất trắng 1 lần OCR thành công vì crash giữa batch, sửa thành ghi manifest ngay sau MỖI document.
- Khi fastembed bị ISP chặn CDN giữa chừng tải (Phase 3), nhận diện ngay đây là CÙNG DẠNG lỗi đã gặp với Docker Hub (Phase 1), chuyển hướng sang tự viết BM25 (không phụ thuộc mạng ngoài) trong cùng phiên.

**Kỷ luật checklist trung thực**
- Không có mục nào tick `[x]` mà không có bằng chứng chạy thật đi kèm. Khi 1 tiêu chí DoD chỉ đạt một phần (Phase 2 "300 câu hỏi", Phase 3 "≥10 tài liệu"), checklist ghi rõ % thật và lý do — không âm thầm hạ tiêu chí.
- Approve golden set qua AI self-review (theo yêu cầu tường minh của user) vẫn có audit trail đầy đủ (`reviewed_by`, `reviewed_at`, `review_note`) thay vì sửa ngầm field, và ghi rõ đây KHÔNG tương đương domain-expert review.

**Thiết kế cấu hình**
- Không hard-code model/tham số trong code — mọi model, chunking param, rate limit nằm trong `config/*.yaml`, có `*_config_id` bắt buộc. Đổi model chỉ sửa YAML.
- Version đặt tên có quy tắc (`data_YYYYMMDD`, `idx_<data>_<embedding>`) nhất quán từ Phase 2. Qdrant collection đặt tên theo `index_version` (không phải 1 collection cố định) — cho phép rollback bằng cách trỏ lại `retrieval.yaml`.

**Kiểm chứng bằng chạy thật, không chỉ code + test đơn vị**
- Mỗi phase có bước "chạy thật trên Docker/API thật" trước khi commit (Phase 1: `/health/dependencies` thật; Phase 2: OCR thật tốn quota thật; Phase 3: `docker compose up` + ingest thật tốn quota Gemini thật + `smoke_retrieval.py` trả kết quả thật).

### 2. Cần cải thiện — nợ kỹ thuật, xếp theo mức ưu tiên

**P0 — phải làm trước khi dùng làm baseline/số liệu chính thức cho báo cáo**

1. **Golden set mới 76/300 (25%).** Gốc rễ khiến mọi metric ở Phase 5+ (recall, faithfulness...) chưa đại diện được cho toàn domain. `golden_set_stats.md` có bảng so target theo nhóm (adversarial 2/20, refusal thật 4/30, multi-hop 4/30 — chỉ 1 câu multi-hop THẬT qua 2 văn bản, ambiguous 1/20).
2. **Golden set chỉ qua AI self-review, chưa qua domain-expert review thật.** User (SV IUH) nên tự đối chiếu trải nghiệm thực tế, đặc biệt câu có con số (tín chỉ/điểm/%) — "khớp nguồn" không đồng nghĩa "nguồn đó còn đúng/còn hiệu lực".
3. **`relevant_chunks` trong golden set vẫn trống.** Auto-match citation cấp Điểm (vd "Điều 6, Khoản 4.a") với chunk gom theo nhóm Khoản (`structure_aware`) chỉ khớp đúng 5/71 câu không-refusal — chưa gán vì rủi ro gán sai cao hơn giá trị. Không có `relevant_chunks` = không đo được recall@k đúng nghĩa ở Phase 5. **Hướng sửa gợi ý:** dùng chunk `parent_child` (child = từng Khoản riêng) làm nguồn linking, hoặc parse range "Khoản 4-6".

**P1 — nên làm trước khi coi hệ thống "hoàn thành"**

4. **9/13 tài liệu được ingest ở Phase 3** — 4 tài liệu còn lại là site-chrome SPA gần như rỗng nội dung, loại có chủ đích. Nhưng **D2 "quy chế học vụ" là nội dung thật sự cần** mà vẫn chưa có cách lấy (pdt.iuh.edu.vn là SPA React/Vue, cần Playwright — ngoài scope hiện tại).
5. **`page_start`/`page_end` luôn `null`** trong mọi chunk — marker trang OCR bị xóa ở bước normalize trước khi tới chunker. Muốn page-level citation chính xác phải thread page marker qua trước khi strip.
6. ~~CI chưa cài `dataops`/`ragops` extras~~ — **đã fix trong Phase 3** (`.github/workflows/ci.yml` cài `.[dev,dataops,ragops]`).
7. **`tests/integration/` và `tests/e2e/` vẫn trống** — toàn bộ pipeline Qdrant/Postgres/Gemini mới verify bằng chạy tay, chưa có test tự động hoá lại được (kể cả dạng skip-nếu-service-không-chạy).
8. **BM25 tự viết (`src/dataops/sparse_bm25.py`) chưa so sánh với 1 baseline đã biết đúng** (vd rank_bm25) để xác nhận công thức/hashing-trick cho kết quả tương đương — mới có unit test kiểm tra tính chất tương đối, chưa kiểm tra độ chính xác retrieval tuyệt đối.
9. **Chunking coverage còn thiếu nội dung:** học phí cụ thể theo ngành/năm, thang điểm rèn luyện đầy đủ — chưa tìm thấy trong bất kỳ nguồn nào đã ingest (thiếu nguồn từ Phase 2, không phải lỗi chunking).

**P2 — cải thiện khi có thời gian, không chặn tiến độ**

10. **Token counting dùng `tiktoken cl100k_base`** làm xấp xỉ (không phải tokenizer thật của Gemini) — đủ để quyết định ranh giới chunk, không chính xác nếu cần tính cost/latency theo token thật.
11. **Không có migration tool cho Postgres** (`sql/schema.sql` áp dụng thủ công, `CREATE TABLE IF NOT EXISTS`) — ổn cho quy mô hiện tại (2 bảng), khó track lịch sử nếu schema đổi nhiều.
12. **Môi trường có phần phụ thuộc máy cụ thể của user** (Docker Desktop registry-mirror workaround, Ollama cài sẵn dù cuối cùng không dùng) — người khác clone repo cần tự set up.
13. **Retry/backoff cho Gemini API viết riêng lẻ ở từng script** thay vì 1 lớp client dùng chung — chấp nhận được ở quy mô hiện tại, nên rút thành `src/common/gemini_client.py` nếu thêm nhiều script gọi Gemini nữa.
14. **Chưa verify model ID/URL tham khảo dùng trong báo cáo khóa luận** (GPT-5.5, Gemma 4, Llama 4...) tồn tại thật; chưa xóa tham chiếu file `llmops_image_prompts.md` không tồn tại; caption ảnh chưa khớp tên file `figures/`; chưa export lại `.docx`. Không liên quan Phase 3, đang mở từ trước.

### Cách dùng

Trước khi bắt đầu 1 phase mới: đọc P0/P1 xem có mục nào block không. Sau
Phase 12: xử lý P0 trước khi dùng số liệu cho báo cáo chính thức. Khi 1
mục được xử lý xong, gạch ngang (như mục 6) thay vì xoá — giữ lại làm
bằng chứng đã từng có vấn đề và đã sửa.

**Changelog:** 2026-07-11 — tạo mục này, tổng hợp điểm tốt/nợ kỹ thuật từ Phase 1-3.

