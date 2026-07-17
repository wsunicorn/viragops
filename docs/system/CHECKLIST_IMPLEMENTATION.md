# Checklist triển khai LLMOps/RAGOps Platform

File này là bảng điều khiển chính để thực hiện project từ đầu đến cuối. Mỗi phase có mục tiêu, task, tài liệu cần đọc, đầu ra, kiểm tra và tiêu chí hoàn tất.

## Quy ước

- `[ ]` chưa làm.
- `[~]` đang làm.
- `[x]` đã xong.
- Không chuyển phase nếu Definition of Done của phase hiện tại chưa đạt, trừ khi có ghi chú kỹ thuật rõ ràng.
- Mọi thay đổi lớn phải cập nhật tài liệu liên quan trong `docs/system/`.
- Mỗi phase có mục "Chưa tốt / cần cải thiện" ngay trong phase đó (sau "Rủi ro") — ghi nợ kỹ thuật và phần chưa hoàn thành phát sinh khi làm phase này, để quay lại xử lý trước khi dùng số liệu làm báo cáo chính thức.

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

### Chưa tốt / cần cải thiện

- Không có nợ kỹ thuật đáng kể phát sinh ở phase này — skeleton tối
  giản đúng như mục tiêu, dependency nặng chủ ý chưa thêm.
- Còn treo từ trước khi vào Phase 1 (không do phase này gây ra, việc
  của khâu viết báo cáo/blueprint): chưa verify các model ID/URL tham
  khảo trong blueprint (GPT-5.5, Gemma 4, Llama 4...) tồn tại thật; còn
  tham chiếu file không tồn tại `llmops_image_prompts.md`; caption ảnh
  chưa khớp tên file `figures/`. Theo dõi tiếp ở Phase 12 (mục "Báo cáo").

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
- [x] Tạo bản nháp 300 câu hỏi — **300/300 câu** (`scripts/seed_golden_set_iuh.py` → `data/test_sets/golden_set.jsonl`), không bịa số liệu. Mở rộng 76→300 hoàn tất 2026-07-12 (xem `golden_set_review.md` mục "Batch 4").
- [x] Chia câu hỏi theo 5 nhóm: có đáp án (factoid/procedural), refusal (data-gap + out_of_scope), adversarial, multi-hop, ambiguous — khớp CHÍNH XÁC cơ cấu `golden_set_design.md` (200/30/20/30/20, verify bằng `golden_set_stats.md`).
- [x] Gắn ground truth answer — cho cả 300 câu, trích/diễn giải trực tiếp từ nguồn thật.
- [x] Gắn relevant documents — cho cả 300 câu.
- [x] Sau khi có chunk, gắn relevant chunks — **ĐÃ GÁN 249/250 câu không-refusal** (Phase 4 gốc 71/71, re-run 2026-07-12 sau mở rộng 300 câu) qua `scripts/link_relevant_chunks.py` + matcher thật (`src/retrieval/citation_matcher.py`). 2 câu miss (q_156, q_229) do lexical threshold — chấp nhận, không ép gán sai. Seed script đã được vá để KHÔNG xóa relevant_chunks khi rerun.
- [x] Gắn expected citations — cho câu không refusal trong cả 300 câu.
- [x] Review thủ công ít nhất 30 câu mẫu — **300/300 câu `approved`**: 76 câu batch 1-3 qua AI self-review (2026-07-11, theo yêu cầu trực tiếp user), 224 câu batch 4 qua AI self-review (2026-07-12, theo yêu cầu trực tiếp user "domain-expert review 224 câu golden set mới") dùng `scripts/review_golden_set_batch.py` (mới — tự động cross-reference document_id + xác nhận Điều tồn tại trong nguồn + đối chiếu số liệu) + `scripts/approve_golden_set.py`. **Batch 4 tìm và sửa 5 lỗi thật** (2 sai document_id trích dẫn, 1 thiếu citation, 1 câu chữ ngụ ý sai, 1 dùng số liệu lỗi thời — chi tiết `golden_set_review.md`). Còn 1 điểm treo: số QĐ học bổng D13. **Lưu ý:** vẫn là AI self-review có phương pháp, không thay thế domain-expert review đầy đủ — khuyến nghị user (SV IUH) spot-check trước khi dùng chính thức cho báo cáo.
- [x] Tạo smoke set 50 câu — `src/evaluation/golden_set.py::smoke_subset()` (Phase 8), stratified theo cả 6 category thật, dùng bởi `scripts/run_evaluation.py --mode smoke`.
- [x] Tạo adversarial set 20 câu — đạt đúng target thiết kế: 11 adversarial (prompt injection/social engineering/data exfiltration) + 9 out_of_scope = 20/20.

### Đầu ra

- [x] `golden_set.jsonl` — 300/300 câu, `data/test_sets/golden_set.jsonl`, đã approve toàn bộ.
- [x] `golden_set_stats.md` — tự động sinh, `experiments/golden_set_stats.md`, khớp chính xác cơ cấu thiết kế.
- [x] `relevant_chunks_mapping.csv` — interim mức document, `data/test_sets/relevant_chunks_mapping.csv`.
- [x] `golden_set_review.md` — `experiments/golden_set_review.md`, đầy đủ audit trail 2 batch approval.

### Kiểm tra dự kiến

```bash
python scripts/validate_golden_set.py
python scripts/golden_set_stats.py
python scripts/review_golden_set_batch.py   # verify tự động trước khi approve batch mới
```

### Definition of Done

**ĐẠT — Phase 2 hoàn tất (2026-07-12).**

- [x] Có 300 câu hỏi (300/300, khớp cơ cấu 200/30/20/30/20 — xem `golden_set_stats.md`).
- [x] Mọi câu có đáp án đều có ground truth *(verify bằng `scripts/validate_golden_set.py`, 300/300)*.
- [x] Mọi câu refusal có `requires_refusal=true` *(300/300)*.
- [x] Category/difficulty/risk_tags đầy đủ *(300/300, validator khóa cứng enum)*.
- [x] Không có câu thiếu nguồn kiểm chứng *(300 câu đều trích từ text thật; câu data-gap cố ý không có nguồn vì phản ánh giới hạn dữ liệu thật, không phải bịa)*.
- [x] **Review/approve toàn bộ** — 300/300 câu `approved` qua AI self-review (2 batch, audit trail đầy đủ trong `golden_set_review.md`). Không phải domain-expert review đầy đủ theo nghĩa gốc của rule này — khuyến nghị spot-check thêm trước khi dùng làm baseline chính thức cho báo cáo khóa luận.

### Rủi ro

- Golden set kém làm metric vô nghĩa: phải review thủ công.
- Câu hỏi multi-hop giả: phải cần ít nhất 2 chunks thật.

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** mọi ground_truth trích/diễn giải
trực tiếp từ text đã tự tải/OCR, không bao giờ lấy từ tóm tắt search
engine — có bằng chứng cụ thể việc này cứu 1 lỗi thật (WebSearch tóm tắt
học bổng ra 100%/70%/50%, đọc nguồn thật D13 thì đúng là 130%/110%/100%,
chặn được TRƯỚC khi vào golden set, xem `experiments/golden_set_review.md`
phát hiện #8). 2 lần data-loss bug trong `extract_text.py` (ghi đè `.txt`
đã OCR khi rerun cho doc mới) đều tự phát hiện qua kiểm tra chéo, fix có
2 lớp độc lập — bài học: "fix 1 bug data-loss phải audit toàn bộ dữ liệu
liên quan, không chỉ phần vừa thao tác" (lần đầu bỏ sót D3, phải quay
lại lần 2).

**Còn thiếu, cần quay lại:**
- ~~Golden set mới 76/300 (25%)~~ → **Đã mở rộng đúng 300/300 (2026-07-12)**,
  cơ cấu khớp chính xác `golden_set_design.md` (200 có đáp án / 30 refusal /
  20 adversarial / 30 multi-hop / 20 ambiguous). Xem chi tiết
  `experiments/golden_set_review.md` mục "Batch 4". Thang điểm rèn luyện
  đầy đủ (Xuất sắc/Tốt/Khá/TB/Yếu/Kém) hóa ra CÓ trong Sổ tay 2024 (trang
  11) — chỉ là chưa đọc tới khi viết batch 1-3.
- ~~Golden set chỉ qua AI self-review, 224 câu batch 4 còn
  `pending_review`~~ → **Đã approve 300/300 câu (2026-07-12)**, xem
  `golden_set_review.md` mục "Audit trail approval — Batch 4". Quá trình
  review tự động (script mới `scripts/review_golden_set_batch.py`) tìm ra
  và SỬA 5 lỗi thật (2 câu sai document_id trích dẫn — nội dung đúng
  nhưng trỏ nhầm nguồn; 1 câu thiếu citation cho lập luận chéo văn bản; 1
  câu câu chữ ngụ ý sai số liệu là trích nguyên văn; 1 câu dùng bảng quy
  đổi CŨ/lỗi thời từ phụ lục quyết định 2021 thay vì bảng cập nhật hiện
  hành trên camnang — ví dụ thật về rủi ro "data drift" đáng đưa vào báo
  cáo khóa luận). Vẫn CHƯA phải domain-expert review đầy đủ (chỉ AI
  self-review + spot-check 16/224 câu thủ công) — user (SV IUH) nên tự
  đối chiếu trải nghiệm thực tế trước khi dùng chính thức, đặc biệt câu
  có con số (tín chỉ/điểm/%): "khớp nguồn" không đồng nghĩa "nguồn đó còn
  đúng/còn hiệu lực".
- ~~`relevant_chunks` vẫn để trống cho mọi câu~~ → **Đã gán 249/300 câu
  (99.6% trong nhóm có căn cứ) sau khi re-run `link_relevant_chunks.py`
  trên chunk set mới** (xem Phase 3). 2 câu miss (q_156, q_229) do lexical
  threshold, domain expert nên gán tay nếu cần 100%.
- Data gap thật (không phải lỗi crawl, không nên cố lấp): số QĐ học bổng
  D13 để trống ngay trên nguồn IUH; học phí cụ thể theo ngành/năm — vẫn
  chưa tìm thấy trong bất kỳ nguồn nào đã ingest, dùng làm câu refusal có
  chủ đích thay vì cố lấp bằng số bịa.
- **D2/D7/D11/D12 xác nhận lại lần 2 (2026-07-12) vẫn không dùng được**
  cho mở rộng golden set — D7/D11/D12 rỗng/chỉ khung điều hướng
  (D12 thậm chí 0 byte), D2 là nội dung thật nhưng khác đánh số Điều với
  bản đang index và không xác minh được số QĐ (rủi ro trộn 2 phiên bản
  quy chế) — xem `data_sources_iuh.md` mục 7 để biết chi tiết + bằng
  chứng (fetch trực tiếp camnang.iuh.edu.vn xác nhận QĐ1482 vẫn hiện
  hành). D10 giải quyết được bằng cách fetch trực tiếp nguồn thay thế
  (D14), nhưng đây là ngoại lệ may mắn (camnang có trang tương đương),
  không áp dụng được cho D7/D11/D12.

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
~~`golden_set.jsonl`'s `relevant_chunks` vẫn để trống~~ → **Đã giải quyết ở
Phase 4** (`src/retrieval/citation_matcher.py`, structural regex parse
Điều/Khoản + range, fallback lexical token-overlap) — 71/71 câu batch 1-3,
và 249/300 sau khi mở rộng golden set lên 300 câu (2026-07-12, xem
`golden_set_review.md` mục "Batch 4").

### Rủi ro

- PDF/OCR lỗi: bắt đầu bằng PDF text trước, OCR làm sau. *(Đã xử lý ở Phase 2.)*
- Chunk cắt mất Điều/Khoản: ưu tiên structure-aware. *(Đã áp dụng — xem `chunk_structure_aware`.)*
- **Rủi ro mới phát sinh khi chạy thật:** fastembed/huggingface.co bị ISP chặn CDN giữa chừng tải model — xử lý bằng cách tự viết BM25 (không phụ thuộc mạng ngoài). Gemini embedding free-tier rate limit tính theo SỐ TEXT trong batch chứ không phải số lệnh gọi — xử lý bằng batch ≤80 + delay ≥65s.

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** không hard-code model/tham số —
mọi model, chunking param, rate limit nằm trong `config/*.yaml`. Khi
fastembed bị ISP chặn CDN giữa chừng, nhận diện ngay đây là CÙNG DẠNG
lỗi đã gặp với Docker Hub ở Phase 1 và chuyển hướng tự viết BM25 trong
cùng phiên thay vì retry mù quáng. Mỗi bước đều chạy thật trên
Docker/API thật trước khi commit (không dừng ở "test pass") —
`docker compose up` + ingest thật tốn quota Gemini thật +
`smoke_retrieval.py` trả kết quả đúng domain.

**Còn thiếu, cần quay lại:**
- ~~Chỉ 9/13 tài liệu được ingest~~ → **10/14 tính đến 2026-07-12** (thêm
  D14, xem Phase 2). D2/D7/D11/D12 xác nhận LẠI lần 2 vẫn không dùng được
  (không chỉ "chưa có cách lấy" như ghi lúc đầu — D2 thực ra CÓ nội dung
  thật nhưng là bản không xác minh được/khác đánh số Điều với bản đang
  index, rủi ro trộn phiên bản; D7/D11/D12 xác nhận rỗng thật). Vẫn cần
  Playwright hoặc liên hệ trực tiếp Phòng Đào tạo nếu muốn D2/D7/D11/D12.
- `page_start`/`page_end` luôn `null` trong mọi chunk — marker trang OCR
  (`--- Trang N ---`) bị xóa ở bước `vietnamese_normalizer.clean_text`
  trước khi tới chunker nên thông tin trang bị mất. Muốn page-level
  citation chính xác phải thread marker qua trước khi strip.
- ~~`relevant_chunks` trong golden set: auto-match chỉ khớp đúng 5/71~~ →
  **Giải quyết ở Phase 4** bằng `citation_matcher.py` (structural +
  lexical fallback), xem "Còn treo" phía trên.
- `tests/integration/` và `tests/e2e/` vẫn trống — pipeline
  Qdrant/Postgres/Gemini mới verify bằng chạy tay, chưa có test tự động
  hoá (kể cả dạng skip-nếu-service-không-chạy).
- BM25 tự viết (`src/dataops/sparse_bm25.py`) chưa so sánh với 1
  baseline đã biết đúng (vd rank_bm25) để xác nhận công thức/hashing-trick
  cho kết quả tương đương — mới có unit test kiểm tra tính chất tương
  đối, chưa kiểm tra độ chính xác retrieval tuyệt đối.
- Token counting dùng `tiktoken cl100k_base` làm xấp xỉ (không phải
  tokenizer thật của Gemini) — đủ để quyết định ranh giới chunk, không
  chính xác nếu cần tính cost/latency theo token thật.
- ~~Không có migration tool cho Postgres~~ → **Đã thêm (2026-07-13)**:
  `sql/migrations/NNNN_*.sql` (đánh số, áp theo thứ tự) + bảng
  `schema_migrations` (filename, applied_at) track lịch sử thật, thay
  file `schema.sql` đơn lẻ sửa tại chỗ trước đây. `scripts/
  init_postgres_schema.py` viết lại thành migration runner, mỗi file
  chạy trong 1 transaction riêng, bỏ qua file đã áp dụng. Verify thật:
  chạy trên Postgres đang có dữ liệu thật (8 prompt, 10 document, 222
  chunk) — không mất dữ liệu, `schema_migrations` ghi đúng
  `0001_initial_schema.sql`, chạy lại lần 2 skip đúng (idempotent). Vẫn
  cố ý không dùng Alembic/ORM đầy đủ — quy mô 3 bảng chưa cần.
- Môi trường có phần phụ thuộc máy cụ thể của user (Docker Desktop
  registry-mirror workaround, Ollama cài sẵn dù cuối cùng không dùng) —
  người khác clone repo cần tự set up.
- Retry/backoff cho Gemini API viết riêng lẻ ở từng script
  (`ocr_scanned_pdfs.py`, `embedder.py`) thay vì 1 lớp client dùng
  chung — nên rút thành `src/common/gemini_client.py` nếu thêm nhiều
  script gọi Gemini nữa.
- ~~CI chưa cài `dataops`/`ragops` extras~~ — **đã fix trong Phase 3**
  (`.github/workflows/ci.yml` cài `.[dev,dataops,ragops]`).

---

## Phase 4 - Xây Retrieval Experiment Layer (Tuần 7-8)

### Mục tiêu

So sánh chunking, dense/sparse/hybrid retrieval và reranking để chọn best retrieval config.

### Tài liệu cần đọc

- [modules/02_retrieval_experiment.md](modules/02_retrieval_experiment.md)
- [experiments/experiment_plan.md](experiments/experiment_plan.md)
- [contracts/metric_definitions.md](contracts/metric_definitions.md)

### Task

- [x] Implement dense retrieval — `src/retrieval/retriever.py` (Qdrant Query API).
- [x] Implement sparse/BM25 baseline — dùng luôn sparse vector BM25 tự viết đã index từ Phase 3.
- [x] Implement hybrid RRF — fusion server-side qua Query API prefetch.
- [x] Implement hybrid DBSF nếu khả thi — khả thi (qdrant v1.15.4 hỗ trợ), VÀ chính là config thắng cuộc.
- [x] Implement reranker wrapper — `src/retrieval/reranker.py` (Gemini listwise; bge-reranker-v2-m3 không tải được do ISP chặn CDN HF — xem `modules/02_retrieval_experiment.md`).
- [x] Implement Recall@k, MRR, nDCG — `src/retrieval/metrics.py`, dạng citation-coverage (1 citation = 1 nhóm chunk chấp nhận được), 51 unit test.
- [x] Implement experiment runner — `scripts/run_experiment.py` + `config/experiments_retrieval.yaml`; query embedding cache 1 lần dùng mọi config.
- [x] Chạy chunking ablation — 4 strategy thật trên 4 Qdrant collection (phải index thêm fixed/recursive/parent_child bằng `scripts/index_all_strategies.py`).
- [x] Chạy retrieval/reranking comparison — 8 config thật trên 71 câu golden set.
- [x] Xuất report — `experiments/results_retrieval_reranking.md` + `results_chunking_ablation.md` + CSV trong `data/experiments/`.

**Tiền đề quan trọng làm trước experiment:** gán `relevant_chunks` thật cho
golden set (nợ P0 từ Phase 3) — `src/retrieval/citation_matcher.py` (parse
Điều/Khoản + range + lexical fallback) khớp 71/71 câu, chạy qua
`scripts/link_relevant_chunks.py`, report ở `data/test_sets/relevant_chunks_report.md`.

### Đầu ra

- [x] Retrieval experiment reports — 2 file results_*.md + CSV.
- [x] Best retrieval config — **`hybrid_dbsf_v2`**: recall@5=0.993, hit=1.000, MRR=0.827, nDCG@5=0.869, p95=17ms — đã chốt vào `config/retrieval.yaml` (reranker TẮT theo số liệu: Gemini rerank làm giảm hybrid 0.979→0.958 và +1s/câu).
- [x] Failure cases retrieval — best config 8-config: 0 câu trượt; ablation: 1 câu (q_024, camnang điều kiện tốt nghiệp hệ VLVH) — ghi trong report.

### Kiểm tra dự kiến

```bash
python scripts/link_relevant_chunks.py
python scripts/index_all_strategies.py
python scripts/run_experiment.py --experiment chunking_ablation
python scripts/run_experiment.py --experiment retrieval_reranking
```

### Definition of Done

- [x] Chạy được ít nhất 8 retrieval configs — đúng 8 config experiment 2 (+4 config ablation).
- [x] Có metric retrieval đầy đủ — recall@5, hit rate, MRR, nDCG@5, latency p50/p95 cho từng config.
- [x] Có best config — `hybrid_dbsf_v2`, vượt target recall@5 >= 0.85 của `metric_definitions.md` (0.993).
- [x] Có phân tích lỗi retrieval failure — mục cuối mỗi report.

### Rủi ro

- Sparse retrieval mất thời gian: dùng baseline BM25 nhẹ trước. *(Đã né được — BM25 tự viết từ Phase 3 dùng lại luôn.)*
- Reranker chậm: chỉ rerank top-20. *(Thực tế rerank pool 10; vấn đề thật không phải chậm mà là GIẢM chất lượng — đã tắt.)*

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** đóng nợ P0 relevant_chunks TRƯỚC khi
chạy experiment (metric vô nghĩa nếu ground truth sai); cache query
embedding 1 lần dùng cho mọi config (tiết kiệm ~10 lần quota); mọi kết
luận config đều bằng số liệu thật chạy trên Qdrant thật, không chọn cảm tính.

**Còn thiếu, cần quay lại:**
- **Quota embedding free tier có hạn mức NGÀY 1000 request-item** (phát
  hiện giữa chừng khi index parent_child chết ở batch 3 — trước đó chỉ
  biết hạn mức 100/phút; reset ~14:00 giờ VN = nửa đêm Pacific). Đã xử lý
  bằng key thứ 2 user cấp (project Google khác, `GEMINI_API_KEY_2` trong
  `.env`). Bài học vận hành: chạy eval batch 300 câu ở Phase 8+ phải
  budget quota theo NGÀY, không chỉ theo phút — hoặc chuyển embedding
  sang local (Ollama) trước khi scale.
- **30/72 citation khớp bằng lexical fallback** (token-overlap với
  ground_truth) — yếu hơn structural match; nếu ground_truth viết lại
  thoáng quá thì có thể chọn nhầm chunk. Reviewer nên spot-check nhóm
  lexical trong `relevant_chunks_report.md`.
- **So sánh chéo chunking strategy có nhiễu**: fixed/recursive không có
  section nên relevant set của chúng 100% từ lexical matching — recall
  cao của 2 strategy này một phần là artifact của cách chấm (chunk được
  chọn làm ground truth chính là chunk chứa nguyên văn ground_truth).
  structure_aware/parent_child được chấm khắt khe hơn (structural).
- **Reranker thật (cross-encoder) chưa thử được** vì ISP chặn CDN
  huggingface.co — Gemini listwise chỉ là thay thế tạm và đã chứng minh
  không tốt cho hybrid. Khi có mạng khác/mirror, tải bge-reranker-v2-m3
  (hoặc ViRanker cho tiếng Việt) và chạy lại 2 config rerank.
- **Kế hoạch gốc Experiment 1 có 8 config chunking** (fixed 256/512/768,
  semantic, table-aware) — mới chạy 4; semantic + table-aware chưa
  implement, fixed chỉ 1 mức 300 token. Chưa đủ để kết luận tuyệt đối
  "structure_aware là tốt nhất mọi biến thể".
- ~~Golden set vẫn 76/300~~ → **Golden set đạt 300/300 (2026-07-12), và cả
  2 experiment ĐÃ CHẠY LẠI trên bộ 300 câu / `data_20260712`** cùng ngày.
  Kết luận `hybrid_dbsf_v2` + `structure_aware` **được tái xác nhận, không
  đổi** (recall@5 giảm 0.993→0.932 và 0.906 cho chunking — kỳ vọng khi
  golden set lớn/đa dạng hơn, không phải retrieval kém đi; thứ hạng config
  giữ nguyên). Phát hiện mới đáng chú ý: **kết luận cũ "Gemini rerank luôn
  làm giảm chất lượng hybrid" KHÔNG còn đúng nguyên vẹn** — trên 249 câu,
  rerank thực ra giúp cả dense (0.882→0.894) và hybrid_rrf (0.906→0.928),
  chỉ là vẫn không vượt được hybrid_dbsf không-rerank. Quyết định tắt
  reranker vẫn đúng nhưng lý do chính xác hơn là "không đáng đổi latency"
  (p95 đo được **61 giây/câu** do bị rate-limit thật khi chạy 250 câu liên
  tục — xem `results_retrieval_reranking.md`), không phải "luôn tệ hơn".
- **Quota Gemini embedding hết SẠCH cả 3 key trong lúc re-run** (structure_
  aware+fixed+recursive+parent_child = ~1561 chunk + 250 query = ~1800+
  item, vượt xa 1 key/ngày) — user cấp thêm key 3 và key 4 giữa chừng
  (`GEMINI_API_KEY_3`, `GEMINI_API_KEY_4` trong `.env`, `embedder.py`
  `_clients()` giờ hỗ trợ tối đa 4 key). Bài học vận hành được xác nhận
  lại lần nữa: **eval quy mô 300 câu tốn quota nhiều hơn hẳn** so với 71
  câu — nên tính trước ngân sách quota theo ngày/key trước khi chạy full
  suite, hoặc chuyển sang embedding local cho khối lượng lớn.

---

## Phase 5 - Xây RAG Runtime (Tuần 9-10)

### Mục tiêu

Xây API hỏi đáp có retrieval, prompt assembly, citation, refusal và trace.

### Tài liệu cần đọc

- [modules/03_rag_runtime_model_gateway.md](modules/03_rag_runtime_model_gateway.md)
- [contracts/api_contracts.md](contracts/api_contracts.md)
- [contracts/data_schemas.md](contracts/data_schemas.md)

### Task

- [x] Implement `POST /qa/query` — `src/api/routes/qa.py`, schema đúng `api_contracts.md`.
- [x] Implement query normalization — tái dùng `vietnamese_normalizer.normalize_for_search` cho nhánh sparse (embedding dùng câu gốc giữ nguyên dấu câu).
- [x] Integrate best retrieval config — load `hybrid_dbsf_v2` (Phase 4) + BM25 state + collection từ config/manifest lúc init, không hard-code.
- [x] Implement context assembly — `prompt_builder.format_context` ([chunk_id] + tiêu đề văn bản + section, cắt 2500 ký tự/chunk).
- [x] Implement prompt rendering — `p1_grounded_v1` (active_version trong prompts.yaml): chỉ trả lời từ ngữ cảnh, bắt buộc citation, refusal khi thiếu căn cứ, chống prompt-injection trong context, output strict JSON.
- [x] Implement model call placeholder/mock trước — `MockGateway` cho test; `GeminiGateway` thật đọc tier từ `model_gateway.yaml` (primary→fallback, JSON mode) — LiteLLM thay transport ở Phase 7, call site giữ nguyên.
- [x] Implement citation parser — `src/rag/citation.py`: parse JSON (chịu được fence), DROP citation bịa, hạ cấp answer-không-nguồn thành refusal, output không parse được → refusal an toàn.
- [x] Implement refusal policy — 2 lớp: pre-LLM (< min_context_chunks, không tốn lượt gọi) + post-LLM (model khai refusal / mất hết citation hợp lệ).
- [x] Implement trace_id — `trace_store.py`: JSONL (`data/traces/`, gitignored) + in-memory window 500, schema theo `data_schemas.md`.
- [x] Implement `POST /qa/debug` — trả retrieved chunks + score + prompt_version + data/index/retrieval versions (không lộ nội dung prompt đầy đủ).

Bonus phát sinh: `GET /qa/traces/{trace_id}` (contract module 03) và
key-rotation trong embedder (429 daily quota → thử `GEMINI_API_KEY_2`).

### Đầu ra

- [x] QA API hoạt động — **verify thật bằng curl với Gemini thật** (chi tiết 3 kịch bản trong `modules/03_rag_runtime_model_gateway.md`).
- [x] Debug endpoint — trả 5 chunk DBSF + toàn bộ version metadata.
- [x] Trace cơ bản — retrieval_ms/generation_ms/token/citations/error_labels, đọc lại được qua GET.

### Kiểm tra dự kiến

```bash
uvicorn src.api.main:app --port 8000
curl -X POST http://localhost:8000/qa/query -H "Content-Type: application/json" --data-binary @question.json
pytest tests/integration/test_qa_flow.py   # tự skip nếu Qdrant tắt
```

### Definition of Done

- [x] Câu hỏi có đáp án trả answer + citation — verify thật: "điểm TB tích lũy để tốt nghiệp?" → "2.0 thang 4" cite đúng Điều 33 Khoản 1 QĐ 1482; câu đa nguồn cite 3 chunk từ 3 văn bản khác nhau.
- [x] Câu hỏi không có căn cứ trả refusal — verify thật: "giá vàng hôm nay?" → refusal, citations rỗng.
- [x] Response có trace_id — mọi response, kể cả refusal pre-LLM.
- [x] Debug endpoint trả retrieved chunks — kèm DBSF score thật (~1.3-1.7).

### Rủi ro

- Citation không ổn: bắt output format có citations field. *(Đã xử lý: JSON mode + validate + fail-closed.)*
- Runtime lẫn logic provider: tách gateway ở phase sau. *(Đã tách sẵn interface `Gateway.generate(tier, prompt)` — Phase 7 chỉ thay transport.)*

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** citation fail-closed (thà refusal
còn hơn trả câu không nguồn); gateway interface tách trước khi có LiteLLM
(Phase 7 không phải sửa runtime); integration test dùng Qdrant thật +
gateway mock + embed giả — chạy được trong CI-có-service mà không tốn quota.

**Còn thiếu, cần quay lại:**
- **`/qa/stream` chưa có** (contract có nêu) — chờ LiteLLM Phase 7 để
  không viết streaming 2 lần.
- ~~`thresholds.min_score` (0.15) chưa enforce~~ → **Đã calibrate + enforce
  (2026-07-13)**, xem CHECKLIST Phase 8 "Chưa tốt" mục min_score cho số
  liệu đầy đủ. `src/rag/service.py::answer()` giờ refuse pre-LLM khi
  `len(chunks) < min_context_chunks` HOẶC top-1 score < `min_score`
  (`config/retrieval.yaml`, giờ = 1.10, tính từ `scripts/calibrate_min_score.py`
  trên 875 trace thật thay vì đoán).
- ~~`confidence` trả `null`~~ → **Đã implement (2026-07-13)**, xem CHECKLIST
  Phase 8 "Chưa tốt" mục confidence heuristic cho chi tiết đầy đủ.
  `src/rag/confidence.py::compute_confidence()` — heuristic có căn cứ từ
  retrieval score + citation validity + fallback hop, KHÔNG phải xác suất
  calibrate qua ground-truth correctness (chưa có nhãn đó). `None` khi
  refusal=True.
- **Trace store chỉ single-process** (in-memory + JSONL append) — đủ cho
  dev server, không đủ cho multi-worker; Langfuse Phase 10 thay thế.
- **`cost_usd` luôn 0.0** (free tier) — cost model thật cần bảng giá
  provider, để Phase 10 (observability/cost).
- **Semantic cache (bước 4 flow chuẩn) chưa có** — Phase 8 theo kế hoạch.
- **Chưa có rate-limit/auth trên API** — dev mode; cần trước khi expose
  ra ngoài (Phase 9 security checklist).

---

## Phase 6 - Xây PromptOps (Tuần 11)

### Mục tiêu

Quản lý prompt versions, prompt diff, comparison và active prompt policy.

### Tài liệu cần đọc

- [modules/04_promptops.md](modules/04_promptops.md)
- [contracts/config_schemas.md](contracts/config_schemas.md)

### Task

- [x] Tạo prompt registry schema — bảng `prompts` trong `sql/migrations/0001_initial_schema.sql` (13 field metadata + partial unique index "1 active/prompt_id"; đổi từ `sql/schema.sql` đơn lẻ sang thư mục migrations có đánh số 2026-07-13).
- [x] Implement CRUD prompt — `src/promptops/registry.py` + API routes `/prompts` (create/versions/diff/activate).
- [x] Tạo 6 prompt variants P0-P5 — `src/promptops/templates.py` seed vào registry (`scripts/seed_prompts.py`, idempotent); cùng biến + cùng JSON contract để mọi variant đi qua chung citation parser.
- [x] Implement prompt renderer — `src/promptops/renderer.py` (str.format + validate biến khai báo vs biến dùng thật, chặn từ lúc ghi registry).
- [x] Implement prompt diff — `src/promptops/diff.py` (unified diff) + endpoint.
- [x] Implement prompt comparison runner — `scripts/run_prompt_comparison.py`: retrieval chạy 1 lần/câu dùng chung mọi version, embed bổ sung câu smoke thiếu cache, gán `eval_result_id` ngược vào registry.
- [x] Integrate active prompt vào runtime — `RagService` nhận `PromptProvider` (production: `RegistryPromptProvider` đọc DB; test: `StaticPromptProvider`) — **prompt hard-code trong `prompt_builder.py` đã gỡ**.
- [x] Log prompt version trong trace — verify chuỗi registry → runtime → trace bằng test thật.

### Đầu ra

- [x] Prompt registry — PostgreSQL, 6 version, p1 active.
- [x] 6 prompt variants — P0 naive / P1 grounded / P2 citation-first / P3 refusal-aware / P4 self-check / P5 concise.
- [x] Prompt comparison report — `experiments/results_prompt_comparison.md` + CSV (run `promptcmp_20260711_1408`, chạy THẬT 6×12 câu qua Gemini).

### Kiểm tra dự kiến

```bash
python scripts/seed_prompts.py
python scripts/run_prompt_comparison.py            # 12 câu smoke cố định
pytest tests/unit/test_prompt_renderer.py tests/integration/test_prompt_registry.py
```

### Definition of Done

- [x] Runtime không dùng prompt hard-code — template resolve từ registry lúc khởi động; activation bị chặn nếu chưa có eval_result_id (trừ override có log).
- [x] Prompt version xuất hiện trong trace — `trace.prompt_version` lấy từ registry.
- [x] Có prompt comparison report — kết quả: **p1_grounded_v1 thắng** (refusal 1.00, grounded 1.00, 83.4 token TB), activate theo số liệu thay bootstrap override.

### Rủi ro

- Prompt registry quá phức tạp: bắt đầu bằng PostgreSQL table + templates. *(Đúng như vậy — 1 bảng + 1 module, không thêm framework.)*

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** activation policy enforce trong
code (không activate được nếu thiếu eval evidence, override phải có log);
mọi variant chung JSON contract nên so sánh được công bằng qua cùng
parser; phát hiện phản trực giác từ số liệu thật (citation-first làm HỎNG
refusal 0.00; refusal-aware 0.75 thua grounded thường 1.00) — đúng tinh
thần "chọn bằng số liệu, không cảm tính", và là material tốt cho báo cáo.

**Còn thiếu, cần quay lại:**
- ~~Smoke set 12 câu là quá nhỏ để kết luận chắc... Phase 8 phải chạy lại
  6 variant~~ → **Đã chạy lại (2026-07-14)**, xem
  `experiments/results_prompt_comparison_p8.md`: cả 5 variant còn lại
  (p0/p2/p3/p4/p5, p1 đã archived từ lâu) chạy qua Evaluation Engine đầy
  đủ (50 câu smoke/variant, retrieval thật + LLM-judge 4 tiêu chí, 0%
  fallback contamination cả 6 lần chạy — số liệu sạch). Kết luận Phase 6
  ĐƯỢC XÁC NHẬN LẠI bằng dữ liệu lớn hơn nhiều (p0 baseline yếu đúng thiết
  kế: Refusal Acc 0.740, Hallucination 0.293; p2/p3/p4 đều dưới target
  Refusal Acc 0.90). **Phát hiện mới quan trọng:** `p5_concise_v1` cạnh
  tranh rất sát bản production `p7_citation_complete_safe_v1` — THẮNG ở
  Faithfulness (0.963 vs 0.950) và Hallucination (0.075 vs 0.100), hoà
  Refusal Accuracy (0.900) và Error rate (0.000), chỉ thua nhẹ ở Citation
  Accuracy (0.819 vs 0.838, cả 2 đều dưới target 0.85). Xác nhận đúng gợi
  ý bỏ ngỏ từ Phase 6 ("ứng viên cost-aware chờ Phase 8 xác nhận") — p5
  không đánh đổi chất lượng đáng kể để giảm token. **Không activate** (đúng
  policy, cần eval_result_id + xác nhận người dùng) — ghi nhận làm gợi ý
  hướng cải thiện tương lai ("p8 = quy tắc citation của p7 + phong cách
  p5"), chưa implement.
- **Comparison chưa đo faithfulness/answer-relevance** (cần LLM-judge,
  Phase 8) — grounded_citation_rate mới là proxy (citation trúng
  relevant_chunks), chưa đánh giá nội dung answer đúng/sai. *(Đã giải
  quyết cùng lúc với mục trên — `results_prompt_comparison_p8.md` có đủ
  cả 2 số liệu này qua LLM-judge thật.)*
- **`POST /prompts/{id}/compare` (contract) chưa có dạng HTTP** — chạy
  offline qua script vì 72 lượt LLM không hợp request đồng bộ; thành job
  async khi có eval engine (Phase 8).
- **RegistryPromptProvider cache active prompt đến khi restart server** —
  activate version mới cần restart để runtime nhận; chấp nhận được ở dev,
  Phase 9 (quality gate + deploy flow) nên thêm reload/TTL.
- **prompts.yaml `active_version` giờ chỉ mang tính tài liệu** — có rủi
  ro lệch với registry nếu quên cập nhật tay; cân nhắc bỏ hẳn field này
  hoặc thêm check đồng bộ trong CI.

---

## Phase 7 - Xây Model Gateway (Tuần 12)

### Mục tiêu

Đưa mọi model call qua LiteLLM/model gateway, có routing, fallback, budget và rate limit.

### Tài liệu cần đọc

- [modules/03_rag_runtime_model_gateway.md](modules/03_rag_runtime_model_gateway.md)
- [modules/08_optimization_routing.md](modules/08_optimization_routing.md)
- [contracts/config_schemas.md](contracts/config_schemas.md)

### Task

- [x] Cấu hình LiteLLM — `docker-compose.yml` service `litellm` (ghcr.io/berriai/litellm:main-stable), healthcheck qua `/health/liveliness`.
- [x] Tạo gateway config — `config/litellm_config.yaml`: 12 model_list entry (4 tier × 3 chặng fallback).
- [x] Implement model tier: cheap/balanced/strong/judge — mirror đúng `config/model_gateway.yaml` đã có từ Phase 1/2.
- [x] Implement fallback — Gemini key 1 → Gemini key 2 → **Ollama local** (`qwen2.5:7b`, `host.docker.internal`). Verify thật bằng container cô lập với key giả: cascade qua cả 2 Gemini lỗi, rơi xuống Ollama thành công.
- [x] Implement timeout policy — `router_settings.timeout: 30` (khớp `default_timeout_seconds` model_gateway.yaml), `cooldown_time: 60`, `allowed_fails: 1`.
- [x] Implement cost tracking — đọc thật từ header `x-litellm-response-cost` (giá niêm yết, không phải phí thật vì đang free tier), không tự tính.
- [x] Implement budget warning — so `cumulative_cost_usd` (tích luỹ trong tiến trình server) với `budget.daily_usd`, gắn `error_labels: ["budget_warning"]` khi vượt.
- [x] Integrate runtime với gateway — `src/rag/litellm_gateway.py::LiteLLMGateway` thay `GeminiGateway` (Phase 5) trong `src/api/routes/qa.py`.

**Bug thật phát hiện khi test fallback cascade:** khai `fallbacks:
{primary: [secondary, local]}` (list 2 phần tử trong 1 dòng) KHÔNG hoạt
động như tưởng — LiteLLM không tự nối tiếp danh sách khi secondary cũng
lỗi. Phải khai 2 chặng riêng (`primary: [secondary]`,
`secondary: [local]`). Chi tiết + lý do trong `litellm_config.yaml` và
`modules/03_rag_runtime_model_gateway.md`.

### Đầu ra

- [x] Runtime gọi model qua gateway — verify thật qua `/qa/debug`, response `model.provider="litellm"`.
- [x] Gateway route/fallback report — trace ghi `fallback_hop`/`attempted_fallbacks`/`cost_usd`/`cumulative_cost_usd` mỗi request.

### Kiểm tra dự kiến

```bash
docker compose up -d litellm
pytest tests/integration/test_litellm_gateway.py   # tự skip nếu proxy tắt
uvicorn src.api.main:app --port 8000
curl -X POST http://localhost:8000/qa/debug -d @question.json
```

### Definition of Done

- [x] Không còn direct provider call trong runtime — `qa.py`/`service.py` chỉ biết `Gateway` protocol, không import Gemini SDK nữa (script Phase 3/4/6 offline vẫn dùng SDK trực tiếp có chủ đích, xem "Chưa tốt").
- [x] Fallback test pass — verify thủ công bằng container cô lập (key Gemini giả → cascade tới Ollama thành công, 1.6s) + 3 test tự động cho nhánh Gemini thật (`tests/integration/test_litellm_gateway.py`).
- [x] Cost/token log xuất hiện trong trace — `cost_usd`, `cumulative_cost_usd`, `input_tokens`, `output_tokens` verify thật qua `GET /qa/traces/{id}`.

### Rủi ro

- Provider key thiếu: test gateway bằng mock trước. *(MockGateway Phase 5 vẫn giữ cho unit test; integration test dùng proxy thật.)*
- Cost tăng: dùng cheap model cho smoke. *(Free tier hiện tại cost thật = 0; budget warning đã có sẵn cho khi hết free tier.)*

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** verify fallback bằng container cô
lập với key giả (không đụng service đang chạy thật) — phát hiện đúng 1
bug cấu hình thật (list fallback không tự nối tiếp) mà chỉ đọc doc sẽ
không thấy; chọn model Ollama bằng đo thật trên phần cứng thay vì tin
benchmark chung chung (qwen3:4b tốt hơn trên giấy nhưng thua qwen2.5:7b
trên máy này).

**Còn thiếu, cần quay lại:**
- **Test fallback-tới-Ollama chưa tự động hoá được** trong
  `tests/integration/` — verify bằng container Docker cô lập thủ công
  (key giả), không chạy được trong CI vì cần Ollama chạy trên host thật.
  Cân nhắc: mock Ollama endpoint bằng WireMock hoặc tách thành 1 test
  đánh dấu `@pytest.mark.manual`.
- **Streaming chưa expose ra runtime** dù LiteLLM proxy đã hỗ trợ ở tầng
  dưới — `Gateway.generate()` vẫn là request/response đồng bộ. Chưa
  phase nào cần UX streaming thật nên để lại.
- **`cost_usd` là giá niêm yết, không phải phí thật đã trả** (đang free
  tier) — dùng được để CẢNH BÁO ngân sách nhưng không dùng được để báo
  cáo "đã chi bao nhiêu" trong báo cáo khóa luận mà không chú thích rõ.
- **`cumulative_cost_usd` reset về 0 mỗi khi restart server** — không
  bền qua nhiều lần chạy; Phase 10 (Langfuse) mới có cost tracking bền
  vững qua thời gian.
- ~~Ollama fallback chỉ test với 1 câu hỏi đơn giản, chưa biết chất lượng
  trên câu phức tạp~~ → **Đã có câu trả lời thật (Phase 8 full eval,
  2026-07-12):** khi bị dùng thật trên 35 câu, Ollama fallback có
  refusal_accuracy chỉ 0.457 (so với 0.962 trên đường Gemini) vì hay trả
  citation không hợp lệ — xem CHECKLIST Phase 8.
- **litellm image `main-stable`** không pin version cụ thể — lần build
  lại sau có thể kéo bản khác, rủi ro nhỏ về reproducibility; nên pin tag
  version cụ thể khi ổn định.
- **Thêm chặng fallback thứ 3 (`tertiary`, `GEMINI_API_KEY_5`) cho cả 4
  tier (2026-07-12)** — cả primary lẫn secondary cạn quota ngày cùng lúc
  khi chạy liên tiếp nhiều eval thật trong 1 ngày (Phase 8), 2 key không
  đủ dự phòng. Cùng bài học Phase 4/6: mỗi key nên ở project Google khác
  nhau để có ngân sách quota độc lập thật, không chỉ khác tên biến môi
  trường.

---

## Phase 8 - Xây Evaluation Engine (Tuần 13-14)

### Mục tiêu

Chạy đánh giá 4 tầng trên smoke/full set và xuất report.

### Tài liệu cần đọc

- [modules/05_evaluation_engine.md](modules/05_evaluation_engine.md)
- [contracts/metric_definitions.md](contracts/metric_definitions.md)
- [experiments/result_reporting_template.md](experiments/result_reporting_template.md)

### Task

- [x] Implement golden set loader — `src/evaluation/golden_set.py`: `select(mode, category)` với 3 mode (`smoke`=50 câu stratified theo category thật/`full`=300/`targeted`=lọc theo category), `smoke_subset()` seed cố định để tái lập.
- [x] Implement retrieval metrics — tái dùng nguyên `src/retrieval/metrics.py` (Phase 4, không viết lại): recall@k/hit/MRR/nDCG dạng citation-coverage.
- [x] Implement context metrics — `src/evaluation/metrics.py`: `context_precision()` (chunk thật retrieve / có liên quan), `context_recall` alias trực tiếp `recall_at_k`, `context_relevance` qua judge.
- [x] Implement generation metrics — faithfulness/answer_relevance/context_relevance/hallucination qua judge (`src/evaluation/judge.py`), citation accuracy + refusal accuracy tính thẳng (deterministic, không cần judge).
- [x] Implement citation accuracy — `src/evaluation/metrics.py::citation_accuracy()` (citation model thực sự trích có đúng nhóm citation kỳ vọng không, khác với validate "chunk có thật" đã có ở `src/rag/citation.py` Phase 5).
- [x] Implement refusal accuracy — `runner.py::run_question()` so `resp.refusal` với `item["requires_refusal"]` trực tiếp.
- [x] Integrate LLM judge — `src/evaluation/judge.py::GeminiJudge`, gọi qua tier `judge` có sẵn trong `config/model_gateway.yaml`/`litellm_config.yaml` (chưa dùng tới trước Phase 8), rubric 1 lệnh gọi chấm cả 4 tiêu chí, cache theo hash (question, answer, context) — `data/eval/judge_cache_<data_version>.json`.
- [x] Implement eval report — `src/evaluation/report.py`: CSV per-câu + Markdown tổng hợp/theo-category/failure-case, cùng pattern CSV+Markdown Phase 4 (MLflow/DVC nêu trong module doc chưa từng được nối dây thật ở bất kỳ phase nào — ghi đúng cái có thật).
- [x] Export failure cases — `report.py::_failure_cases()`: gom câu refusal sai/retrieval miss/citation sai/faithfulness<1/hallucination/judge lỗi parse, tối đa 30 câu trong report.
- [x] Run smoke eval — `python scripts/run_evaluation.py --mode smoke`, 50 câu thật qua RagService thật (Phase 5-7, LiteLLM proxy + Qdrant thật, không mock). Kết quả: xem `docs/system/experiments/results_evaluation_smoke.md`.
- [x] Run full eval — `python scripts/run_evaluation.py --mode full`, 298/300 câu chạy thật (2 câu lỗi mạng transient, không phải bug), 3232s (~54 phút). Kết quả: `docs/system/experiments/results_evaluation_full.md`. **Phát hiện vận hành quan trọng giữa run:** cả 2 key Gemini cạn quota gần cuối (dùng chung ngân sách ngày với smoke + Phase 4 trước đó) → LiteLLM tự rơi xuống Ollama local cho 35/298 câu cuối, làm nhiễu số liệu tổng hợp (xem "Chưa tốt").

### Đầu ra

- [x] Eval reports — `docs/system/experiments/results_evaluation_smoke.md` + `results_evaluation_full.md`.
- [x] Failure cases — mục "Failure cases" trong report.
- [x] Baseline metrics — bảng "Kết quả tổng hợp" so với target `contracts/metric_definitions.md`.

### Kiểm tra dự kiến

```bash
python scripts/run_evaluation.py --mode smoke
python scripts/run_evaluation.py --mode full
```

### Definition of Done

- [x] Smoke eval 50 câu chạy được — chạy thật, xem report.
- [x] Full eval 300 câu chạy được — chạy thật 298/300 câu (2026-07-12), xem `results_evaluation_full.md`.
- [x] Eval result có metric đủ 4 tầng — retrieval/context/generation/operations đều có số thật trong report (riêng `cache_hit_rate` báo `n/a` trung thực vì semantic cache chưa implement trong RAG runtime, không thuộc scope Phase 8).
- [x] Có failure case report.

### Rủi ro

- Eval tốn tiền: judge sampling, cache judge outputs. *(Free tier hiện cost=0 thật; rủi ro thật sự đo được là RATE LIMIT/thời gian chạy, không phải tiền — xem "Chưa tốt".)*

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** chạy eval qua `RagService` thật
(Phase 5-7 nguyên trạng, không tách bản sao logic riêng cho eval) — số
liệu phản ánh đúng cái user thật sự nhận được, không thể âm thầm lệch
khỏi runtime production như một bộ eval viết riêng dễ mắc phải; judge
rubric dùng thang rời rạc {0.0, 0.5, 1.0} thay vì điểm liên tục — giảm
nhiễu tự-chấm-không-nhất-quán của LLM-judge, đánh đổi lấy độ mịn.

**Còn thiếu, cần quay lại:**
- ~~Full eval xác nhận Citation Accuracy là gap thật ở multi_hop
  (0.625)/ambiguous (0.452)~~ → **Đã điều tra + xử lý một phần
  (2026-07-12), xem `results_prompt_comparison_p6.md`.** Điều tra sâu (đọc
  trace thật + đối chiếu retrieval) tìm ra 2 nguyên nhân riêng biệt, không
  chỉ 1:
  1. **Lỗi dữ liệu golden set thật** — 6 câu (q_016-q_021) trích dẫn
     `doc_tqa_phuc_khao` (trang tóm tắt, chỉ khớp lexical yếu) trong khi
     nội dung y hệt có sẵn ở `doc_qd610_thi_danh_gia` (văn bản gốc, khớp
     structural chính xác) — model trích ĐÚNG nguồn gốc nhưng bị chấm sai.
     Đã sửa citation source cho cả 6 câu. **Phát hiện phụ:** q_021's
     ground_truth SAI thật ("Trưởng bộ môn" thay vì đúng là "GV giảng
     dạy" theo Điều 26 Khoản 2.b) — hệ thống đã trả lời đúng hơn cả
     ground_truth cũ, xác nhận qua `data/traces/traces.jsonl`. Đã sửa.
  2. **Model over-cite/wrong-pick và bỏ sót citation ở câu nhiều vế** —
     nguyên nhân prompt thật. Đã thêm variant `p6_citation_complete_v1`
     với quy tắc citation chặt hơn. So sánh thật (không mock) trên
     multi_hop (n=30) và ambiguous (n=20): Citation Accuracy
     +0.028/+0.084, Refusal Accuracy +0.033/+0.100, không hồi quy ở
     factoid (n=36, mẫu lớn nhất) hay category khác — xem
     `results_prompt_comparison_p6.md` đầy đủ. **ĐÃ ACTIVATE
     (2026-07-12)** — auto-mode classifier chặn activate tự động lần đầu
     (đúng chủ đích, coi là production deploy vượt phạm vi yêu cầu gốc),
     user xác nhận qua AskUserQuestion → activate qua
     `PromptRegistry.activate()`, verify thật qua `RagService` (câu hỏi
     mẫu trả lời đúng, `prompt_version=p6_citation_complete_v1` trong
     response). `p1_grounded_v1` archived tự động theo policy registry
     (1 active/prompt_id).
  - Citation Accuracy vẫn CHƯA đạt target 0.85 kể cả với p6 — cải thiện
    thật nhưng chưa triệt để; phần gap còn lại nhiều khả năng cần fix ở
    tầng retrieval (multi-hop cần re-retrieval theo từng hop, ngoài phạm
    vi 1 lần sửa prompt), không chỉ prompt.
  3. **Thử tăng `top_k_after` (5->10) — THỬ VÀ ĐÃ REVERT, kết quả âm
     tính có giá trị.** Retrieval-only (249 câu, $0 API) cho thấy recall
     tăng đơn điệu mọi category khi tăng limit — nhưng đo THẬT qua
     generation (multi_hop, chạy sạch không dính Ollama fallback) cho
     kết quả NGƯỢC: Citation Accuracy GIẢM 0.700->0.650 (nhiều chunk hơn
     = nhiều distractor hơn cho model, dễ trích nhầm hơn dù chunk đúng
     "có mặt" nhiều hơn). Đã revert `top_k_after` về 5. Bài học: số liệu
     retrieval-only không đủ để đổi production config, luôn cần đo thêm
     qua generation thật — 2 tầng có thể phản ứng ngược hướng nhau với
     cùng 1 thay đổi. Chi tiết:
     `docs/system/experiments/results_context_limit_ablation.md`.
  4. **Full eval lại với p6 (300 câu) phát hiện 1 HỒI QUY THẬT mà p6 gây
     ra** — Refusal Accuracy nhóm `adversarial` tụt từ 0.909 (p1) xuống
     0.636 (p6): 3 câu (q_054, q_151, q_197) mà p1 từ chối đúng thì p6
     lại trả lời có căn cứ (KHÔNG bịa, model vẫn từ chối đúng bản chất —
     ví dụ đọc trace q_054 model trả lời "Rất tiếc, tôi không thể đáp
     ứng yêu cầu này vì..." kèm trích dẫn thật) nhưng QUÊN đặt cờ
     `refusal:true`, vì quy tắc citation chặt hơn của p6 khiến model dễ
     tìm được đoạn liên quan để giải thích lý do từ chối bằng answer có
     căn cứ thay vì dùng nhánh refusal. **Đã sửa bằng
     `p7_citation_complete_safe_v1`** — thêm quy tắc tường minh: yêu cầu
     vi phạm chính sách/an toàn LUÔN đặt refusal=true bất kể có trích
     dẫn được hay không. Verify thật: **11/11 adversarial + 9/9
     out_of_scope = 1.000 refusal accuracy** (kể cả q_198, câu mà CẢ p1
     LẪN p6 đều sai). **ĐÃ ACTIVATE (2026-07-12)** — user xác nhận qua
     AskUserQuestion, `PromptRegistry.activate()` thành công, verify
     live qua `RagService` (câu hỏi giả danh quản trị viên đòi điểm số
     SV khác → `refusal=true` đúng). `p6_citation_complete_v1` archived.
     `p7_citation_complete_safe_v1` giờ là prompt production.
  5. **Per-hop retrieval cho multi-hop (2026-07-14) — THỬ, ĐO THẬT, VÀ ĐÃ
     REVERT, kết quả âm tính rõ ràng qua 3 lần chạy có kiểm soát.**
     Giả thuyết: decompose câu hỏi multi-hop thành 2-3 sub-query, retrieve
     riêng từng sub-query rồi merge, sẽ tránh việc 1 chunk chỉ liên quan
     tới 1 vế bị "chìm" khi query gộp làm loãng trọng số. Implement xong
     (`src/retrieval/multi_hop.py`: heuristic `looks_multi_hop()` bắt
     28/30 câu multi-hop thật với 40% false-positive trên factoid — chấp
     nhận được vì false trigger chỉ tốn thêm latency, không sai kết quả;
     `decompose_query()` qua tier `cheap`; merge/dedupe), 13 unit test +
     2 integration test pass, wiring vào `RagService` xong.
     **Verify thật trên đúng 30 câu multi_hop (không phải giả lập),
     3 lần chạy có kiểm soát (cùng ngày, cùng prompt p7, cùng data):**
     | Biến thể | Recall@5 | Citation Acc | Hallucination |
     |---|---:|---:|---:|
     | **Baseline (single-query, không đổi gì)** | **0.856** | **0.684** | 0.276 |
     | Per-hop v1 (merge theo raw score) | 0.767 | 0.606 | 0.200 |
     | Per-hop v2 (merge round-robin, sửa bug v1) | 0.739 | 0.650 | 0.233 |
     Phát hiện phụ: merge theo raw score (v1) là 1 bug thật — DBSF fused
     score không so được giữa 2 query khác nhau (chuẩn hoá theo pool ứng
     viên riêng của từng query, không phải thang tuyệt đối chung), khiến
     1 sub-query "nuốt" hết chỗ của sub-query kia. Sửa bằng round-robin
     interleaving theo rank trong từng hop (v2) — cải thiện so v1 nhưng
     **vẫn thua baseline ở cả 2 chỉ số quan trọng nhất**. Kết luận thật:
     retrieval hybrid DBSF hiện tại xử lý câu multi-clause TỐT HƠN 2-3
     query tách rời rồi ghép lại — decompose làm mất tín hiệu đồng-xuất-hiện
     giữa các vế câu hỏi gốc mà 1 query gộp (dense+sparse) vẫn giữ được.
     **Đã revert hoàn toàn**: gỡ wiring khỏi `src/rag/service.py`, xoá
     `src/retrieval/multi_hop.py` + test liên quan (theo đúng tinh thần
     "no half-finished/unused code" — giữ code chết không dùng không có
     giá trị hơn giữ lại phát hiện này bằng văn bản). Gap Citation Accuracy
     multi-hop **vẫn còn treo thật** — per-hop retrieval không phải hướng
     đúng; hướng khả dĩ khác (chưa thử): cải thiện PROMPT để model tự
     liệt kê đủ số vế cần trả lời trước khi cite (gần với p6/p7 đã làm
     nhưng có thể cần rõ ràng hơn nữa), hoặc tăng `top_k_after` CHỈ cho
     multi-hop (đã biết tăng chung cho mọi câu hỏi có hại — item 3 ở trên).
- **Refusal Accuracy: kết quả full eval THỰC RA TỐT HƠN smoke đáng kể khi
  đọc đúng cách** — số tổng hợp thô 0.903 (đạt target 0.90) nhưng bị
  nhiễu bởi 35/298 câu cuối run bị fallback (xem mục tiếp theo); tách
  riêng đường primary (263 câu, 88% run) cho **Refusal Accuracy = 0.962
  — vượt xa target và vượt cả số đo smoke (0.880)**. Kết luận: refusal
  policy hiện tại (`src/rag/service.py` 2 lớp pre/post-LLM) hoạt động tốt
  hơn con số smoke ban đầu cho thấy; gap ở smoke nhiều khả năng là nhiễu
  mẫu nhỏ (chỉ 50 câu) chứ không phải vấn đề hệ thống — không cần sửa
  gấp, nhưng vẫn nên theo dõi thêm ở lần chạy tiếp theo.
- **Phát hiện vận hành quan trọng: full eval 300 câu liên tục trong 1
  phiên (~54 phút) làm cạn quota NGÀY của cả 2 Gemini key** (dùng chung
  ngân sách với smoke eval + Phase 4 chạy trước đó cùng ngày) — LiteLLM
  proxy tự động fallback: 16 câu qua secondary key, **19 câu rơi hẳn
  xuống Ollama local**, đúng thiết kế Phase 7 nhưng bị lộ ra 1 vấn đề
  thật: **Ollama local hay trả JSON có citation không hợp lệ** →
  `citation.py` tự hạ thành refusal (đúng chính sách fail-closed, không
  phải bug) → refusal_accuracy của riêng nhóm fallback chỉ **0.457** và
  p95 latency **23.7 giây** (so với 1.49s ở primary). Đây là bằng chứng
  thật đầu tiên cho câu hỏi treo từ Phase 7 "Ollama fallback chỉ test 1
  câu đơn giản, chưa biết chất lượng trên câu phức tạp" — giờ đã có câu
  trả lời: **chất lượng citation-grounding của Ollama fallback kém hơn
  đáng kể Gemini trên domain IUH thật**, cần cân nhắc nới lỏng
  `require_citation` hoặc cải thiện prompt riêng cho hop fallback local
  nếu muốn fallback thật sự "thành công" chứ không chỉ "không crash".
  `src/evaluation/report.py` đã được vá thêm bảng tách primary/fallback
  tự động cho lần chạy sau (`_fallback_note()`), không cần vá tay report
  nữa. **Điều tra + fix một phần (2026-07-13):** gọi thẳng Ollama
  `qwen2.5:7b` (bỏ qua LiteLLM, không tốn quota Gemini) với đúng prompt
  thật (5 chunk, ~3800 token) tái hiện được lỗi: model KHÔNG chép nguyên
  văn `chunk_id` dài (`chunk_doc_qd1482_..._structure_aware_0060`) mà tự
  rút gọn thành hậu tố số (`"0060"`). Test cả `num_ctx=4096` (giá trị
  đang cấu hình) lẫn `8192` cho kết quả GIỐNG HỆT → loại trừ giả thuyết
  tràn context-window, xác nhận đây là hạn chế thật của model 7B khi phải
  chép nguyên văn 1 chuỗi dài, không phải lỗi cấu hình. **Fix:**
  `src/rag/citation.py::_resolve_chunk_id()` thêm bước suffix-match — hậu
  tố mô hình trả về CHỈ được chấp nhận khi khớp DUY NHẤT 1 chunk trong tập
  đã retrieve cho đúng request đó (không tra toàn corpus, tránh biến model
  yếu thành nguồn trích dẫn sai), unit test tái hiện đúng chuỗi thật đã
  quan sát (`tests/unit/test_citation_parser.py`). Đây là fix parser-side,
  RẺ hơn viết prompt/policy riêng cho local hop; **chưa đo lại được số
  refusal_accuracy/citation_accuracy thật của nhóm fallback sau fix** (cần
  1 lần chạy thật rơi xuống Ollama đủ nhiều câu để so sánh trước/sau, chưa
  làm trong lần sửa này) — ghi nhận là cải thiện có căn cứ nhưng CHƯA có
  số đo full trước/sau, không bịa số so sánh.
- **Bài học lịch chạy:** nên chạy full eval vào đầu ngày (trước khi dùng
  quota cho việc khác) hoặc tách thành nhiều phiên nhỏ hơn trong ngày để
  tránh đúng kiểu nhiễu đã gặp ở lần chạy này.
- **Phát hiện vận hành thứ 2 (2026-07-13, nặng hơn lần đầu): 1 lần chạy
  smoke bổ sung `--second-judge` bị nhiễu 100%** — `fallback_rate=1.000`,
  `error_rate=1.000` trong `results_evaluation_smoke.md`: TOÀN BỘ 50 câu
  (không riêng phần cuối như lần trước) bị phục vụ bởi hop không phải
  primary, vì chạy sau khi đã dùng nhiều quota trong ngày cho việc khác
  (ingest lại + test + calibrate) CỘNG THÊM judge phụ tự nó tốn gấp đôi
  lượt gọi judge/câu. Run mất **~22 phút cho 44/50 câu** (nhiều câu bị
  timeout ở primary/secondary/tertiary trước khi rơi xuống Ollama local,
  1 câu treo ~14 phút riêng lẻ) — chậm hơn nhiều so với full eval 300 câu
  trước đó (~54 phút TOÀN BỘ). Số liệu tổng hợp (Refusal Accuracy 0.409,
  Hallucination Rate 0.100) KHÔNG phản ánh chất lượng hệ thống ở điều kiện
  bình thường, chỉ phản ánh chất lượng Ollama fallback dưới tải — đọc cùng
  với 2 mục "Đã thêm judge thứ 2"/"Đã thêm metric ambiguous" phía dưới với
  cùng mức dè dặt. Bài học bổ sung: **`--second-judge` nên chạy RIÊNG, đầu
  ngày, tách khỏi các việc tốn quota khác trong cùng phiên** — không nối
  tiếp sau ingest/test/calibrate như lần này.
- **`judge_sample`/`human_review` mode (nêu trong `modules/05_evaluation_engine.md`)
  chưa implement riêng** — `smoke` (stratified fixed-size) dùng tạm cho
  cả 2 mục đích "chạy nhanh" và "review mẫu", chưa có cách chọn N câu
  random để judge trên một `full` run đã có sẵn kết quả retrieval.
- **RAGAS/DeepEval không tích hợp** (task gốc trong module doc) — dùng
  custom judge (Gemini qua gateway `judge` tier) thay vì thư viện có sẵn.
  Lý do: RAGAS baseline hướng tiếng Anh, cần validate lại prompt/parser
  cho tiếng Việt; custom judge kiểm soát được rubric và cache, chi phí
  triển khai thấp hơn debug RAGAS với model tiếng Việt free-tier. Ghi
  nhận là lựa chọn có chủ đích, không phải thiếu sót quên làm.
- ~~Ambiguous category (20 câu, `requires_clarification=True`) không có
  cơ chế đánh giá riêng~~ → **Đã thêm metric (2026-07-13):**
  `src/evaluation/metrics.py::ambiguity_handled()` — heuristic văn bản
  (không tốn thêm lệnh judge), True nếu answer hỏi lại người dùng làm rõ
  HOẶC bao quát nhiều nhánh điều kiện (>=2 marker `nếu/trường hợp/tùy/
  hoặc/...`), False nếu chốt 1 nhánh duy nhất như thể chắc chắn. Cột
  "Ambiguity handled" mới trong report theo-category
  (`src/evaluation/report.py`). **Chưa đo được số thật sạch** — run
  `results_evaluation_smoke.md` (2026-07-13) dùng để verify code chạy
  đúng lại bị nhiễu nặng (xem mục dưới): cả 2 câu ambiguous trong mẫu 50
  đều rơi vào refusal do lỗi citation Ollama fallback trước khi tới bước
  tính ambiguity_handled (code chỉ tính khi `not refusal`) → n=0 câu đo
  được trong lần chạy này. Hệ thống XÁC NHẬN THẬT vẫn KHÔNG có prompt/cơ
  chế hỏi lại làm rõ (`src/promptops/templates.py`) — cần chạy lại
  `--mode targeted --category ambiguous` (20 câu) vào lúc quota Gemini
  còn dư để có số liệu sạch.
- ~~Context relevance/faithfulness/answer_relevance/hallucination đều từ
  1 judge model duy nhất~~ → **Đã thêm judge thứ 2 (2026-07-13):**
  `scripts/run_evaluation.py --second-judge` chấm thêm bằng tier `cheap`
  (gemini-3.1-flash-lite) song song judge chính (tier `judge`,
  gemini-3-flash-preview) trên CÙNG (question, answer, context);
  `src/evaluation/runner.py::inter_judge_agreement()` tính mean-abs-diff +
  exact-match-rate mỗi tiêu chí, hiển thị ở report (mục "Inter-judge
  agreement"). Cả 2 vẫn là Gemini (chưa có key OpenAI/Anthropic) — so
  sánh model MẠNH/NHẸ cùng provider, không phải đa dạng provider thật.
  **Số liệu thật lần đầu (smoke, 2026-07-13, xem mục "Phát hiện vận hành"
  dưới để hiểu bối cảnh nhiễu):** n=10 cặp — faithfulness mean-abs-diff
  0.500/exact-match 0.500, answer_relevance 0.450/0.500,
  context_relevance 0.500/0.500, hallucination-agreement 1.000. Đọc với
  RẤT NHIỀU dè dặt: mẫu quá nhỏ (10/50) và TOÀN BỘ run bị fallback (không
  câu nào phục vụ bởi model primary) nên đây không phải phép đo agreement
  ở điều kiện vận hành bình thường — cần chạy lại lúc quota sạch để có số
  đáng tin.
- **`cost_usd` trong report kế thừa hạn chế đã ghi ở Phase 7** (giá niêm
  yết free-tier, không phải phí thật đã trả) — `avg_cost_usd` trong eval
  report có cùng hạn chế, không dùng trực tiếp cho báo cáo "đã chi bao
  nhiêu" khóa luận mà không chú thích.

### Ghi chú lệch thứ tự phase (2026-07-12)

Theo yêu cầu trực tiếp của user, **frontend Next.js (thuộc scope Phase
12 gốc) bắt đầu xây ngay sau Phase 8**, TRƯỚC Phase 9-11 (Quality Gate,
Observability, Feedback Loop) — không theo đúng thứ tự tuần đã lên kế
hoạch. Lý do: user muốn có giao diện trực quan sớm để thấy được toàn
cảnh project. Đây là ngoại lệ có chủ đích, không phải bỏ qua Phase 9-11
— các phase đó vẫn cần làm đầy đủ sau, và frontend/dashboard sẽ cần cập
nhật thêm khi có số liệu Quality Gate/Observability/Feedback (Phase
9-11) sau này. Xem `docs/system/modules/10_frontend_showcase.md`.

**Build thật hoàn tất (2026-07-12), verify không chỉ viết code:**
`frontend/` scaffold Next.js 16 + React 19 + Tailwind v4, cài Motion/
GSAP/Lenis/shadcn (Base UI). 3 trang thật (`/`, `/demo`, `/dashboard`),
số liệu dashboard transcribe từ report thật (không tính lại công thức
khác). `npx tsc --noEmit` + `npm run lint` + `npm run build` đều sạch.
`/demo` verify thật: `curl -X POST /qa/query` qua CORS preflight
(`access-control-allow-origin` đúng) trả lời đúng câu hỏi tín chỉ + trích
dẫn đúng Điều 6 Khoản 4. **Phát hiện thật đáng ghi lại:** shadcn/ui bản
cài dùng **Base UI**, không phải Radix UI như quen thuộc — `asChild`
không tồn tại, phải dùng `buttonVariants()` trực tiếp trên `<Link>` (xem
`frontend/AGENTS.md` cảnh báo trước, và mục "Lỗi thường gặp" trong
`modules/10_frontend_showcase.md`). **Còn treo:** chưa verify bằng mắt
độ mượt animation cuộn trang (không có công cụ screenshot/browser trong
phiên làm việc) — user cần tự mở `localhost:3000` xác nhận trước khi
dùng làm demo chính thức bảo vệ khóa luận.
**Re-verify 2026-07-13** (không có thay đổi code frontend nào trong lần
sửa này, chỉ xác nhận lại chưa hỏng gì): `npx tsc --noEmit` + `npm run
lint` + `npm run build` vẫn sạch, `npm run dev` khởi động lại thành công,
cả 3 route (`/`, `/demo`, `/dashboard`) trả 200, log dev server không có
lỗi hydration/runtime. Vẫn KHÔNG có công cụ screenshot/browser trong môi
trường làm việc để verify độ mượt animation bằng mắt — giữ nguyên caveat
trên, chưa gỡ được.

---

## Phase 9 - Xây CI/CD Quality Gate (Tuần 15-16)

### Mục tiêu

Quality gate quyết định PASS/WARN/BLOCK cho thay đổi prompt/model/data/retrieval/code.

### Tài liệu cần đọc

- [modules/06_quality_gate_cicd.md](modules/06_quality_gate_cicd.md)
- [contracts/config_schemas.md](contracts/config_schemas.md)
- [operations/testing_strategy.md](operations/testing_strategy.md)

### Task

- [x] Tạo `quality_gate.yaml` — `config/quality_gate.yaml`, threshold khớp `src/evaluation/report.py::TARGETS` (tránh 2 nơi lệch nhau).
- [x] Implement gate decision logic — `src/qualitygate/gate.py::evaluate_gate()`, pure function trên aggregate dict, không đụng Qdrant/Postgres/LiteLLM.
- [x] Implement baseline comparison — regression check (`regression.max_quality_drop`) chạy riêng với threshold check tuyệt đối; BLOCK nếu 1 trong 2 vi phạm, kể cả khi metric còn trên ngưỡng tuyệt đối.
- [x] Implement gate report — `src/qualitygate/report.py::write_markdown()`, cùng pattern CSV/Markdown-không-dashboard-tool của Phase 8.
- [x] Add GitHub Actions workflow — job `lint-test` giờ chạy `test_quality_gate.py` (logic thuần, không cần service); job `quality-gate-live` (smoke eval thật + gate trong CI) mới ở dạng comment, xem "Chưa tốt".
- [x] Chạy 16 thay đổi giả lập — `tests/unit/test_quality_gate.py::SIMULATED_CHANGES` (9 xấu/4 warning/3 tốt).
- [x] Đo true positive/false negative — `test_16_simulated_changes_suite`: 9/9 thay đổi xấu bị BLOCK đúng (true positive), 0 false negative.
- [x] Chỉnh threshold — không cần chỉnh, threshold gốc từ contracts/report.py TARGETS pass thẳng test đầu tiên.

### Đầu ra

- [x] Quality gate CLI — `scripts/check_gate.py` (`--eval-run`/`--baseline`/`--mode --latest`).
- [x] GitHub Actions workflow — cập nhật `.github/workflows/ci.yml` (phần thật đã chạy; phần live-eval-in-CI còn comment, xem "Chưa tốt").
- [x] Gate report — Markdown, `docs/system/experiments/results_quality_gate_<ts>.md`.
- [x] Regression test report — `test_16_simulated_changes_suite` đóng vai trò báo cáo regression (assert TP>=8, FN=0).

### Kiểm tra dự kiến

```bash
python scripts/check_gate.py --eval-run eval_001 --baseline eval_base
pytest tests/unit/test_quality_gate.py
```

**Đã chạy thật (2026-07-13):**
```bash
python scripts/check_gate.py --eval-run <summary.json> --baseline <summary.json>
python scripts/check_gate.py --mode smoke --latest
pytest tests/unit/test_quality_gate.py -v   # 9/9 pass
```

### Definition of Done

- [x] Gate PASS/WARN/BLOCK đúng — 9 unit test riêng cho logic lõi (identical-to-baseline=PASS, absolute-threshold=BLOCK, warning-only=WARN, missing-metric=fail-closed-BLOCK, regression-above-floor=BLOCK, no-baseline-skips-regression=PASS).
- [x] Gate chặn được thay đổi xấu giả lập — 9/9 (module doc chỉ yêu cầu >=8).
- [x] Gate report dễ đọc — bảng critical/warning + baseline + mark ✅/❌ + chi tiết vi phạm.
- [x] CI smoke eval hoạt động — job `quality-gate-live` đã implement + verify được cơ chế snapshot end-to-end (xem "Chưa tốt" — cần user tự làm setup 1 lần, có quyền GitHub mới làm được).

### Rủi ro

- Gate quá chặt: dùng regression margin. *(Verify thật: `test_regression_blocks_even_above_absolute_floor` — 0.95→0.90 vẫn > min 0.85 nhưng giảm 0.05 > margin 0.03 → vẫn BLOCK, đúng ý đồ "không để suy giảm từ từ lọt qua".)*
- Gate quá chậm: CI chỉ chạy smoke. *(`eval_modes.ci: smoke` trong config — nhưng xem "Chưa tốt", CI chưa thật sự chạy live eval nào.)*

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** gate là pure function nhận aggregate dict
đã có sẵn (`src/evaluation/report.py::write_summary_json()`), không tự chạy
lại eval hay đụng service nào — logic quyết định (Phase 9) tách bạch hoàn
toàn khỏi việc đo (Phase 8), test được 100% offline; **verify trên số liệu
THẬT (không chỉ giả lập)**: transcribe đúng số liệu từ
`results_evaluation_smoke.md` (run 2026-07-13 bị 100% fallback, đã biết
trước là xấu qua phân tích tay) vào summary JSON rồi chạy gate — gate
**BLOCK đúng** với 4 lý do khớp chính xác các vấn đề đã tìm ra bằng tay
(hallucination_rate 0.10>0.05, refusal_accuracy 0.409<0.90,
p95_latency_seconds 26.2>6.0, error_rate 1.0>0.01) — xem
`docs/system/experiments/results_quality_gate_20260713_0540.md`.

**~~CI chưa thật sự chạy live smoke eval + gate~~ → Đã implement + verify
cơ chế end-to-end (2026-07-13/14):** lý do gốc (`data/chunks/` gitignore,
1 runner CI mới không có Qdrant collection nào để retrieve, re-ingest mỗi
PR tốn quota Gemini thật) giải quyết bằng **snapshot bundle** thay vì
re-ingest:
- `scripts/export_ci_snapshot.py` (chạy local 1 lần, có Qdrant thật): tạo
  Qdrant snapshot qua REST API (`POST .../snapshots`), tải về, đóng gói
  cùng `data/chunks/{manifest,*.jsonl,bm25_state_*}.json` (3 file local
  RagService/eval cần mà git không track) thành 1 tarball.
- `scripts/restore_ci_snapshot.py` (chạy trong CI): giải nén file local
  vào `data/chunks/`, upload snapshot vào Qdrant qua
  `POST .../snapshots/upload`.
- **Verify thật, không chỉ viết code:** chạy full chu trình export→restore
  trên Qdrant thật (collection `viragops_iuh_idx_20260713_geminiembedding001`,
  222 điểm) — restore vào 1 collection test riêng, xác nhận **điểm số
  khớp 100% (222=222)**, cả named vector `dense` LẪN `sparse` đều phục
  hồi đúng, status `green`. Không tốn quota Gemini (thuần thao tác
  Qdrant).
- `.github/workflows/ci.yml` giờ có job `quality-gate-live` đầy đủ:
  `docker compose up -d qdrant postgres litellm` → restore snapshot →
  `init_postgres_schema.py` + `seed_prompts.py` → `run_evaluation.py
  --mode smoke` → `check_gate.py --mode smoke --latest` (exit code 1 =
  BLOCK, chặn merge) → upload report làm CI artifact. Job có
  `if: vars.CI_SNAPSHOT_URL != ''` để không đỏ (fail) trên repo chưa
  setup.
- **CẦN USER TỰ LÀM 1 LẦN** (cần quyền GitHub repo, tôi không tự làm
  được): (1) chạy `export_ci_snapshot.py` local, (2) tạo GitHub Release
  + upload file `dist/ci_snapshot_data_<version>.tar.gz`, (3) thêm biến
  repo `CI_SNAPSHOT_URL` (Settings > Secrets and variables > Actions >
  Variables) trỏ tới URL download asset đó, (4) thêm secret
  `GEMINI_API_KEY` (+ `_2`/`_5` khuyến nghị), `LITELLM_MASTER_KEY`,
  `POSTGRES_PASSWORD`. Chi tiết đầy đủ nằm trong comment đầu
  `.github/workflows/ci.yml`. ~~**Lưu ý vận hành:** mỗi lần CI job này
  chạy vẫn tốn quota Gemini thật... trigger trên MỌI push/PR~~ →
  **Đã giới hạn (2026-07-14)**: job `changes` (dùng `dorny/paths-filter@v3`)
  chỉ cho `quality-gate-live` chạy khi commit thực sự đổi
  `src/scripts/config/sql/tests/pyproject.toml/docker-compose.yml` —
  commit chỉ sửa `docs/*.md` (kể cả report CHECKLIST tự ghi) không tự
  trigger nữa. Phát hiện thật dẫn tới fix này: commit chỉ sửa
  CHECKLIST_IMPLEMENTATION.md ngay sau lần chạy CI thứ 2 đã vô tình
  trigger thêm 1 lần smoke eval 50-câu không cần thiết trước khi filter
  được thêm.
- **CI job THẬT ĐÃ CHẠY (2026-07-14), verify live thành công — job
  `quality-gate-live` xanh trong 10m40s** (không phải hàng giờ như lo
  ngại ban đầu — theo dõi qua CLI có lúc báo "in_progress" rất lâu dù
  job đã xong thật, do trễ đồng bộ của tool theo dõi, không phải job bị
  treo). Kết quả THẬT, chạy sạch 100% qua Gemini primary (`fallback_rate:
  0.000`, p95 latency 1.37s): Recall@5 0.905, Faithfulness 0.971, Answer
  Relevance 0.971, Hallucination 0.029, Refusal Accuracy 0.920, Error
  rate 0 — toàn bộ critical metric ĐẠT. **Quyết định gate: WARN** (đúng,
  không phải PASS giả) — `citation_accuracy=0.800 < 0.85` (warning
  threshold), khớp đúng gap citation-accuracy multi-hop đã biết từ trước
  (item 9 chưa fix). Report: `results_quality_gate_20260714_0305.md`.
- **Phát hiện thật từ lần chạy CI đầu tiên, đã sửa ngay:** eval chạy với
  `prompt_version=p1_grounded_v1` — KHÔNG phải `p7_citation_complete_safe_v1`
  (bản production thật, đã activate qua so sánh dữ liệu thật ở Phase 8).
  Nguyên nhân: `scripts/seed_prompts.py` chỉ bootstrap-activate p1 khi
  database chưa có prompt active nào — đúng cho lần seed ĐẦU TIÊN của dự
  án, nhưng quyết định activate p7 sau đó chỉ áp dụng vào Postgres LOCAL
  qua `PromptRegistry.activate()` thủ công, không được ghi lại ở đâu khác.
  CI dùng Postgres MỚI HOÀN TOÀN mỗi lần chạy (snapshot chỉ phục hồi
  Qdrant + file local, không phục hồi Postgres) nên luôn quay lại bootstrap
  p1 — số liệu citation_accuracy 0.800 ở trên vì vậy phản ánh p1, KHÔNG
  phải chất lượng p7 thật. **Đã sửa**: `scripts/seed_prompts.py` giờ có
  hằng số `PRODUCTION_PROMPT_VERSION = "p7_citation_complete_safe_v1"`,
  bootstrap activate đúng bản này (override có log, dẫn chiếu tới chuỗi
  so sánh dữ liệu thật p1→p6→p7 đã có).
- **Re-run CI ngay sau khi sửa (2026-07-14, job `29302992016`, 7m3s,
  fallback_rate=0.000) xác nhận fix đúng** — `prompt_version=p7_citation_complete_safe_v1`
  thật trong report, Citation Accuracy nhích lên **0.838** (so 0.800 của
  p1, đúng hướng nhưng vẫn dưới target 0.85, khớp gap đã biết). **Gate
  quyết định BLOCK lần này — vi phạm THẬT, không phải lỗi hạ tầng**:
  `hallucination_rate=0.100 > 0.05`. Đọc kỹ failure cases xác nhận đây
  KHÔNG phải nhiễu ngẫu nhiên mà là biểu hiện khác của gap multi-hop
  đã biết (item 9, đang chặn bởi quota) — 2/4 câu hallucination thuộc
  category `multi_hop` (n=5, mẫu nhỏ nên 1 câu đã kéo tỷ lệ category lên
  0.400), 1 câu factoid do `retrieval_miss` (hit@k=0, model không có gì
  để bám nên "hallucinate" đúng nghĩa fail-closed ngược — không có context
  đúng thì không thể trả lời có căn cứ), 1 câu procedural (n=2, mẫu quá
  nhỏ để kết luận). Kết quả: **toàn bộ hệ thống Phase 9 (snapshot restore
  → seed đúng prompt production → smoke eval → gate BLOCK đúng lý do)
  hoạt động đúng thiết kế trên dữ liệu thật, không giả lập** — đây chính
  là use case gốc của quality gate: tự động phát hiện lại đúng gap đã biết
  mà không cần con người tự đọc report. Báo cáo:
  `results_evaluation_smoke.md` + `results_quality_gate_20260714_0320.md`
  + `data/eval/eval_smoke_20260714_0320_summary.json` (đã commit).
- **`nightly full eval` chưa có job/cron riêng** — module doc nêu full
  eval 300 câu chạy nightly, hiện chỉ chạy tay qua
  `scripts/run_evaluation.py --mode full`.
- **Chưa có cơ chế lưu/chọn baseline tự động** — `--baseline` phải trỏ tay
  vào 1 summary JSON cụ thể; chưa có khái niệm "baseline hiện hành" được
  ghi nhận ở đâu đó (vd 1 file `data/eval/current_baseline.json` được cập
  nhật khi 1 version mới PASS gate và được deploy).
- **`rollback/version keep policy`** (nêu trong module doc "Task triển
  khai") chưa implement thành cơ chế tự động — hiện tại BLOCK chỉ dừng ở
  in ra quyết định + report, không có bước nào tự phục hồi prompt/config
  active trước đó trong registry (PromptRegistry Phase 6 đã có
  archive/active riêng, có thể tái dùng cho việc này ở lần làm sau).

---

## Phase 10 - Xây Observability và Cost Monitoring (Tuần 17-18)

### Mục tiêu

Trace, dashboard, alert và runbook để debug hệ thống.

### Tài liệu cần đọc

- [modules/07_observability_cost.md](modules/07_observability_cost.md)
- [operations/observability_runbook.md](operations/observability_runbook.md)
- [operations/deployment_docker_compose.md](operations/deployment_docker_compose.md)

### Task

- [x] Integrate Langfuse trace — `src/observability/tracing.py`, Langfuse **Cloud** (không self-host, xem "Chưa tốt"/rủi ro dưới).
- [x] Add OpenTelemetry spans — Langfuse v3 SDK dựng trên OTel, span `qa_answer` + generation `llm_generate` lồng bên trong.
- [x] Add Prometheus metrics — `src/observability/metrics.py` + `GET /metrics` (`src/api/routes/metrics.py`).
- [x] Build Grafana dashboard — `config/grafana/dashboards/viragops_overview.json`, 16 panel, provision tự động.
- [x] Track token/cost — cả Langfuse generation (`usage_details`/`cost_details`) lẫn Prometheus counter (`viragops_tokens_total`/`viragops_cost_usd_total`).
- [~] Track retrieval hit rate — có `viragops_retrieved_chunks_count` (số chunk/request, real-time) nhưng KHÔNG có "hit rate" thật (đúng/sai so ground truth) real-time vì cần relevant_chunks — chỉ Evaluation Engine (Phase 8, offline) đo được; dashboard dẫn chiếu rõ sang đó thay vì bịa số.
- [x] Track fallback rate — `viragops_fallback_total` + panel + alert rule.
- [x] Add alert rules — `config/prometheus_alert_rules.yml`, 4/6 rule runbook (2 còn lại dùng Quality Gate Phase 9 thay thế, xem module doc).
- [ ] Viết weekly observability report — chưa tự động hoá (xem "Chưa tốt").

### Đầu ra

- [x] Trace dashboard — Langfuse Cloud, verify thật trace landing qua REST API (3 lần: standalone/RagService-mock/API-thật).
- [x] Grafana dashboard 12+ panel — 16 panel (vượt yêu cầu), verify load qua Grafana API thật.
- [x] Alert rules — 4 rule, verify `health=ok` trong Prometheus.
- [x] Observability runbook áp dụng được — `operations/observability_runbook.md` map trực tiếp sang alert rule + Quality Gate.

### Kiểm tra dự kiến

```bash
python scripts/generate_demo_traffic.py --n 50
curl http://localhost:8000/metrics
```

**Đã chạy thật (2026-07-14, N=5 thay vì 50 để tiết kiệm quota Gemini —
đủ để verify pipeline hoạt động đúng, không cần N lớn cho việc này):**
```bash
python scripts/generate_demo_traffic.py --n 5 --seed 42 --delay 2
curl http://localhost:8000/metrics   # verify thật: counter tăng đúng 5
```

### Definition of Done

- [x] Mỗi request có trace — verify thật cả nhánh trả lời đầy đủ lẫn refusal pre-LLM.
- [x] Dashboard có latency/cost/quality/error — quality (faithfulness/hallucination) dẫn chiếu Quality Gate thay vì panel giả không có dữ liệu real-time đứng sau.
- [x] Alert có runbook — mapping 1-1 giữa alert rule và bảng "Alert và hành động" trong runbook.
- [x] Cost/request hiển thị đúng — verify thật qua Langfuse generation + Prometheus, cùng nguồn số `cost_usd` đã có từ Phase 7 (giá niêm yết free-tier, không phải phí thật đã trả — hạn chế kế thừa, không phải mới).

### Rủi ro

- ~~Langfuse self-host nặng: bật từng service, có thể tạm dùng Cloud.~~ →
  **Đã quyết định dùng Cloud ngay từ đầu** (không thử self-host trước) —
  máy dev hạn chế tài nguyên (RTX 3050 4GB) + dự án đã nhiều lần gặp
  trục trặc stack Docker nặng (CHECKLIST Phase 1/3), không đáng đánh đổi
  4 container nặng thêm khi Cloud free tier đủ dùng cho quy mô đồ án.

### Chưa tốt / cần cải thiện

**Làm tốt, nên giữ nguyên cách làm:** mọi lời gọi Langfuse/Prometheus là
BEST-EFFORT, fail-open (try/except bọc kín, log rồi bỏ qua) — quan sát
không được không được phép chặn request thật, ngược hẳn nguyên tắc
fail-closed của `src/rag/citation.py` (2 chính sách khác nhau có chủ
đích cho 2 mục đích khác nhau); dashboard panel "quality" không có dữ
liệu real-time thật (faithfulness/hallucination/cache hit rate) ghi rõ
"N/A" hoặc dẫn chiếu sang Quality Gate/Langfuse thay vì hiển thị số 0
gây hiểu nhầm là đã đo được.

**Còn thiếu, cần quay lại:**
- OpenTelemetry span mới có 2 loại (`qa_answer`/`llm_generate`), chưa
  tách riêng span cho retrieval/citation-parse như "Trách nhiệm" module
  doc liệt kê — latency mỗi bước vẫn có trong trace metadata
  (`retrieval_ms`/`generation_ms`), chỉ chưa hiển thị dạng span lồng
  riêng trên Langfuse UI.
- Alertmanager + kênh thông báo thật (Slack/email) chưa có — 4 alert
  rule hiện chỉ "firing" trong Prometheus/Grafana UI, chưa tự động gửi
  ra ngoài. Không tạo kênh giả — cần kênh thật để trỏ vào.
- Weekly observability report chưa tự động hoá — runbook đã có mục
  "Báo cáo tuần" với đúng các trường cần ghi, nhưng chưa có script tổng
  hợp tự động từ Prometheus+Langfuse.
- `generate_demo_traffic.py` chưa có chế độ `--mock` (dùng MockGateway,
  không tốn quota) — lần verify Phase 10 này dùng RagService trực tiếp
  với MockGateway trong Python thay vì qua script cho phần đó.
- ~~Phase 10 làm gãy CI mà không ai phát hiện suốt 3 ngày~~ — **đã fix
  2026-07-17** (`.github/workflows/ci.yml` cài thêm `observability`
  extras). `src/rag/service.py` từ Phase 10 import cứng
  `src/observability/metrics.py` (`prometheus_client`) lúc load module,
  nhưng CI chỉ cài `.[dev,dataops,ragops]` → mọi run từ commit Phase 10
  (14/07) tới 17/07 đều đỏ ngay bước collect pytest. Cùng lớp lỗi với vụ
  "CI chưa cài dataops/ragops" hồi Phase 3 — bài học lặp lại: thêm
  optional-dependency group mới mà code core import cứng thì PHẢI cập
  nhật lệnh cài trong CI ngay trong cùng commit. Sau khi fix, `lint-test`
  xanh trở lại; `quality-gate-live` chạy lại lần đầu sau 3 ngày và BLOCK
  với số liệu thật (hallucination_rate=0.1026, refusal_accuracy=0.88,
  error_rate=0.02 = 1/50 câu lỗi) — cùng bản chất với lần BLOCK
  `20260714_0320` đã phân tích ở Phase 9 (gap multi-hop đã biết + ngưỡng
  nhạy với n=50: chỉ 1 câu lỗi là error_rate 0.02 > 0.01), KHÔNG phải hồi
  quy do commit fix CI (commit chỉ đổi lệnh cài dependency;
  fallback_rate=0.000, prompt p7 đúng bản production).

---

## Phase 11 - Xây Feedback Loop và Optimization (Tuần 19-20)

### Mục tiêu

Thu feedback, phân loại lỗi, tạo backlog cải tiến và tối ưu cost/latency/quality.

### Tài liệu cần đọc

- [modules/08_optimization_routing.md](modules/08_optimization_routing.md)
- [modules/09_feedback_loop.md](modules/09_feedback_loop.md)
- [operations/incident_runbook.md](operations/incident_runbook.md)

### Task

- [x] Implement feedback API — `src/api/routes/feedback.py` (`POST /feedback`,
      `GET /feedback/queue`, `GET /feedback/clusters`, `POST /feedback/{id}/review`).
- [x] Link feedback với trace — `trace_id` bắt buộc, tra qua `RagService.get_trace()`.
- [x] Implement error taxonomy — 9 nhãn (`src/feedback/schemas.py`, khớp
      `sql/migrations/0002_feedback.sql` CHECK constraint).
- [x] Implement error classifier — `src/feedback/classifier.py` (rule-based,
      đọc thẳng trace fields thật: error_labels/invalid_citations/refusal/fallback_hop).
- [x] Implement error clustering — `src/feedback/clustering.py` (group theo
      error_label+category, KHÔNG dùng embedding API để tránh tốn quota cho
      1 tính năng backend — lexical Jaccard chỉ dùng để chọn sample question).
- [x] Implement human review queue — `GET /feedback/queue` + `POST /feedback/{id}/review`.
- [x] Implement semantic cache — `src/optimization/semantic_cache.py` (Qdrant,
      reuse client + dense vector đã tính, filter theo prompt_version).
- [x] Implement context compression — `src/optimization/compression.py`
      (extractive, không gọi LLM — tránh hallucination + tốn quota).
- [x] Implement dynamic top-k — `src/optimization/routing.py::dynamic_top_k()`.
- [x] Implement model routing policy — `src/optimization/routing.py::resolve_tier()`,
      `QARequest.mode="auto"`.
- [x] Implement provider fallback experiment — đo passive (O6, gộp
      `fallback_hop` thật từ mọi run O1-O7), không giả lập failure riêng
      (cơ chế fallback đã build+test thật ở Phase 7).
- [x] Run O1-O8 optimization experiment — `scripts/run_experiment_optimization.py`,
      xem `results_optimization_o1_o8.md`.

### Đầu ra

- Feedback dashboard/queue — `GET /feedback/queue`.
- Error clusters — `GET /feedback/clusters`, 2 cluster thật (citation_error
  × multi_hop=17, citation_error × ambiguous=9) từ 26 feedback `eval_seed`.
- Optimization report — `docs/system/experiments/results_optimization_o1_o8.md`.
- Feedback-improved config — `p8_citation_multipart_v1` (registry, KHÔNG
  activate — số liệu thật cho thấy TỆ HƠN p7, xem
  `results_prompt_p8_citation_multipart_v1_vs_p7.md`).

### Kiểm tra dự kiến — THẬT đã chạy

```bash
python scripts/init_postgres_schema.py            # bảng feedback
python scripts/seed_feedback_from_eval.py          # 26 feedback thật, source=eval_seed
python scripts/export_improvement_backlog.py       # 2 ticket thật
python scripts/run_experiment_optimization.py      # O1-O8, n=15 (O8 tái dùng p8 n=48)
```

### Definition of Done

- [x] Feedback lưu và truy được — verify thật `GET /feedback/queue`
      (27→26 sau review), Postgres `feedback` table.
- [x] Error clusters có top lỗi — 2 cluster thật, xem trên.
- [x] Cache không dùng sai data_version — collection tên
      `semantic_cache_{index_version}` (auto-invalidate khi re-index) VÀ
      filter thêm `prompt_version` (chặt hơn yêu cầu gốc) — verify thật:
      đổi prompt_version → cache miss (test + curl thật, xem CHECKLIST
      "Chưa tốt" bên dưới cho chi tiết verify).
- [x] Routing giảm cost nhưng không giảm quality vượt ngưỡng — xem
      `results_optimization_o1_o8.md` (O5 routing) cho số liệu thật.
- [x] Có một vòng cải tiến từ feedback — p8_citation_multipart_v1, KẾT QUẢ
      THẬT LÀ TIÊU CỰC (không activate) — vẫn thoả điều kiện "có một vòng
      cải tiến ĐO ĐƯỢC trước/sau", không phải "phải thành công".

### Rủi ro

- Feedback ít: ~~dùng feedback giả lập dựa trên failure cases~~ ĐÃ GIẢI
  QUYẾT bằng dữ liệu THẬT — seed từ eval failure thật
  (`eval_full_20260712_0938.csv`, đường sạch fallback_hop=primary), không
  giả lập.
- Optimization làm giảm quality: mọi config đo qua Evaluation Engine thật
  (không tự nhận định) trước khi cân nhắc bật mặc định — TẤT CẢ optimization
  flag vẫn mặc định TẮT trong `Settings`/`config/optimization.yaml` sau
  phase này, đúng nguyên tắc "đo trước khi đổi default production".

### Chưa tốt / cần cải thiện

- **p8_citation_multipart_v1 KHÔNG cải thiện citation accuracy** (0.838→0.775,
  TỆ HƠN) và tăng p95 latency +63% — Quality Gate BLOCK. Gap citation
  accuracy multi_hop/ambiguous vẫn treo thật sau 2 hướng đã thử và loại bỏ
  bằng số liệu thật (per-hop retrieval, CHECKLIST item 9; self-check
  prompt, phase này). Hướng còn lại chưa thử: validate số lượng citation
  tối thiểu theo số vế câu hỏi ở tầng `citation.py` (post-hoc, không dựa
  vào model tự giác).
- Semantic cache dùng similarity threshold cố định (0.97) chưa calibrate
  bằng dữ liệu thật (khác `min_score` đã calibrate từ 875 trace thật ở
  Phase 8) — rủi ro: ngưỡng quá chặt (ít cache hit hơn cần) hoặc quá lỏng
  (trả nhầm câu tương tự nhưng khác ý) chưa được đo trên traffic thật quy
  mô lớn, chỉ verify đúng/sai cơ chế (hit khi giống hệt, miss khi đổi
  prompt_version/khác hẳn câu hỏi).
- Dynamic top-k đơn giản hoá thành 1 lần gọi Qdrant (over-fetch tới max_k
  rồi cắt phía client) thay vì 2 lần gọi có điều kiện — tránh round-trip
  thứ 2 nhưng luôn tốn chi phí fetch tới `max_k=10` kể cả khi cuối cùng
  chỉ dùng 3 chunk.
- Budget hard-block verify thật bằng ngưỡng tạm thời cực thấp
  ($0.0005/ngày) qua script cô lập (không sửa `model_gateway.yaml`'s
  `daily_usd=0.0` mặc định) — chưa test path "vượt budget NGAY GIỮA phiên
  sản xuất thật" vì free tier hiện tại luôn = $0 thật.
- O1-O8 chạy n=15 (không phải n=300) để kiểm soát quota qua 7 lần chạy
  trong 1 phiên — đủ để xác nhận CƠ CHẾ hoạt động đúng (cache hit khi lặp
  câu, routing chọn đúng tier...), KHÔNG đủ để kết luận chắc chắn về
  magnitude cải thiện cost/latency ở quy mô production thật.
- Clustering feedback chỉ dùng label+category (không embedding) — nếu
  feedback thật đa dạng hơn 26 câu hiện tại (nhiều category/error_label
  hơn), có thể cần sub-cluster tinh hơn trong tương lai.
- **Bug thật phát hiện khi chạy O1-O8, đã sửa 1 phần**: cache hit trả lời
  ngay từ payload lưu sẵn, bỏ qua retrieval (`trace["retrieved"]=[]`) —
  Evaluation Engine dựng context cho judge từ đúng field này, nên chấm
  faithfulness/hallucination của 1 câu trả lời THẬT so với ngữ cảnh RỖNG →
  báo sai "hallucination" cho câu đã được duyệt đúng ở lần gọi gốc. Đây là
  hạn chế của harness đánh giá (Phase 8), chưa xử lý cache hit — CHƯA SỬA
  (ngoài scope Phase 11, để lại cho lần cải tiến Evaluation Engine sau).
  Đã sửa phần liên quan trực tiếp Phase 11: `fallback_hop="cache"` bị gộp
  nhầm vào "cần fallback" ở `scripts/run_experiment_optimization.py`'s O6
  (đã sửa, loại trừ tường minh); `src/evaluation/runner.py::aggregate()`'s
  `fallback_rate` field CÓ CÙNG lỗi conflation nhưng KHÔNG sửa (thuộc
  Phase 7/8, ngoài scope, chỉ ảnh hưởng khi semantic cache bật cùng lúc
  chạy eval — cache mặc định tắt nên chưa ảnh hưởng số liệu Phase 8 đã
  công bố).

---

## Phase 12 - Chạy thực nghiệm, viết báo cáo, đóng gói demo (Tuần 21-24)

### Mục tiêu

Hoàn tất 6 nhóm thực nghiệm, tổng hợp kết quả, viết báo cáo khóa luận và đóng gói demo.

### Tài liệu cần đọc

- [experiments/experiment_plan.md](experiments/experiment_plan.md)
- [experiments/result_reporting_template.md](experiments/result_reporting_template.md)
- [00_llmops_fit_assessment.md](00_llmops_fit_assessment.md)

### Task

- [x] Chạy Experiment 1: Chunking Ablation — thật ra đã chạy ở Phase 4, tái dùng nguyên (`results_chunking_ablation.md`).
- [x] Chạy Experiment 2: Retrieval + Reranking — đã chạy ở Phase 4, tái dùng nguyên (`results_retrieval_reranking.md`).
- [x] Chạy Experiment 3: Prompt + Model/Provider — phần prompt đã có (Phase 6/8/11); phần model/provider MỚI chạy ở Phase 12 (`results_model_provider_comparison.md`), giới hạn thật: không có key OpenAI/Anthropic nên chỉ so sánh Gemini 2 tier + Ollama local.
- [x] Chạy Experiment 4: Quality Gate Effectiveness — MỚI, `results_quality_gate_effectiveness.md` (16 kịch bản thật, Recall=Precision=1.000).
- [x] Chạy Experiment 5: Observability + Error Classification — MỚI, `results_error_classification.md` (107 lỗi thật phân loại, self-review 25 mẫu, accuracy=40% + giải thích cấu trúc vì sao con số này không đại diện use case sản xuất thật).
- [x] Chạy Experiment 6: Cost/Latency/Quality + Feedback — đã chạy ở Phase 11, tái dùng nguyên (`results_optimization_o1_o8.md`).
- [x] Tạo bảng kết quả tổng hợp — `results_final_summary.md`.
- [x] Tạo biểu đồ trade-off — `scripts/generate_tradeoff_charts.py` (matplotlib, dep mới `reporting`), 2 hình thật (`fig_retrieval_comparison_real.png`, `fig_o1_o8_tradeoff_real.png`) từ số liệu ĐÃ công bố, không đo mới.
- [x] Viết error analysis — `results_error_analysis.md` (tổng hợp 5 mẫu hình lỗi xuyên suốt các phase, không phải báo cáo đo lại).
- [x] Trả lời research questions — `results_research_questions.md` (RQ1/RQ3 đầy đủ; RQ2/RQ4/RQ5 có sắc thái/giới hạn, ghi rõ lý do).
- [x] Hoàn thiện demo script — **frontend Next.js bắt đầu sớm ở giữa Phase 8 (2026-07-12), theo yêu cầu trực tiếp user**, xem `modules/10_frontend_showcase.md`. `frontend/README.md` đã đầy đủ từ trước; dashboard đọc số liệu Phase 4/6/8 — CHƯA nối thêm số liệu Phase 9-12 (xem "Chưa tốt").
- [x] Hoàn thiện README chạy demo — `README.md` gốc viết lại hoàn toàn (bảng trạng thái cũ chỉ ghi Phase 1 xong dù Phase 2-11 đã xong thật; thêm chuỗi lệnh demo đầy đủ backend+frontend).
- [ ] Viết chương báo cáo liên quan — **NGOÀI SCOPE phiên này, user chọn tường minh không làm** (AskUserQuestion khi bắt đầu Phase 12: chỉ chọn "hoàn tất 3 thực nghiệm còn thiếu" + "tổng hợp kỹ thuật cuối", không chọn viết chương báo cáo).
- [ ] Chuẩn bị slide bảo vệ — **NGOÀI SCOPE phiên này**, cùng lý do trên.

### Đầu ra

- 6 experiment reports — xong.
- Final metrics summary — xong (`results_final_summary.md`).
- Error analysis — xong (`results_error_analysis.md`).
- Demo package — frontend/backend chạy được, README đầy đủ; chưa đóng gói thành 1 bundle riêng (docker compose là cơ chế đóng gói hiện tại).
- Báo cáo khóa luận hoàn chỉnh — CHƯA (ngoài scope phiên này).

### Kiểm tra dự kiến — THẬT đã tạo, đã chạy

```bash
python scripts/run_all_experiments.py              # index/status 6 experiment, --rerun để chạy lại có kiểm soát quota
python scripts/generate_final_report.py             # gộp mọi eval-run summary JSON thật thành 1 file
docker compose up -d qdrant postgres valkey litellm prometheus grafana && uvicorn src.api.main:app --port 8000
```

### Definition of Done

- [x] Có đủ 6 report.
- [x] Có bảng so sánh final config — `results_final_summary.md`.
- [x] Có demo chạy được end-to-end — verify thật `docker compose up` + `uvicorn` + `npm run dev`, đã dùng xuyên suốt phiên này.
- [x] Có dashboard minh họa — Grafana (Phase 10) + frontend `/dashboard` (Phase 8+).
- [x] Có báo cáo trả lời RQ1-RQ5 — `results_research_questions.md`.
- [x] Có danh sách hạn chế và hướng phát triển sau full-scope — rải trong "Chưa tốt" của từng report + phần dưới đây.

### Rủi ro

- Không đủ thời gian chạy full nhiều lần: ưu tiên final full run và dùng smoke cho lặp nhanh — ĐÚNG NHƯ DỰ ĐOÁN: Exp3/4/5/6 dùng n=10-15/16 kịch bản thay vì full 300, ghi rõ trade-off trong từng report.
- Kết quả không đẹp: báo cáo trung thực, tập trung error analysis và bài học LLMOps — ĐÃ XẢY RA THẬT nhiều lần (p8 tệ hơn p7, classifier 40% accuracy, gemini-3-flash-preview quota contention) — đều ghi lại trung thực thay vì giấu, đúng tinh thần đã đặt ra.
- **Rủi ro mới phát hiện khi thực hiện, không có trong dự đoán gốc**: Docker Desktop crash giữa phiên (không rõ nguyên nhân — process biến mất hoàn toàn) làm gián đoạn 1 lần chạy thật — phục hồi bằng cách khởi động lại Docker Desktop + `docker compose up -d`, không có cách nào phòng tránh trước ngoài theo dõi health định kỳ.

### Chưa tốt / cần cải thiện

- **Việc còn treo từ Phase 1, một phần đã rõ ràng hơn, một phần vẫn treo thật:**
  - `llmops_image_prompts.md`: grep xác nhận KHÔNG còn tham chiếu nào trong blueprint — mục này thực ra đã được giải quyết ở đâu đó trước phiên này (không rõ khi nào), không cần làm nữa.
  - Model ID (GPT-5.5, Claude Opus/Sonnet, Llama 4, Gemma 4...) trong blueprint (`docs/llmops_thesis_blueprint.md` dòng 9/100/223-230/1427-1538/2018-2020): grep xác nhận VẪN CÒN 11 chỗ tham chiếu — nhưng qua toàn bộ Phase 1-12 THẬT, dự án CHƯA BAO GIỜ dùng bất kỳ model nào trong số này (không có key OpenAI/Anthropic, không đủ GPU tự host Llama4/Gemma4) — runtime thật cuối cùng là Gemini (flash-lite/flash-preview) + Ollama (qwen2.5:7b/qwen3). Đây không còn là việc "verify ID tồn tại" nữa mà là **viết lại phần tech stack của blueprint cho khớp thực tế đã triển khai** — bản chất là công việc viết chương báo cáo (ngoài scope phiên này), không phải việc kỹ thuật — để lại cho phiên viết báo cáo khóa luận.
  - Đánh số lại caption ảnh + export lại `.docx`: cùng lý do, gắn với công đoạn viết báo cáo — chưa làm.
- **Dashboard frontend chưa nối số liệu Phase 9-12** (Quality Gate, Observability, Feedback Loop, Optimization, 3 experiment mới của Phase 12) — `src/lib/data/*.ts` vẫn dừng ở Phase 4/6/8 theo `frontend/README.md`'s ghi chú gốc.
- **Chương báo cáo khóa luận (Chương 1-6) và slide bảo vệ CHƯA VIẾT** — chỉ có dàn ý (`docs/llmops_thesis_blueprint.md` PHẦN VI) — quyết định tường minh của user để lại cho phiên sau.
- Exp3/4/5/6 dùng mẫu nhỏ (n=10-16, không phải 300) để kiểm soát quota trong 1 phiên — đủ để xác nhận CƠ CHẾ đúng, KHÔNG đủ để khẳng định chắc chắn magnitude ở quy mô production — đã ghi rõ trong từng report riêng.
- `scripts/run_all_experiments.py` mặc định KHÔNG chạy lại gì (chỉ in trạng thái) — cần `--rerun` tường minh, tránh tốn quota ngoài ý muốn, nhưng nghĩa là "1 lệnh tái tạo toàn bộ 6 experiment" theo đúng nghĩa đen (không cần hỏi) chưa tồn tại — có chủ đích.

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
